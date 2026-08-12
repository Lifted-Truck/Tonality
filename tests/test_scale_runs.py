"""gap 31(b) — find_scale_runs: maximal stepwise walks through a scale.

Pins the definitions that make a walk a walk: register-adjacency (an octave
leap to the neighbouring pc is a leap), maximality, constant direction with the
turning note shared, strict diatony (chromatics break runs), and the min-notes
gate that keeps ordinary stepwise motion from triggering everywhere.
"""

from __future__ import annotations

import pytest

from mts.mcp.tools import _canonical_sequence
from mts.temporal import find_scale_runs

MAJOR = "Ionian"


def _line(midis, voice="m"):
    return _canonical_sequence([[i, 1, m, 90, voice] for i, m in enumerate(midis)])


def test_the_motivating_case_descent_then_partway_back_up():
    """Julian's topline: a walk down the scale, then partway back up."""
    r = find_scale_runs(_line([67, 65, 64, 62, 60, 62, 64]), MAJOR, 0)
    assert len(r.runs) == 1                       # the ascent is under the gate
    run = r.runs[0]
    assert run.direction == "descent" and run.note_count == 5
    assert run.midis == [67, 65, 64, 62, 60]
    assert run.degrees == [5, 4, 3, 2, 1]
    # lower the gate and the return trip appears, sharing the turning note
    r3 = find_scale_runs(_line([67, 65, 64, 62, 60, 62, 64]), MAJOR, 0, min_notes=3)
    assert [(x.direction, x.note_count) for x in r3.runs] == [("descent", 5), ("ascent", 3)]
    assert r3.runs[0].end_index == r3.runs[1].start_index      # shared turnaround


def test_runs_are_maximal_never_nested():
    r = find_scale_runs(_line([72, 71, 69, 67, 65, 64, 62, 60]), MAJOR, 0)
    assert len(r.runs) == 1 and r.runs[0].note_count == 8


def test_a_chromatic_note_breaks_the_run():
    # G F E (D#) D C — the D# is not a scale tone, so no 6-note run exists
    r = find_scale_runs(_line([67, 65, 64, 63, 62, 60]), MAJOR, 0, min_notes=3)
    assert [(x.midis) for x in r.runs] == [[67, 65, 64]]


def test_an_octave_leap_to_the_adjacent_pc_is_not_a_step():
    # C5 down to B3 is pc-adjacent but register-distant: a leap, not a walk
    r = find_scale_runs(_line([72, 59, 57, 55]), MAJOR, 0, min_notes=3)
    assert len(r.runs) == 1 and r.runs[0].midis == [59, 57, 55]


def test_step_sizes_follow_the_scale_not_a_fixed_interval():
    # harmonic minor's augmented second (Ab -> B) is one scale step
    r = find_scale_runs(_line([67, 68, 71, 72]), "Harmonic Minor", 0, min_notes=4)
    assert len(r.runs) == 1 and r.runs[0].direction == "ascent"


def test_repeated_notes_break_a_run():
    r = find_scale_runs(_line([67, 65, 65, 64, 62]), MAJOR, 0, min_notes=3)
    assert all(65 not in run.midis[1:] or run.midis.count(65) == 1 for run in r.runs)
    assert [(x.midis) for x in r.runs] == [[65, 64, 62]]


def test_min_notes_gate_and_validation():
    assert find_scale_runs(_line([67, 65, 64]), MAJOR, 0).runs == []   # under default gate
    with pytest.raises(ValueError, match="min_notes"):
        find_scale_runs(_line([60, 62]), MAJOR, 0, min_notes=1)
    with pytest.raises(ValueError, match="root"):
        find_scale_runs(_line([60, 62]), MAJOR)          # scale without root
    with pytest.raises(ValueError, match="Unknown scale"):
        find_scale_runs(_line([60, 62]), "Klingon", 0)


def test_inferred_key_is_cited_and_matches_declared():
    midis = [72, 71, 69, 67, 65, 64, 62, 60]             # unambiguous C major
    inferred = find_scale_runs(_line(midis))
    declared = find_scale_runs(_line(midis), MAJOR, 0)
    assert inferred.key_inferred and not declared.key_inferred
    assert inferred.root_pc == 0
    assert [r.to_dict() for r in inferred.runs] == [r.to_dict() for r in declared.runs]


def test_line_conventions_match_melodic_analysis():
    two_voices = _canonical_sequence(
        [[0, 1, 60, 90, "a"], [1, 1, 62, 90, "a"], [0, 4, 40, 90, "b"]])
    with pytest.raises(ValueError, match="voice"):
        find_scale_runs(two_voices, MAJOR, 0)
    overlap = _canonical_sequence([[0, 4, 60, 90, "m"], [1, 1, 62, 90, "m"]])
    with pytest.raises(ValueError, match="monophonic"):
        find_scale_runs(overlap, MAJOR, 0)


def test_deterministic():
    midis = [67, 65, 64, 62, 60, 62, 64, 65, 67, 69, 71, 72]
    a = find_scale_runs(_line(midis), MAJOR, 0, min_notes=3).to_dict()
    b = find_scale_runs(_line(midis), MAJOR, 0, min_notes=3).to_dict()
    assert a == b


def test_mcp_parity():
    from mts.mcp import tools

    out = tools.find_scale_runs(
        events=[[i, 1, m, 90, "m"] for i, m in enumerate([67, 65, 64, 62, 60])],
        scale=MAJOR, root_pc=0)
    assert out["descents"] == 1
    assert out["runs"][0]["degrees"] == [5, 4, 3, 2, 1]
