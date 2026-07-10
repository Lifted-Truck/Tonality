"""The pattern matcher (gap C slice 1): find every occurrence of a melodic
pattern in a sequence — exact under the pattern's declared abstraction.

Analytical, not generative: matching *reduces* material to the pattern's level
and compares; it never invents. The honesty contract:

- a **degree**-level pattern needs a key — ``key=(tonic_pc, mode)`` is required
  and never inferred here (**error, don't guess**; run ``infer_key`` yourself and
  pass its answer if that's what you mean);
- a note with no degree in the key (chromatic) simply cannot match a degree
  element — no enharmonic fudging;
- a **rhythm-free** match reports the actual IOIs it spanned (the "time-warp"
  is surfaced as evidence, not hidden);
- **overlapping occurrences are all reported**, never collapsed;
- a voice line the matcher cannot linearize (simultaneous onsets — a chordal
  "line") is skipped and *named* in ``voices_skipped``, never silently dropped.

Occurrences are over **contiguous** notes of one voice line (a motif is
contiguous; gapped/subsequence matching is the induction-side follow-on).
"""

from __future__ import annotations

from collections.abc import Iterable

from ..temporal import Sequence
from .results import PatternMatches, PatternOccurrence
from .schema import Pattern, parse_pattern

_EPS = 1e-6

_MODE_SCALE: dict[str, tuple[int, ...]] = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),  # natural minor (shared with harmony_stream)
}


def _lines(sequence: Sequence, only_voice) -> tuple[dict, list]:
    """Per-voice note lines sorted by onset; a non-linearizable voice is skipped."""

    by_voice: dict = {}
    for event in sequence.events:
        if only_voice is not _UNSET and event.voice != only_voice:
            continue
        by_voice.setdefault(event.voice, []).append(event)
    lines: dict = {}
    skipped: list = []
    for voice, events in by_voice.items():
        events.sort(key=lambda e: (e.onset, e.pitch.midi))
        if any(
            abs(a.onset - b.onset) <= _EPS
            for a, b in zip(events, events[1:])
        ):
            skipped.append(voice)  # simultaneous onsets — not a single line
            continue
        lines[voice] = events
    return lines, skipped


_UNSET = object()


def _degree_of(midi: int, tonic_pc: int, scale: tuple[int, ...]) -> int | None:
    rel = (midi % 12 - tonic_pc) % 12
    return scale.index(rel) + 1 if rel in scale else None


def find_pattern(
    sequence: Sequence,
    pattern: Pattern | dict,
    *,
    key: tuple[int, str] | None = None,
    voice=_UNSET,
) -> PatternMatches:
    """Every occurrence of *pattern* in *sequence*, per voice line.

    ``key=(tonic_pc, mode)`` is **required** for a degree-level pattern
    (major/minor; error, don't guess) and ignored otherwise. ``voice`` restricts
    matching to one line (``None`` is the unvoiced line). Returns every
    (possibly overlapping) occurrence with its evidence: the matched onsets,
    MIDI pitches, actual IOIs, and the per-level binding (degrees / moves).
    """

    if not isinstance(pattern, Pattern):
        pattern = parse_pattern(pattern)

    scale = None
    tonic = None
    if pattern.pitch_level == "degree":
        if key is None:
            raise ValueError(
                "a degree-level pattern needs key=(tonic_pc, mode) — the matcher "
                "never infers a key (run infer_key and pass its answer if that is "
                "what you mean)."
            )
        tonic = int(key[0]) % 12
        mode = str(key[1]).lower()
        scale = _MODE_SCALE.get(mode)
        if scale is None:
            raise ValueError(
                f"degree matching supports major/minor only, got mode {key[1]!r}."
            )

    lines, skipped = _lines(sequence, voice)
    n = pattern.n_notes
    occurrences: list[PatternOccurrence] = []

    for line_voice in sorted(lines, key=lambda v: (v is None, v)):
        events = lines[line_voice]
        for start in range(len(events) - n + 1):
            window = events[start:start + n]
            midis = [e.pitch.midi for e in window]
            onsets = [e.onset for e in window]
            iois = [round(b - a, 9) for a, b in zip(onsets, onsets[1:])]

            if pattern.time_level == "exact" and any(
                abs(actual - declared) > _EPS
                for actual, declared in zip(iois, pattern.iois)
            ):
                continue

            degrees = None
            moves = None
            if pattern.pitch_level == "exact":
                if tuple(midis) != pattern.elements:
                    continue
            elif pattern.pitch_level == "degree":
                degrees = [_degree_of(m, tonic, scale) for m in midis]
                if any(d is None for d in degrees) or tuple(degrees) != pattern.elements:
                    continue
            else:  # contour
                moves = [
                    "up" if b > a else ("down" if b < a else "same")
                    for a, b in zip(midis, midis[1:])
                ]
                if tuple(moves) != pattern.elements:
                    continue

            occurrences.append(PatternOccurrence(
                voice=line_voice,
                start_beat=onsets[0],
                end_beat=window[-1].offset,
                midis=midis,
                onsets=onsets,
                iois=iois,
                degrees=degrees,
                moves=moves,
            ))

    return PatternMatches(
        pattern_name=pattern.name,
        pattern_version=pattern.version,
        pitch_level=pattern.pitch_level,
        time_level=pattern.time_level,
        key=(tonic, str(key[1]).lower()) if scale is not None else None,
        count=len(occurrences),
        occurrences=occurrences,
        voices_skipped=skipped,
    )


__all__ = ["find_pattern"]
