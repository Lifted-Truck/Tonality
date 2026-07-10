"""The pattern layer, slice 1 (gap C): melodic-motif object + matcher.

Oracle: hand-built lines where the occurrences are countable by eye. Covers the
abstraction lattice (pitch exact/degree/contour × time exact/free), the honesty
contract (degree needs a key — error don't guess; overlaps all reported; chordal
lines skipped loudly; rhythm-free matches surface their IOIs), total validation,
the named library, payload round-trip, determinism, and MCP parity.
"""

import pytest

from mts.mcp.tools import _canonical_sequence
from mts.patterns import (
    PatternValidationError,
    find_pattern,
    list_named_patterns,
    load_named_pattern,
    parse_pattern,
    pattern_to_payload,
    pattern_validation_errors,
)


def _seq(events):
    return _canonical_sequence(events)


def _pat(pitch, time, elements, iois=None, **extra):
    payload = {"schema_version": "pattern.1", "name": "t", "version": "1",
               "domain": "melody", "abstraction": {"pitch": pitch, "time": time},
               "elements": elements, **extra}
    if iois is not None:
        payload["iois"] = iois
    return payload


# A-G-F-E twice in C major: once plain, once an octave lower and time-stretched.
PRINNER_LINE = [[0, 1, 81, "v"], [1, 1, 79, "v"], [2, 1, 77, "v"], [3, 1, 76, "v"],
                [4, 2, 84, "v"],
                [6, .5, 69, "v"], [6.5, .5, 67, "v"], [7, 1, 65, "v"], [8, 2, 64, "v"]]


# --- the lattice ----------------------------------------------------------------

def test_degree_pattern_matches_across_octave_and_stretch():
    m = find_pattern(_seq(PRINNER_LINE), _pat("degree", "free", [6, 5, 4, 3]),
                     key=(0, "major"))
    assert m.count == 2
    assert m.occurrences[0].degrees == [6, 5, 4, 3]
    # the rhythm-free match surfaces its actual time-warp as evidence
    assert m.occurrences[1].iois == [0.5, 0.5, 1.0]


def test_exact_pattern_is_transposition_sensitive():
    riff = _pat("exact", "free", [60, 62, 64])
    events = [[0, 1, 60, "v"], [1, 1, 62, "v"], [2, 1, 64, "v"],
              [3, 1, 62, "v"], [4, 1, 64, "v"], [5, 1, 66, "v"]]  # +2 copy: no match
    m = find_pattern(_seq(events), riff)
    assert m.count == 1 and m.occurrences[0].midis == [60, 62, 64]


def test_contour_pattern_matches_shape_only():
    arch = load_named_pattern("arch-contour")  # up up down down
    events = [[0, 1, 60, "v"], [1, 1, 64, "v"], [2, 1, 67, "v"],
              [3, 1, 65, "v"], [4, 1, 62, "v"]]
    m = find_pattern(_seq(events), arch)
    assert m.count == 1 and m.occurrences[0].moves == ["up", "up", "down", "down"]
    assert m.occurrences[0].degrees is None  # contour makes no pitch claims


def test_time_exact_filters_by_iois():
    riff = _pat("exact", "exact", [60, 62, 64], iois=[0.5, 0.5])
    events = [[0, .5, 60, "v"], [0.5, .5, 62, "v"], [1, .5, 64, "v"],
              [2, .5, 60, "v"], [2.5, .5, 62, "v"], [3.5, .5, 64, "v"]]  # 2nd: IOI 1.0
    m = find_pattern(_seq(events), riff)
    assert m.count == 1 and m.occurrences[0].start_beat == 0.0


# --- honesty --------------------------------------------------------------------

def test_degree_without_key_raises():
    with pytest.raises(ValueError, match="never infers a key"):
        find_pattern(_seq(PRINNER_LINE), _pat("degree", "free", [6, 5, 4, 3]))


def test_modal_key_raises():
    with pytest.raises(ValueError, match="major/minor only"):
        find_pattern(_seq(PRINNER_LINE), _pat("degree", "free", [6, 5, 4, 3]),
                     key=(2, "dorian"))


def test_chromatic_note_cannot_match_a_degree():
    # F# in C major has no degree — the window containing it can't match.
    events = [[0, 1, 81, "v"], [1, 1, 79, "v"], [2, 1, 78, "v"], [3, 1, 76, "v"]]
    m = find_pattern(_seq(events), _pat("degree", "free", [6, 5, 4, 3]), key=(0, "major"))
    assert m.count == 0


def test_overlapping_occurrences_all_reported():
    rep = _pat("contour", "free", ["same"])
    m = find_pattern(_seq([[0, 1, 60, "v"], [1, 1, 60, "v"], [2, 1, 60, "v"]]), rep)
    assert m.count == 2  # both adjacent pairs


def test_chordal_line_skipped_loudly():
    arch = load_named_pattern("arch-contour")
    chordal = [[0, 1, 60, "p"], [0, 1, 64, "p"], [1, 1, 62, "p"]]
    m = find_pattern(_seq(chordal), arch)
    assert m.voices_skipped == ["p"] and m.count == 0


def test_unvoiced_line_works():
    m = find_pattern(_seq([[0, 1, 60], [1, 1, 64], [2, 1, 67], [3, 1, 65], [4, 1, 62]]),
                     load_named_pattern("arch-contour"))
    assert m.count == 1 and m.occurrences[0].voice is None


# --- validation + library -------------------------------------------------------

def test_validation_is_total():
    errors = pattern_validation_errors(
        {"domain": "nope", "abstraction": {"pitch": "x", "time": "exact"},
         "elements": [], "bogus": 1})
    # name, version, domain, pitch level, elements, iois-required, unknown key
    assert len(errors) >= 6
    with pytest.raises(PatternValidationError):
        parse_pattern({"domain": "nope"})


def test_iois_only_with_time_exact():
    errors = pattern_validation_errors(_pat("exact", "free", [60, 62], iois=[1.0]))
    assert any("iois" in e for e in errors)


def test_library_and_round_trip():
    assert list_named_patterns() == ["arch-contour", "prinner-descent"]
    for name in list_named_patterns():
        pattern = load_named_pattern(name)
        assert parse_pattern(pattern_to_payload(pattern)) == pattern
    with pytest.raises(ValueError, match="Unknown pattern"):
        load_named_pattern("nope")


def test_deterministic():
    a = find_pattern(_seq(PRINNER_LINE), load_named_pattern("prinner-descent"),
                     key=(0, "major")).to_dict()
    b = find_pattern(_seq(PRINNER_LINE), load_named_pattern("prinner-descent"),
                     key=(0, "major")).to_dict()
    assert a == b


# --- MCP parity -------------------------------------------------------------------

def test_mcp_find_pattern_matches_engine():
    from mts.mcp import tools
    from mts.patterns import load_named_pattern as _load

    engine = find_pattern(_seq(PRINNER_LINE), _load("prinner-descent"),
                          key=(0, "major")).to_dict()
    tool = tools.find_pattern(tools.load_named_pattern("prinner-descent"),
                              PRINNER_LINE, key=["C", "major"])
    assert tool == engine


def test_mcp_library_tools():
    from mts.mcp import tools

    assert tools.list_named_patterns() == ["arch-contour", "prinner-descent"]
    payload = tools.load_named_pattern("arch-contour")
    assert payload["abstraction"] == {"pitch": "contour", "time": "free"}
