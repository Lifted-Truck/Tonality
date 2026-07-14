"""gap E slice 4 — cross-part patterns (the two-voice Prinner and kin).

A CrossPartPattern is a schema spanning >= 2 voices moving together
(homorhythmic); the matcher pairs co-onset single-pitch voices BY REGISTER
(high->low), matches exactly under the declared pitch abstraction, needs a key
for degree matching (error, don't guess), enforces strict homorhythm, and skips
chordal voices loudly. These tests pin all of that plus the shipped Prinner.
"""

from __future__ import annotations

import pytest

from mts.patterns import (
    parse_cross_part_pattern,
    find_cross_part_pattern,
    cross_part_validation_errors,
    cross_part_pattern_to_payload,
    load_named_cross_part_pattern,
    list_named_cross_part_patterns,
)
from mts.mcp.tools import _canonical_sequence

PRINNER = {
    "schema_version": "cross_part.1", "name": "prinner", "version": "1",
    "domain": "schema", "abstraction": {"pitch": "degree", "alignment": "homorhythmic"},
    "lines": [[6, 5, 4, 3], [4, 3, 2, 1]],
}


def _prinner_events(shift=0, upper="S", lower="B"):
    # C-major two-voice Prinner: upper A-G-F-E over F-E-D-C, homorhythmic on 0..3.
    rows = []
    for b, (hi, lo) in enumerate([(69, 65), (67, 64), (65, 62), (64, 60)]):
        rows += [[b, 1, hi + shift, upper], [b, 1, lo + shift, lower]]
    return _canonical_sequence(rows)


def test_two_voice_prinner_matches_with_register_lines():
    r = find_cross_part_pattern(_prinner_events(), parse_cross_part_pattern(PRINNER), key=(0, "major"))
    assert r.count == 1
    occ = r.occurrences[0]
    assert sorted(occ.voices) == ["B", "S"]
    assert occ.lines[0].degrees == [6, 5, 4, 3]   # register line 0 = upper
    assert occ.lines[1].degrees == [4, 3, 2, 1]   # register line 1 = lower
    assert occ.lines[0].midis == [69, 67, 65, 64]


def test_degree_schema_is_transposition_invariant():
    a = find_cross_part_pattern(_prinner_events(0), PRINNER, key=(0, "major")).count
    b = find_cross_part_pattern(_prinner_events(7), PRINNER, key=(7, "major")).count
    assert a == b == 1


def test_wrong_key_reading_does_not_match():
    assert find_cross_part_pattern(_prinner_events(), PRINNER, key=(2, "major")).count == 0


def test_lines_are_matched_by_register_not_label():
    # Swap the labels so the *upper* voice is called "B" — register still decides.
    r = find_cross_part_pattern(_prinner_events(upper="B", lower="S"), PRINNER, key=(0, "major"))
    assert r.count == 1
    assert r.occurrences[0].lines[0].degrees == [6, 5, 4, 3]  # highest-sounding is line 0


def test_degree_needs_a_key():
    with pytest.raises(ValueError, match="needs key"):
        find_cross_part_pattern(_prinner_events(), PRINNER)


def test_strict_homorhythm_rejects_an_interloping_onset():
    # Insert an extra note in the upper voice between beats 1 and 2 → the window
    # is no longer homorhythmic (a voice onsets alone), so no match.
    rows = []
    for b, (hi, lo) in enumerate([(69, 65), (67, 64), (65, 62), (64, 60)]):
        rows += [[b, 1, hi, "S"], [b, 1, lo, "B"]]
    rows.append([1.5, 0.4, 66, "S"])  # interloper — S moves alone
    r = find_cross_part_pattern(_canonical_sequence(rows), PRINNER, key=(0, "major"))
    assert r.count == 0


def test_pick_two_of_three_voices():
    # A third (inner) voice that does not participate; the Prinner still matches
    # on the outer pair (combinations over voices).
    rows = []
    for b, (hi, mid, lo) in enumerate([(69, 67, 65), (67, 65, 64), (65, 64, 62), (64, 62, 60)]):
        rows += [[b, 1, hi, "S"], [b, 1, mid, "A"], [b, 1, lo, "B"]]
    r = find_cross_part_pattern(_canonical_sequence(rows), PRINNER, key=(0, "major"))
    # S/B realize 6-5-4-3 over 4-3-2-1; other pairings don't → at least the S/B match
    assert r.count >= 1
    assert any(sorted(o.voices) == ["B", "S"] for o in r.occurrences)


def test_chordal_voice_is_skipped_and_named():
    # A voice with simultaneous onsets can't be linearized → skipped loudly.
    rows = []
    for b, (hi, lo) in enumerate([(69, 65), (67, 64), (65, 62), (64, 60)]):
        rows += [[b, 1, hi, "S"], [b, 1, lo, "B"]]
    rows += [[0, 1, 48, "pad"], [0, 1, 52, "pad"]]  # co-onset in 'pad' → chordal
    r = find_cross_part_pattern(_canonical_sequence(rows), PRINNER, key=(0, "major"))
    assert "pad" in r.voices_skipped
    assert r.count == 1  # S/B still match


def test_contour_schema():
    # A two-voice parallel-descent contour (both down), alignment homorhythmic.
    pat = {"schema_version": "cross_part.1", "name": "parallel-descent", "version": "1",
           "domain": "schema", "abstraction": {"pitch": "contour", "alignment": "homorhythmic"},
           "lines": [["down", "down", "down"], ["down", "down", "down"]]}
    r = find_cross_part_pattern(_prinner_events(), pat)  # contour needs no key
    assert r.count == 1
    assert r.occurrences[0].lines[0].moves == ["down", "down", "down"]


def test_validation_total_and_strict():
    assert cross_part_validation_errors(PRINNER) == []
    bad = {"name": "x", "version": "1", "domain": "melody",  # wrong domain
           "abstraction": {"pitch": "degree", "alignment": "swung"},  # bad alignment
           "lines": [[6, 5, 4, 3]]}  # only one line
    errs = cross_part_validation_errors(bad)
    assert any("domain" in e for e in errs)
    assert any("alignment" in e for e in errs)
    assert any("lines" in e for e in errs)


def test_unequal_line_lengths_rejected():
    bad = {**PRINNER, "lines": [[6, 5, 4, 3], [4, 3, 2]]}  # 4 vs 3 onsets
    assert any("same number of onsets" in e for e in cross_part_validation_errors(bad))


def test_shipped_prinner_loads_and_matches():
    assert "prinner-two-voice" in list_named_cross_part_patterns()
    p = load_named_cross_part_pattern("prinner-two-voice")
    assert p.n_lines == 2 and p.n_onsets == 4
    assert find_cross_part_pattern(_prinner_events(), p, key=(0, "major")).count == 1


def test_payload_round_trips():
    p = parse_cross_part_pattern(PRINNER)
    assert parse_cross_part_pattern(cross_part_pattern_to_payload(p)) == p


def test_mcp_parity():
    from mts.mcp import tools

    events = [[b, 1, m, v] for b, (u, l) in enumerate([(69, 65), (67, 64), (65, 62), (64, 60)])
              for m, v in ((u, "S"), (l, "B"))]
    out = tools.find_cross_part_pattern(pattern=PRINNER, events=events, key=[0, "major"])
    assert out["count"] == 1 and out["pitch_level"] == "degree"
