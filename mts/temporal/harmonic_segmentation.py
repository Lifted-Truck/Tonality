"""Harmonic segmentation (gap B slice-2a): a note ``Sequence`` → a chord stream.

The harmony rule family and harmony induction read an **explicit** chord stream
``[(root_pc, quality), …]`` + key. This module derives that stream from raw
notes, so evaluation/induction can point at real MIDI instead of hand-annotated
progressions — the recorded slice-2 unlock.

**The metric-grid model** (the chosen slice, ROADMAP gap B slice-2a): one chord
per metric window (a bar by default; ``subdivisions`` splits it). Within each
window the pitch classes are weighted by **sounding duration × metric emphasis**
(downbeat onsets count more), the salient set is thresholded, and that set is
named against the catalog inside the piece's inferred (or supplied) key. It is an
**analytical reduction** (notes → identity stream), and it **errors, not
guesses**: a window that names no catalog chord is surfaced as unnameable — never
fabricated. Consecutive identical labels collapse, so a chord held across bars is
one stream entry.

Honest limits (recorded, slice-2b+): non-harmonic tones are only *approximated*
(the salience threshold drops brief passers; true NHT nesting under a parent
harmony is deferred), and the key is a single global reading (per-window local
key regions are deferred). See ROADMAP gap B.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..analysis.key_induction import candidate_context, infer_key
from ..analysis.naming import name_chord
from ..analysis.results import KeyCandidate
from .sequence import Sequence

_EPS = 1e-9


@dataclass(frozen=True)
class ChordSpan:
    """One metric window and the chord (if any) it reduces to."""

    start_beat: float
    end_beat: float
    bar: int
    salient_pcs: tuple[int, ...]   # pcs kept after the duration×emphasis threshold
    root_pc: int | None            # None ⇒ no chord (rest or unnameable window)
    quality: str | None
    is_ambiguous: bool             # near-tie among namings (name_chord's flag)
    reason: str | None             # why no chord (None when a chord was named)

    def to_dict(self) -> dict:
        return {
            "start_beat": self.start_beat,
            "end_beat": self.end_beat,
            "bar": self.bar,
            "salient_pcs": list(self.salient_pcs),
            "root_pc": self.root_pc,
            "quality": self.quality,
            "is_ambiguous": self.is_ambiguous,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ChordSegmentation:
    """A segmented piece: the key, every window, and the collapsed chord stream."""

    tonic_pc: int
    mode: str
    key_inferred: bool     # True: inferred here; False: supplied by the caller
    key_margin: float      # infer_key top-two margin (0.0 when key was supplied)
    spans: list[ChordSpan]
    chords: list[tuple[int, str]]   # named windows, consecutive repeats collapsed

    @property
    def key(self) -> tuple[int, str]:
        """``(tonic_pc, mode)`` — ready for ``build_harmony_stream`` / ``evaluate``."""
        return (self.tonic_pc, self.mode)

    def to_dict(self) -> dict:
        return {
            "tonic_pc": self.tonic_pc,
            "mode": self.mode,
            "key_inferred": self.key_inferred,
            "key_margin": self.key_margin,
            "spans": [s.to_dict() for s in self.spans],
            "chords": [[root, quality] for root, quality in self.chords],
        }


def _window_pc_weights(
    sequence: Sequence, start: float, end: float, downbeat_emphasis: float
) -> list[float]:
    """Duration-weighted pc content of ``[start, end)``, downbeat onsets scaled."""

    weights = [0.0] * 12
    for event in sequence.events:
        if event.onset >= end - _EPS or event.offset <= start + _EPS:
            continue
        overlap = min(event.offset, end) - max(event.onset, start)
        if overlap <= _EPS:
            continue
        emphasis = (
            downbeat_emphasis
            if sequence.meter.metric_position(event.onset).is_downbeat
            else 1.0
        )
        weights[event.pitch.pc] += overlap * emphasis
    return weights


def segment_to_chords(
    sequence: Sequence,
    *,
    key: tuple[int, str] | None = None,
    subdivisions: int = 1,
    min_pc_weight: float = 0.1,
    downbeat_emphasis: float = 2.0,
    session=None,
) -> ChordSegmentation:
    """Reduce a note ``Sequence`` to a chord stream on a metric grid.

    ``key`` — supply ``(tonic_pc, mode)`` to fix the key; ``None`` infers it once
    globally (``infer_key``), surfacing the top-two margin. ``subdivisions`` splits
    each bar into that many equal windows (1 = one chord per bar). ``min_pc_weight``
    is the salience floor: a pc contributing less than this fraction of a window's
    weighted content is treated as non-harmonic and dropped. ``downbeat_emphasis``
    scales the duration weight of notes that *onset* on a downbeat.
    ``session`` merges that session's registered chord qualities into the catalog.

    Raises ``ValueError`` on an empty sequence or ``subdivisions < 1``. A window
    that reduces to no catalog chord is recorded with ``root_pc=None`` and a
    ``reason`` — never fabricated (error, not guess).
    """

    if subdivisions < 1:
        raise ValueError(f"subdivisions must be >= 1, got {subdivisions}.")
    if not sequence.events:
        raise ValueError("segment_to_chords needs a non-empty sequence.")

    if key is None:
        induction = infer_key(sequence)
        candidate = induction.best
        tonic_pc, mode = candidate.tonic_pc, candidate.mode
        margin, inferred = induction.margin, True
    else:
        tonic_pc, mode = int(key[0]) % 12, str(key[1])
        candidate = KeyCandidate(tonic_pc=tonic_pc, mode=mode, score=1.0)
        margin, inferred = 0.0, False
    context = candidate_context(candidate)

    from ..io.loaders import load_chord_qualities

    catalog = load_chord_qualities(session)

    spans: list[ChordSpan] = []
    for bar_start, bar_end, bar in sequence.meter.bar_spans(sequence.duration_beats):
        step = (bar_end - bar_start) / subdivisions
        for k in range(subdivisions):
            start = bar_start + k * step
            end = bar_end if k == subdivisions - 1 else start + step
            weights = _window_pc_weights(sequence, start, end, downbeat_emphasis)
            total = sum(weights)
            if total <= _EPS:
                spans.append(ChordSpan(start, end, bar, (), None, None, False,
                                       "rest (no sounding pitch)"))
                continue
            salient = tuple(
                pc for pc in range(12) if weights[pc] >= min_pc_weight * total
            )
            naming = name_chord(salient, context, catalog=catalog)
            if naming.chosen is None:
                spans.append(ChordSpan(
                    start, end, bar, salient, None, None, False,
                    f"no catalog chord matches the salient set {list(salient)}",
                ))
                continue
            interp = naming.chosen.interpretation
            spans.append(ChordSpan(
                start, end, bar, salient, interp.root_pc, interp.quality,
                naming.is_ambiguous, None,
            ))

    chords: list[tuple[int, str]] = []
    for span in spans:
        if span.root_pc is None:
            continue
        pair = (span.root_pc, span.quality)
        if not chords or chords[-1] != pair:
            chords.append(pair)

    return ChordSegmentation(
        tonic_pc=tonic_pc, mode=mode, key_inferred=inferred, key_margin=margin,
        spans=spans, chords=chords,
    )


__all__ = ["ChordSpan", "ChordSegmentation", "segment_to_chords"]
