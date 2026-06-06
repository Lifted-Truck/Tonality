"""Chord analysis utilities."""

from __future__ import annotations

import itertools
from collections import Counter, deque
from dataclasses import dataclass

from ..core.bitmask import rotate_mask
from ..core.chord import Chord
from ..core.enharmonics import PC_TO_NAMES, SpellingPref, name_for_pc
from ..core.realization import Realization
from ..core.symmetry import mask_symmetry_order
from .errors import require_realization
from .results import (
    ChordAnalysisResult,
    ChordIntervalSummary,
    EnharmonicSpelling,
    Inversion,
    NoteInContext,
    ReflectionAxis,
    SymmetryData,
    TonnetzAnalysis,
    TonicContext,
    VoicingAnalysis,
)


@dataclass
class ChordAnalysisRequest:
    """Container for chord analysis instructions.

    ``analyze_chord`` requires only the identity (a pitch-class set), so this
    request carries no register. Register-dependent voicing analysis lives in
    ``analyze_voicing``, which takes a
    :class:`~mts.core.realization.Realization`.
    """

    chord: Chord
    tonic_pc: int | None = None
    include_inversions: bool = True
    include_enharmonics: bool = True
    spelling: SpellingPref = "auto"
    key_signature: int | None = None
    interval_label_style: str = "numeric"  # "numeric" or "classical"


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


def _interval_vector(pcs: list[int]) -> list[int]:
    unique = sorted({pc % 12 for pc in pcs})
    vector = [0] * 6
    for a, b in itertools.combinations(unique, 2):
        diff = (b - a) % 12
        step = diff if diff <= 6 else 12 - diff
        if step == 0 or step > 6:
            continue
        vector[step - 1] += 1
    return vector


def _reflection_axes(pcs: set[int]) -> list[ReflectionAxis]:
    axes: list[ReflectionAxis] = []
    if not pcs:
        return axes
    for axis in range(12):
        reflected_pitch = {((2 * axis - pc) % 12) for pc in pcs}
        if reflected_pitch == pcs:
            axes.append(ReflectionAxis(type="pitch", center=axis))
        reflected_between = {((2 * axis + 1 - pc) % 12) for pc in pcs}
        if reflected_between == pcs:
            axes.append(ReflectionAxis(type="between", center=(axis + 0.5) % 12))
    unique_axes: list[ReflectionAxis] = []
    seen: set[tuple[str, float]] = set()
    for ax in axes:
        key = (ax.type, ax.center)
        if key in seen:
            continue
        seen.add(key)
        unique_axes.append(ax)
    return unique_axes


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
    rotational_steps = [step for step in range(1, 12) if rotate_mask(mask, step) == mask]
    order = mask_symmetry_order(mask)
    reflection_axes = _reflection_axes(pcs)
    return SymmetryData(
        rotational_order=order,
        rotational_steps=rotational_steps or [12],
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


def _enharmonic_spellings(
    pcs: list[int],
    *,
    prefer: SpellingPref,
    key_signature: int | None,
) -> list[EnharmonicSpelling]:
    seen: set[int] = set()
    spellings: list[EnharmonicSpelling] = []
    for pc in pcs:
        if pc in seen:
            continue
        seen.add(pc)
        preferred = name_for_pc(pc, prefer=prefer, key_signature=key_signature)
        aliases = PC_TO_NAMES.get(pc % 12, [preferred])
        spellings.append(
            EnharmonicSpelling(
                pc=pc,
                preferred=preferred,
                alternates=[name for name in aliases if name != preferred] or [],
            )
        )
    return spellings


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


def _relative_tonic_analysis(
    chord: Chord,
    tonic_pc: int,
    label_style: str,
) -> TonicContext:
    root_interval = (chord.root_pc - tonic_pc) % 12
    notes_in_context = [
        NoteInContext(
            note=name_for_pc(pc),
            relative_pc=(pc - tonic_pc) % 12,
            relative_label=_label_interval((pc - tonic_pc) % 12, label_style),
        )
        for pc in chord.pcs
    ]
    return TonicContext(
        tonic_pc=tonic_pc,
        root_interval_from_tonic=root_interval,
        root_interval_label=_label_interval(root_interval, label_style),
        note_names_relative_to_tonic=notes_in_context,
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


def _label_interval(interval: int, style: str) -> str:
    interval %= 12
    if style == "classical":
        classical = {
            0: "P1", 1: "m2", 2: "M2", 3: "m3", 4: "M3", 5: "P4",
            6: "TT", 7: "P5", 8: "m6", 9: "M6", 10: "m7", 11: "M7",
        }
        return classical.get(interval, f"ic{interval}")
    return str(interval)


def _label_matrix(matrix: list[list[int]], style: str) -> list[list[str]]:
    return [[_label_interval(iv, style) for iv in row] for row in matrix]


def _label_histogram(histogram: dict[int, int], style: str) -> dict[str, int]:
    return {_label_interval(k, style): v for k, v in histogram.items()}


def _invert_matrix(matrix: list[list[int]]) -> list[list[int]]:
    return [[(-iv) % 12 for iv in row] for row in matrix]


def _generate_inversions(
    chord: Chord,
    spelling: SpellingPref,
    key_sig: int | None,
    label_style: str,
) -> list[Inversion]:
    pcs = list(chord.pcs)
    inversions: list[Inversion] = []
    for idx, root_pc in enumerate(pcs):
        rotated = pcs[idx:] + pcs[:idx]
        intervals = [((pc - root_pc) % 12) for pc in rotated]
        note_names = [
            name_for_pc(pc, prefer=spelling, key_signature=key_sig)
            for pc in rotated
        ]
        inversions.append(
            Inversion(
                root_pc=root_pc,
                intervals=intervals,
                interval_labels=[_label_interval(iv, label_style) for iv in intervals],
                note_names=note_names,
            )
        )
    return inversions


def analyze_voicing(
    realization: Realization | None,
    *,
    spelling: SpellingPref = "auto",
    key_signature: int | None = None,
) -> VoicingAnalysis:
    """Register-aware analysis of an actual realization.

    Requires register: raises
    :class:`~mts.analysis.errors.SpecificationError` if handed ``None`` (a
    register-less identity). Every field is read from the real pitches —
    nothing is invented. Works on both voicings (rooted) and voicing templates
    (rootless); the bass and all spans are derived from absolute pitch height.
    """

    real = require_realization(realization, analysis="analyze_voicing")
    bass = real.bass
    midi = [p.midi for p in real.pitches]
    note_names = [
        f"{name_for_pc(p.pc, prefer=spelling, key_signature=key_signature)}{p.octave}"
        for p in real.pitches
    ]
    intervals_from_bass = [p.midi - bass.midi for p in real.pitches]
    return VoicingAnalysis(
        spec_level=real.spec_level.label,
        rooted=real.is_rooted,
        root_pc=real.root_pc,
        midi=midi,
        note_names=note_names,
        bass_pc=bass.pc,
        bass_midi=bass.midi,
        intervals_from_bass=intervals_from_bass,
        spread_semitones=max(midi) - min(midi),
        distinct_pcs=list(real.distinct_pcs),
        doublings=list(real.doublings),
        mask=real.reduce_to_key(),
    )


def analyze_chord(request: ChordAnalysisRequest) -> ChordAnalysisResult:
    """Return a typed identity analysis for the given chord.

    Requires only the identity (a pitch-class set); carries no register and
    invents none. For register-aware voicing analysis use ``analyze_voicing``;
    for generative voicing suggestions use ``suggest_voicings``.
    """

    pcs = list(request.chord.pcs)
    relative_to_root = _intervals_relative_to_root(request.chord)
    pairwise_matrix = _interval_matrix(pcs)
    inverted_matrix = _invert_matrix(pairwise_matrix)
    intervals_flat = [iv for row in pairwise_matrix for iv in row if iv != 0]
    histogram_numeric = _interval_class_histogram(intervals_flat)
    histogram_labeled = _label_histogram(histogram_numeric, request.interval_label_style)
    inverted_flat = [iv for row in inverted_matrix for iv in row if iv != 0]
    inverted_hist_numeric = _interval_class_histogram(inverted_flat)
    inverted_hist_labels = _label_histogram(inverted_hist_numeric, request.interval_label_style)
    interval_vector = _interval_vector(pcs)

    tonic_context: TonicContext | None = None
    if request.tonic_pc is not None:
        tonic_context = _relative_tonic_analysis(
            request.chord, request.tonic_pc, request.interval_label_style
        )

    inversions: list[Inversion] | None = None
    if request.include_inversions:
        inversions = _generate_inversions(
            request.chord,
            request.spelling,
            request.key_signature,
            request.interval_label_style,
        )

    enharmonics: list[EnharmonicSpelling] | None = None
    if request.include_enharmonics:
        enharmonics = _enharmonic_spellings(
            pcs,
            prefer=request.spelling,
            key_signature=request.key_signature,
        )

    return ChordAnalysisResult(
        root_pc=request.chord.root_pc,
        quality=request.chord.quality.name,
        pcs=pcs,
        mask=request.chord.mask,
        cardinality=len(pcs),
        intervals_relative_to_root=relative_to_root,
        interval_matrix=pairwise_matrix,
        interval_matrix_labels=_label_matrix(pairwise_matrix, request.interval_label_style),
        interval_class_histogram=histogram_labeled,
        interval_class_histogram_numeric=histogram_numeric,
        inverted_interval_matrix=inverted_matrix,
        inverted_interval_matrix_labels=_label_matrix(inverted_matrix, request.interval_label_style),
        inverted_interval_class_histogram=inverted_hist_labels,
        inverted_interval_class_histogram_numeric=inverted_hist_numeric,
        interval_vector=interval_vector,
        interval_summary=_interval_summary(pcs),
        symmetry=_symmetry_data(request.chord),
        tonnetz=_tonnetz_analysis(request.chord),
        note_names=request.chord.spelled(prefer=request.spelling, key_signature=request.key_signature),
        tonic_context=tonic_context,
        inversions=inversions,
        enharmonics=enharmonics,
    )
