"""Melodic atoms: per-note vocabulary for a single line (Phase 4.6 WS0).

The second Workstream 0 item: contour, step/leap classification,
approach/departure intervals, and non-harmonic-tone (NHT) typing — the
vocabulary counterpoint and voice-leading rules quantify over, and the
sequential atoms cadence detection (gap 7) and harmonic segmentation will
reuse.

A melody is **one voice's** monophonic note stream. ``analyze_melody`` takes
the line from an explicit ``voice`` label, or from the whole sequence when it
carries at most one voice; a multi-voice sequence without a ``voice`` argument
errors (the engine does not pick a part for you), as does a line with
overlapping notes (not monophonic — no claim).

Interval classes use the species-counterpoint mapping over semitones:
``unison`` 0 · ``step`` 1–2 (seconds) · ``skip`` 3–4 (thirds) · ``leap`` ≥5
(fourths and wider). This is a definitional vocabulary (like figured bass),
not an empirical knob.

NHT typing is **harmony-relative and never guessed**: it runs only when the
caller provides harmony spans ``(start_beat, end_beat, pcs)`` — from dataset
records, a chord track, or any external analysis. A note is typed by the
span containing its onset; chord tones (pc in the span's set) are not NHTs.
Non-chord tones classify by approach/departure pattern, checked in this
order (first match wins):

- ``pedal`` — unison approach and unison departure (held/repeated through
  the harmony);
- ``suspension`` — unison approach (prepared), resolved down by step;
- ``anticipation`` — unison departure (arrives early, then the harmony
  catches up);
- ``passing`` — step approach and step departure in the same direction;
- ``neighbor`` — step approach and step departure in opposite directions;
- ``appoggiatura`` — skip/leap approach, step departure;
- ``escape`` — step approach, skip/leap departure;
- ``free`` — anything else, including first/last notes (no approach or no
  departure to pattern-match).

Notes outside every provided span get no claim (``is_chord_tone=None``).

Known limitation (theory-grounding review pass #1): typing is
**onset-based** — a note is judged in the span containing its onset only.
A *tied* suspension (one held note across the harmony change — the most
common kind) is therefore invisible: the sustained portion still reads as
the chord tone it was at onset, even where the harmony has moved under it.
Only re-attacked suspensions (unison approach) are typed. Tie-aware typing
(judging a note against every span it overlaps) is the recorded refinement.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from collections.abc import Iterable, Sequence as SequenceABC

from ..core.bitmask import mask_from_pcs
from .sequence import Sequence

_EPS = 1e-9


def interval_class_name(semitones: int) -> str:
    """The species-counterpoint class of a melodic interval (absolute size)."""

    size = abs(int(semitones))
    if size == 0:
        return "unison"
    if size <= 2:
        return "step"
    if size <= 4:
        return "skip"
    return "leap"


@dataclass(frozen=True)
class MelodicNoteAtoms:
    """One note's melodic atoms (intervals signed, in semitones).

    ``approach_*`` / ``departure_*`` are ``None`` at the line's edges.
    ``is_chord_tone`` / ``nht_type`` are ``None`` when no harmony span covers
    the note (or none was provided) — absence of context is not a claim.
    """

    onset: float
    duration: float
    midi: int
    pc: int
    approach_interval: int | None
    departure_interval: int | None
    approach_class: str | None
    departure_class: str | None
    is_chord_tone: bool | None
    nht_type: str | None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class MelodicAnalysis:
    """A line's melodic atoms: per-note detail plus line-level summaries."""

    voice: str | None
    notes: list[MelodicNoteAtoms]
    intervals: list[int]
    interval_classes: list[str]
    parsons_code: str  # *, then u/d/r per interval (Parsons 1975)
    ambitus_semitones: int
    lowest_midi: int
    highest_midi: int
    harmony_provided: bool

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def _line_events(sequence: Sequence, voice: str | None):
    voices = sequence.voices()
    if voice is not None:
        if voice not in voices:
            raise ValueError(
                f"Voice {voice!r} not present (voices: {list(voices) or 'none'})."
            )
        events = sequence.filter_voice(voice).events
    else:
        if len(voices) > 1:
            raise ValueError(
                f"Sequence has {len(voices)} voices ({list(voices)}); "
                "pass voice=... — the engine does not pick a part for you."
            )
        events = sequence.events
    if not events:
        raise ValueError("analyze_melody needs at least one event.")
    ordered = sorted(events, key=lambda e: (e.onset, e.pitch.midi))
    for prev, nxt in zip(ordered, ordered[1:]):
        if nxt.onset < prev.offset - _EPS:
            raise ValueError(
                f"Line is not monophonic: events at beats {prev.onset} and "
                f"{nxt.onset} overlap. Melodic atoms describe one voice's line."
            )
    return ordered


def _normalize_harmony(
    harmony: Iterable[tuple[float, float, Iterable[int]]],
) -> list[tuple[float, float, int]]:
    spans: list[tuple[float, float, int]] = []
    for start, end, pcs in harmony:
        start, end = float(start), float(end)
        if end - start <= _EPS:
            raise ValueError(f"Harmony span [{start}, {end}) has no extent.")
        mask = mask_from_pcs({int(pc) % 12 for pc in pcs})
        if mask == 0:
            raise ValueError(f"Harmony span [{start}, {end}) has no pitch classes.")
        spans.append((start, end, mask))
    return sorted(spans)


def _chord_tone_at(
    spans: list[tuple[float, float, int]], onset: float, pc: int
) -> bool | None:
    for start, end, mask in spans:
        if start - _EPS <= onset < end - _EPS:
            return bool(mask & (1 << pc))
    return None  # no span covers this note: no claim


def _nht_type(
    approach: int | None, departure: int | None, *, is_chord_tone: bool
) -> str | None:
    if is_chord_tone:
        return None
    if approach is None or departure is None:
        return "free"
    a_class = interval_class_name(approach)
    d_class = interval_class_name(departure)
    if a_class == "unison" and d_class == "unison":
        return "pedal"
    if a_class == "unison" and d_class == "step" and departure < 0:
        return "suspension"
    if d_class == "unison":
        return "anticipation"
    if a_class == "step" and d_class == "step":
        return "passing" if (approach > 0) == (departure > 0) else "neighbor"
    if a_class in ("skip", "leap") and d_class == "step":
        return "appoggiatura"
    if a_class == "step" and d_class in ("skip", "leap"):
        return "escape"
    return "free"


def analyze_melody(
    sequence: Sequence,
    *,
    voice: str | None = None,
    harmony: Iterable[tuple[float, float, Iterable[int]]] | None = None,
) -> MelodicAnalysis:
    """Melodic atoms for one line: intervals, classes, contour, NHT typing.

    ``harmony`` (optional) is an iterable of ``(start_beat, end_beat, pcs)``
    spans; without it no chord-tone or NHT claims are made.
    """

    events = _line_events(sequence, voice)
    spans = _normalize_harmony(harmony) if harmony is not None else None

    midis = [e.pitch.midi for e in events]
    intervals = [b - a for a, b in zip(midis, midis[1:])]
    parsons = "*" + "".join(
        "r" if iv == 0 else ("u" if iv > 0 else "d") for iv in intervals
    )

    notes: list[MelodicNoteAtoms] = []
    for i, event in enumerate(events):
        approach = intervals[i - 1] if i > 0 else None
        departure = intervals[i] if i < len(intervals) else None
        if spans is None:
            chord_tone: bool | None = None
            nht: str | None = None
        else:
            chord_tone = _chord_tone_at(spans, event.onset, event.pitch.pc)
            nht = (
                None
                if chord_tone is None
                else _nht_type(approach, departure, is_chord_tone=chord_tone)
            )
        notes.append(
            MelodicNoteAtoms(
                onset=event.onset,
                duration=event.duration,
                midi=event.pitch.midi,
                pc=event.pitch.pc,
                approach_interval=approach,
                departure_interval=departure,
                approach_class=interval_class_name(approach) if approach is not None else None,
                departure_class=interval_class_name(departure) if departure is not None else None,
                is_chord_tone=chord_tone,
                nht_type=nht,
            )
        )

    return MelodicAnalysis(
        voice=voice,
        notes=notes,
        intervals=intervals,
        interval_classes=[interval_class_name(iv) for iv in intervals],
        parsons_code=parsons,
        ambitus_semitones=max(midis) - min(midis),
        lowest_midi=min(midis),
        highest_midi=max(midis),
        harmony_provided=spans is not None,
    )


__all__ = [
    "MelodicAnalysis",
    "MelodicNoteAtoms",
    "analyze_melody",
    "interval_class_name",
]
