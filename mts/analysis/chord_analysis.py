"""Chord analysis utilities — pure identity / numeric analysis.

This layer produces pitch-class and interval *facts*. Spelling (note names),
enharmonic alternates, and interval-label *style* are display concerns rendered at
the edge by :mod:`mts.context.result_format` from a ``DisplayContext`` — they do
not live here (ROADMAP Phase 3; CLAUDE.md "combinatorics here, presentation at the
edge").
"""

from __future__ import annotations

import itertools
from collections import Counter, deque
from dataclasses import dataclass

from ..core.chord import Chord
from ..core.realization import Realization
from ..core.symmetry import mask_symmetry_order, rotational_steps
from .errors import require_realization
from .pcset_math import interval_vector as _interval_vector
from .pcset_math import reflection_axes as _reflection_axes
from .pcset_math import set_class_data
from .voicings import voicing_shapes
from .results import (
    ChordAnalysisResult,
    ChordIntervalSummary,
    Inversion,
    SymmetryData,
    TonnetzAnalysis,
    TonicContext,
    VoicingAnalysis,
)


@dataclass
class ChordAnalysisRequest:
    """Container for chord analysis instructions.

    ``analyze_chord`` requires only the identity (a pitch-class set), so this
    request carries no register and no display preferences. Register-dependent
    voicing analysis lives in ``analyze_voicing``; spelling/labels are applied at
    the display edge from a ``DisplayContext``.
    """

    chord: Chord
    tonic_pc: int | None = None
    include_inversions: bool = True
    include_set_class: bool = True


def _intervals_relative_to_root(chord: Chord) -> list[int]:
    return [((pc - chord.root_pc) % 12) for pc in chord.pcs]


def _interval_matrix(pcs: list[int]) -> list[list[int]]:
    matrix: list[list[int]] = []
    for a in pcs:
        row: list[int] = []
        for b in pcs:
            row.append((b - a) % 12)
        matrix.append(row)
    return matrix


def _interval_class_histogram(intervals: list[int]) -> dict[int, int]:
    reduced = [(iv if iv <= 6 else 12 - iv) for iv in intervals if iv != 0]
    counts = Counter(reduced)
    return dict(sorted(counts.items()))


def _symmetry_data(chord: Chord) -> SymmetryData:
    pcs = set(chord.pcs)
    if not pcs:
        return SymmetryData(
            rotational_order=0,
            rotational_steps=[],
            achiral=False,
            reflection_axes=[],
        )
    mask = chord.mask
    reflection_axes = _reflection_axes(pcs)
    return SymmetryData(
        rotational_order=mask_symmetry_order(mask),
        rotational_steps=list(rotational_steps(mask)),
        achiral=bool(reflection_axes),
        reflection_axes=reflection_axes,
    )


def _interval_summary(pcs: list[int]) -> ChordIntervalSummary:
    if not pcs:
        return ChordIntervalSummary(
            cardinality=0,
            distinct_pcs=0,
            interval_vector=[0] * 6,
            smallest_interval=None,
            largest_interval=None,
            span_semitones=0,
            span_compact=0,
            interval_pairs=[],
        )
    unique = sorted({pc % 12 for pc in pcs})
    vector = _interval_vector(unique)
    pairwise = sorted(((b - a) % 12) for a, b in itertools.combinations(unique, 2))
    nonzero = [iv for iv in pairwise if iv != 0]
    smallest = min(nonzero) if nonzero else None
    largest = max(nonzero) if nonzero else None
    span_linear = max(unique) - min(unique) if len(unique) > 1 else 0
    doubled = unique + [pc + 12 for pc in unique]
    span_compact = span_linear
    if len(unique) > 1:
        span_compact = min(
            max(doubled[i : i + len(unique)]) - doubled[i] for i in range(len(unique))
        )
    return ChordIntervalSummary(
        cardinality=len(pcs),
        distinct_pcs=len(unique),
        interval_vector=vector,
        smallest_interval=smallest,
        largest_interval=largest,
        span_semitones=span_linear,
        span_compact=span_compact,
        interval_pairs=pairwise,
    )


def _tonnetz_analysis(chord: Chord) -> TonnetzAnalysis:
    coords = _tonnetz_coordinates()
    chord_coords = {pc: coords[pc] for pc in chord.pcs if pc in coords}
    if not chord_coords:
        return TonnetzAnalysis(coordinates={}, centroid=None)
    totals = [0.0, 0.0, 0.0]
    for triple in chord_coords.values():
        for idx, value in enumerate(triple):
            totals[idx] += value
    count = len(chord_coords)
    centroid = (totals[0] / count, totals[1] / count, totals[2] / count)
    return TonnetzAnalysis(coordinates=chord_coords, centroid=centroid)


def _relative_tonic_analysis(chord: Chord, tonic_pc: int) -> TonicContext:
    return TonicContext(
        tonic_pc=tonic_pc,
        root_interval_from_tonic=(chord.root_pc - tonic_pc) % 12,
        relative_pcs=[(pc - tonic_pc) % 12 for pc in chord.pcs],
    )


def _tonnetz_coordinates() -> dict[int, tuple[int, int, int]]:
    operations = [
        (7, (1, 0, 0)),  # perfect fifth
        (4, (0, 1, 0)),  # major third
        (3, (0, 0, 1)),  # minor third
    ]
    coords: dict[int, tuple[int, int, int]] = {0: (0, 0, 0)}
    queue = deque([0])
    while queue and len(coords) < 12:
        pc = queue.popleft()
        base = coords[pc]
        for interval, delta in operations:
            target = (pc + interval) % 12
            if target not in coords:
                coords[target] = tuple(base[i] + delta[i] for i in range(3))
                queue.append(target)
    return coords


def _invert_matrix(matrix: list[list[int]]) -> list[list[int]]:
    return [[(-iv) % 12 for iv in row] for row in matrix]


_POSITION_NAMES = [
    "root position",
    "first inversion",
    "second inversion",
    "third inversion",
    "fourth inversion",
    "fifth inversion",
]

# Conventional figured-bass shorthand, keyed by (cardinality, inversion index).
# Defined for tertian triads and seventh chords; other cardinalities get no figure.
_FIGURED_BASS: dict[int, dict[int, str]] = {
    3: {0: "5/3", 1: "6", 2: "6/4"},
    4: {0: "7", 1: "6/5", 2: "4/3", 3: "4/2"},
}


def _inversion_naming(cardinality: int, index: int) -> tuple[str, str | None]:
    """Return (position_name, figured_bass) for an inversion index."""

    position = _POSITION_NAMES[index] if index < len(_POSITION_NAMES) else f"inversion {index}"
    figured = _FIGURED_BASS.get(cardinality, {}).get(index)
    return position, figured


def _generate_inversions(chord: Chord) -> list[Inversion]:
    pcs = list(chord.pcs)
    cardinality = len(pcs)
    inversions: list[Inversion] = []
    for idx, root_pc in enumerate(pcs):
        rotated = pcs[idx:] + pcs[:idx]
        intervals = [((pc - root_pc) % 12) for pc in rotated]
        position_name, figured_bass = _inversion_naming(cardinality, idx)
        inversions.append(
            Inversion(
                root_pc=root_pc,
                intervals=intervals,
                position_index=idx,
                position_name=position_name,
                figured_bass=figured_bass,
            )
        )
    return inversions


def analyze_voicing(realization: Realization | None) -> VoicingAnalysis:
    """Register-aware analysis of an actual realization.

    Requires register: raises
    :class:`~mts.analysis.errors.SpecificationError` if handed ``None`` (a
    register-less identity). Every field is read from the real pitches —
    nothing is invented. Works on both voicings (rooted) and voicing templates
    (rootless); the bass and all spans are derived from absolute pitch height.
    Pitch *spelling* is a display concern (apply ``spell_voicing`` at the edge).
    """

    real = require_realization(realization, analysis="analyze_voicing")
    bass = real.bass
    midi = [p.midi for p in real.pitches]
    intervals_from_bass = [p.midi - bass.midi for p in real.pitches]
    spread = max(midi) - min(midi)

    # --- recognition ---------------------------------------------------------
    openness = "closed" if spread <= 12 else "open"
    inversion_index: int | None = None
    position_name: str | None = None
    figured_bass: str | None = None
    voicing_type: str | None = None
    if real.is_rooted:
        root = real.root_pc
        chord_intervals = sorted({(pc - root) % 12 for pc in real.pcs})
        bass_interval = (bass.pc - root) % 12
        if bass_interval in chord_intervals:
            inversion_index = chord_intervals.index(bass_interval)
            position_name, figured_bass = _inversion_naming(len(chord_intervals), inversion_index)
        # Match the actual spacing (distinct pitches, min-anchored) against the
        # shared voicing vocabulary; first match in registry order wins.
        distinct_midi = sorted(set(midi))
        actual_shape = tuple(m - distinct_midi[0] for m in distinct_midi)
        for label, shape in voicing_shapes(chord_intervals).items():
            if shape == actual_shape:
                voicing_type = label
                break

    return VoicingAnalysis(
        spec_level=real.spec_level.label,
        rooted=real.is_rooted,
        root_pc=real.root_pc,
        midi=midi,
        bass_pc=bass.pc,
        bass_midi=bass.midi,
        intervals_from_bass=intervals_from_bass,
        spread_semitones=spread,
        distinct_pcs=list(real.distinct_pcs),
        doublings=list(real.doublings),
        mask=real.reduce_to_key(),
        openness=openness,
        inversion_index=inversion_index,
        position_name=position_name,
        figured_bass=figured_bass,
        voicing_type=voicing_type,
    )


def analyze_chord(request: ChordAnalysisRequest) -> ChordAnalysisResult:
    """Return a typed identity analysis for the given chord.

    Requires only the identity (a pitch-class set); carries no register and
    invents none, and emits no spelled note names (apply
    ``mts.context.result_format.format_chord_analysis`` at the edge). For
    register-aware voicing analysis use ``analyze_voicing``; for generative
    voicing suggestions use ``suggest_voicings``.
    """

    pcs = list(request.chord.pcs)
    pairwise_matrix = _interval_matrix(pcs)
    inverted_matrix = _invert_matrix(pairwise_matrix)
    intervals_flat = [iv for row in pairwise_matrix for iv in row if iv != 0]
    inverted_flat = [iv for row in inverted_matrix for iv in row if iv != 0]

    tonic_context: TonicContext | None = None
    if request.tonic_pc is not None:
        tonic_context = _relative_tonic_analysis(request.chord, request.tonic_pc)

    inversions: list[Inversion] | None = None
    if request.include_inversions:
        inversions = _generate_inversions(request.chord)

    return ChordAnalysisResult(
        root_pc=request.chord.root_pc,
        quality=request.chord.quality.name,
        pcs=pcs,
        mask=request.chord.mask,
        cardinality=len(pcs),
        intervals_relative_to_root=_intervals_relative_to_root(request.chord),
        interval_matrix=pairwise_matrix,
        interval_class_histogram=_interval_class_histogram(intervals_flat),
        inverted_interval_matrix=inverted_matrix,
        inverted_interval_class_histogram=_interval_class_histogram(inverted_flat),
        interval_vector=_interval_vector(pcs),
        interval_summary=_interval_summary(pcs),
        symmetry=_symmetry_data(request.chord),
        tonnetz=_tonnetz_analysis(request.chord),
        tonic_context=tonic_context,
        inversions=inversions,
        set_class=set_class_data(request.chord.mask) if request.include_set_class else None,
    )
