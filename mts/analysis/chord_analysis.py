"""Chord analysis utilities."""

from __future__ import annotations

import itertools
from collections import Counter, deque
from dataclasses import dataclass

from ..core.bitmask import rotate_mask
from ..core.chord import Chord
from ..core.enharmonics import PC_TO_NAMES, SpellingPref, name_for_pc
from ..core.symmetry import mask_symmetry_order


@dataclass
class ChordAnalysisRequest:
    """Container for chord analysis instructions."""

    chord: Chord
    tonic_pc: int | None = None
    include_inversions: bool = True
    include_voicings: bool = True
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


def _reflection_axes(pcs: set[int]) -> list[dict[str, object]]:
    axes: list[dict[str, object]] = []
    if not pcs:
        return axes
    for axis in range(12):
        reflected_pitch = {((2 * axis - pc) % 12) for pc in pcs}
        if reflected_pitch == pcs:
            axes.append({"type": "pitch", "center": axis})
        reflected_between = {((2 * axis + 1 - pc) % 12) for pc in pcs}
        if reflected_between == pcs:
            axes.append({"type": "between", "center": (axis + 0.5) % 12})
    unique_axes: list[dict[str, object]] = []
    seen: set[tuple[str, float | int]] = set()
    for axis in axes:
        key = (axis["type"], axis["center"])
        if key in seen:
            continue
        seen.add(key)
        unique_axes.append(axis)
    return unique_axes


def _symmetry_data(chord: Chord) -> dict[str, object]:
    pcs = set(chord.pcs)
    if not pcs:
        return {
            "rotational_order": 0,
            "rotational_steps": [],
            "achiral": False,
            "reflection_axes": [],
        }
    mask = chord.mask
    rotational_steps = [step for step in range(1, 12) if rotate_mask(mask, step) == mask]
    order = mask_symmetry_order(mask)
    reflection_axes = _reflection_axes(pcs)
    return {
        "rotational_order": order,
        "rotational_steps": rotational_steps or [12],
        "achiral": bool(reflection_axes),
        "reflection_axes": reflection_axes,
    }


def _interval_summary(pcs: list[int]) -> dict[str, object]:
    if not pcs:
        return {
            "cardinality": 0,
            "interval_vector": [0] * 6,
            "distinct_pcs": 0,
            "span_semitones": 0,
            "span_compact": 0,
            "interval_pairs": [],
        }
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
    return {
        "cardinality": len(pcs),
        "distinct_pcs": len(unique),
        "interval_vector": vector,
        "smallest_interval": smallest,
        "largest_interval": largest,
        "span_semitones": span_linear,
        "span_compact": span_compact,
        "interval_pairs": pairwise,
    }


def _enharmonic_spellings(
    pcs: list[int],
    *,
    prefer: SpellingPref,
    key_signature: int | None,
) -> list[dict[str, object]]:
    seen: set[int] = set()
    spellings: list[dict[str, object]] = []
    for pc in pcs:
        if pc in seen:
            continue
        seen.add(pc)
        preferred = name_for_pc(pc, prefer=prefer, key_signature=key_signature)
        aliases = PC_TO_NAMES.get(pc % 12, [preferred])
        spellings.append(
            {
                "pc": pc,
                "preferred": preferred,
                "alternates": [name for name in aliases if name != preferred] or [],
            }
        )
    return spellings


def _normalize_register(values: list[int]) -> list[int]:
    if not values:
        return []
    ordered = sorted(values)
    normalized = [ordered[0]]
    for val in ordered[1:]:
        nxt = val
        while nxt <= normalized[-1]:
            nxt += 12
        normalized.append(nxt)
    return normalized


def _tonnetz_analysis(chord: Chord) -> dict[str, object]:
    coords = _tonnetz_coordinates()
    chord_coords = {pc: coords.get(pc) for pc in chord.pcs if pc in coords}
    if not chord_coords:
        return {"coordinates": {}, "centroid": None}
    totals = [0.0, 0.0, 0.0]
    for triple in chord_coords.values():
        for idx, value in enumerate(triple):
            totals[idx] += value
    count = len(chord_coords)
    centroid = tuple(total / count for total in totals)
    return {
        "coordinates": chord_coords,
        "centroid": centroid,
    }


def _relative_tonic_analysis(
    chord: Chord,
    tonic_pc: int,
    label_style: str,
) -> dict[str, object]:
    root_interval = (chord.root_pc - tonic_pc) % 12
    return {
        "tonic_pc": tonic_pc,
        "root_interval_from_tonic": root_interval,
        "root_interval_label": _label_interval(root_interval, label_style),
    }


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
            0: "P1",
            1: "m2",
            2: "M2",
            3: "m3",
            4: "M3",
            5: "P4",
            6: "TT",
            7: "P5",
            8: "m6",
            9: "M6",
            10: "m7",
            11: "M7",
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
) -> list[dict[str, object]]:
    pcs = list(chord.pcs)
    inversions: list[dict[str, object]] = []
    for idx, root_pc in enumerate(pcs):
        rotated = pcs[idx:] + pcs[:idx]
        intervals = [((pc - root_pc) % 12) for pc in rotated]
        note_names = [
            name_for_pc(pc, prefer=spelling, key_signature=key_sig)
            for pc in rotated
        ]
        inversions.append(
            {
                "root_pc": root_pc,
                "intervals": intervals,
                "interval_labels": [_label_interval(iv, label_style) for iv in intervals],
                "note_names": note_names,
            }
        )
    return inversions


def _generate_voicings(
    chord: Chord,
    spelling: SpellingPref,
    key_sig: int | None,
) -> dict[str, object]:
    pcs = list(chord.pcs)
    relative = sorted(((pc - chord.root_pc) % 12) for pc in pcs)
    closed_stack = _normalize_register(relative)

    def make_voicing(intervals: list[int], *, label: str) -> dict[str, object]:
        ordered = _normalize_register(intervals)
        modulo = [iv % 12 for iv in ordered]
        return {
            "label": label,
            "semitones_from_root": ordered,
            "intervals_mod_12": modulo,
            "spread": (ordered[-1] - ordered[0]) if len(ordered) > 1 else 0,
            "note_names": [
                name_for_pc((chord.root_pc + iv) % 12, prefer=spelling, key_signature=key_sig)
                for iv in ordered
            ],
        }

    voicings: dict[str, object] = {
        "closed": make_voicing(closed_stack, label="closed"),
    }

    if len(closed_stack) >= 3:
        drop2 = closed_stack.copy()
        drop2[-2] -= 12
        voicings["drop2"] = make_voicing(drop2, label="drop2")
    if len(closed_stack) >= 4:
        drop3 = closed_stack.copy()
        drop3[-3] -= 12
        voicings["drop3"] = make_voicing(drop3, label="drop3")

    return voicings


def analyze_chord(request: ChordAnalysisRequest) -> dict[str, object]:
    """Return a skeleton analysis dictionary for the given chord."""

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
    report: dict[str, object] = {
        "root_pc": request.chord.root_pc,
        "quality": request.chord.quality.name,
        "pcs": pcs,
        "mask": request.chord.mask,
        "cardinality": len(pcs),
        "intervals_relative_to_root": relative_to_root,
        "interval_matrix": pairwise_matrix,
        "interval_matrix_labels": _label_matrix(pairwise_matrix, request.interval_label_style),
        "interval_class_histogram": histogram_labeled,
        "interval_class_histogram_numeric": histogram_numeric,
        "inverted_interval_matrix": inverted_matrix,
        "inverted_interval_matrix_labels": _label_matrix(inverted_matrix, request.interval_label_style),
        "inverted_interval_class_histogram": inverted_hist_labels,
        "inverted_interval_class_histogram_numeric": inverted_hist_numeric,
        "interval_vector": interval_vector,
        "interval_summary": _interval_summary(pcs),
        "symmetry": _symmetry_data(request.chord),
        "tonnetz": _tonnetz_analysis(request.chord),
    }
    report["note_names"] = request.chord.spelled(prefer=request.spelling, key_signature=request.key_signature)
    if request.tonic_pc is not None:
        tonic_summary = _relative_tonic_analysis(request.chord, request.tonic_pc, request.interval_label_style)
        tonic_summary["note_names_relative_to_tonic"] = [
            {
                "note": name_for_pc(pc, prefer=request.spelling, key_signature=request.key_signature),
                "relative_pc": (pc - request.tonic_pc) % 12,
                "relative_label": _label_interval((pc - request.tonic_pc) % 12, request.interval_label_style),
            }
            for pc in request.chord.pcs
        ]
        report["tonic_context"] = tonic_summary
    if request.include_inversions:
        report["inversions"] = _generate_inversions(
            request.chord,
            request.spelling,
            request.key_signature,
            request.interval_label_style,
        )
    if request.include_voicings:
        report["voicings"] = _generate_voicings(
            request.chord,
            request.spelling,
            request.key_signature,
        )
    if request.include_enharmonics:
        report["enharmonics"] = _enharmonic_spellings(
            pcs,
            prefer=request.spelling,
            key_signature=request.key_signature,
        )
    return report
