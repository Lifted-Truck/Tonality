"""Scale-analysis regressions.

issue #205: ScaleAnalysisResult.step_pattern must be a transposition-INVARIANT
shape descriptor (resolution (a)) — a sibling of interval_vector — while each
mode in the `modes` list keeps its own root-anchored ascending pattern.
"""

from __future__ import annotations

from mts.core.scale import Scale
from mts.analysis.scale_analysis import analyze_scale, ScaleAnalysisRequest


def _major(t: int) -> Scale:
    return Scale.from_degrees("major", [0, 2, 4, 5, 7, 9, 11]).transpose(t)


def test_step_pattern_is_transposition_invariant():
    patterns = {
        tuple(analyze_scale(ScaleAnalysisRequest(scale=_major(t), tonic_pc=t)).step_pattern)
        for t in range(12)
    }
    # one canonical shape for all 12 roots (the bug produced 2+ root-dependent rotations)
    assert patterns == {(1, 2, 2, 1, 2, 2, 2)}


def test_step_pattern_ignores_tonic_pc_by_design():
    # It is a shape descriptor, not a tonic-relative field; tonic_pc does not rotate it.
    base = _major(0)
    for tonic in (None, 0, 2, 7):
        res = analyze_scale(ScaleAnalysisRequest(scale=base, tonic_pc=tonic))
        assert res.step_pattern == [1, 2, 2, 1, 2, 2, 2]


def test_step_pattern_invariant_but_interval_vector_still_invariant():
    # regression guard: the order-independent aggregate (interval_vector) was
    # always invariant; step_pattern now matches that stability.
    a = analyze_scale(ScaleAnalysisRequest(scale=_major(0), tonic_pc=0))
    b = analyze_scale(ScaleAnalysisRequest(scale=_major(5), tonic_pc=5))
    assert a.step_pattern == b.step_pattern
    assert a.interval_vector == b.interval_vector


def test_modes_keep_distinct_root_anchored_patterns():
    res = analyze_scale(ScaleAnalysisRequest(scale=_major(0), tonic_pc=0))
    mode_patterns = [tuple(m.step_pattern) for m in res.modes]
    assert len(set(mode_patterns)) == len(mode_patterns) == 7  # all 7 diatonic modes differ
    assert mode_patterns[0] == (2, 2, 1, 2, 2, 2, 1)  # Ionian W-W-H-W-W-W-H
    assert mode_patterns[1] == (2, 1, 2, 2, 2, 1, 2)  # Dorian W-H-W-W-W-H-W


def test_pentatonic_shape_is_invariant_too():
    penta = Scale.from_degrees("maj-pentatonic", [0, 2, 4, 7, 9])
    a = tuple(analyze_scale(ScaleAnalysisRequest(scale=penta)).step_pattern)
    b = tuple(analyze_scale(ScaleAnalysisRequest(scale=penta.transpose(3))).step_pattern)
    assert a == b
    assert sum(a) == 12  # steps close the octave
