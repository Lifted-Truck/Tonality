"""Piano-roll overlay descriptor (Phase 5 slice 2 — A6's player view).

A piano roll plots notes over time (x = time, y = pitch); the *overlay* is the
analytical annotation drawn on top. This descriptor emits all three layers a
renderer needs, on one shared time axis:

- **notes** — the literal rectangles: every event's pitch/voice/velocity with
  onset and duration in **both** beats and seconds (the renderer picks its
  axis; we never make it re-derive the tempo map);
- **chord_regions** — the segmented-harmony overlay bands: each stable-PC-set
  span with its identity and the contextually-chosen chord name, conditioned
  on the **local** key region per onset (gap 13) so the overlay label agrees
  byte-for-byte with the dataset's naming — they come from the same builder;
- **key_bands** — the local-key backdrop (from `track_keys`): tonic, mode,
  span, and confidence margin, when key regions are supplied.

Specification level: register **and** time — this reads a `Sequence` (the
richest form) and declares ``spec_level="registered_time"``; there is no
register-less projection of a piano roll (it *is* the registered view). The
descriptor is numeric/structural only — labels, spellings, and colors stay
at the display edge (A6 keeps spelling per the standing contract).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from ..analysis.analytical_context import AnalyticalContext
from ..dataset.builders import dataset_from_sequence
from ..temporal.key_tracking import KeyTrackingResult
from ..temporal.sequence import Sequence


@dataclass(frozen=True)
class NoteRect:
    """One note rectangle on the roll (both time bases; seconds via tempo map)."""

    midi: int
    pc: int
    voice: str | None
    velocity: int | None
    onset_beats: float
    duration_beats: float
    onset_seconds: float
    duration_seconds: float

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class ChordRegionOverlay:
    """A stable-harmony span as an overlay band, with its chosen chord name.

    ``root_pc`` / ``quality`` are ``None`` when the set matches no catalog
    chord. ``tonic_pc`` / ``key_name`` / ``margin`` describe the local key the
    naming was conditioned on (``margin`` = the region's confidence, ``None``
    when the context was global/supplied rather than inferred).
    """

    index: int
    start_beats: float
    end_beats: float
    start_seconds: float | None
    end_seconds: float | None
    pcs: list[int]
    mask: int
    root_pc: int | None
    quality: str | None
    functional_role: str | None
    is_ambiguous: bool
    tonic_pc: int | None
    key_name: str | None
    margin: float | None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class KeyBand:
    """A local-key backdrop band (from windowed key tracking)."""

    tonic_pc: int
    mode: str
    start_beats: float
    end_beats: float
    start_seconds: float
    end_seconds: float
    mean_margin: float

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class PianoRollDescriptor:
    """The full piano-roll projection: notes + chord overlays + key bands."""

    spec_level: str  # always "registered_time"
    low_midi: int
    high_midi: int
    duration_beats: float
    duration_seconds: float
    notes: list[NoteRect]
    chord_regions: list[ChordRegionOverlay]
    key_bands: list[KeyBand]

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def _note_rects(sequence: Sequence) -> list[NoteRect]:
    rects: list[NoteRect] = []
    for event in sequence.events:
        onset_seconds = sequence.seconds_at(event.onset)
        rects.append(
            NoteRect(
                midi=event.pitch.midi,
                pc=event.pitch.pc,
                voice=event.voice,
                velocity=event.pitch.velocity,
                onset_beats=event.onset,
                duration_beats=event.duration,
                onset_seconds=onset_seconds,
                duration_seconds=sequence.seconds_at(event.offset) - onset_seconds,
            )
        )
    return rects


def _chord_overlays(
    sequence: Sequence,
    analytical_context: AnalyticalContext | None,
    key_regions: KeyTrackingResult | None,
) -> list[ChordRegionOverlay]:
    # Reuse the dataset builder so overlay names == dataset names exactly
    # (and inherit gap-13 per-region context selection for free).
    dataset = dataset_from_sequence(
        sequence, analytical_context=analytical_context, key_regions=key_regions
    )
    overlays: list[ChordRegionOverlay] = []
    for record in dataset.records:
        placement = record.placement
        naming = record.analysis.naming
        chosen = naming.chosen if naming is not None else None
        context = record.analytical_context
        overlays.append(
            ChordRegionOverlay(
                index=record.index if record.index is not None else len(overlays),
                start_beats=placement.onset_beats,
                end_beats=placement.onset_beats + placement.duration_beats,
                start_seconds=placement.onset_seconds,
                end_seconds=(
                    None
                    if placement.onset_seconds is None or placement.duration_seconds is None
                    else placement.onset_seconds + placement.duration_seconds
                ),
                pcs=list(record.identity.pcs),
                mask=record.identity.mask,
                root_pc=chosen.interpretation.root_pc if chosen is not None else None,
                quality=chosen.interpretation.quality if chosen is not None else None,
                functional_role=chosen.functional_role if chosen is not None else None,
                is_ambiguous=naming.is_ambiguous if naming is not None else False,
                tonic_pc=context.tonic_pc if context is not None else None,
                key_name=context.key_name if context is not None else None,
                margin=context.margin if context is not None else None,
            )
        )
    return overlays


def piano_roll_descriptor(
    sequence: Sequence,
    *,
    analytical_context: AnalyticalContext | None = None,
    key_regions: KeyTrackingResult | None = None,
    chord_overlays: bool = True,
) -> PianoRollDescriptor:
    """Project a :class:`Sequence` into a render-ready piano-roll descriptor.

    ``chord_overlays`` toggles the segmented-harmony bands (naming conditioned
    on ``key_regions`` per onset when given, else ``analytical_context``).
    ``key_regions`` (from ``track_keys``) additionally supplies the key-band
    backdrop. Raises ``ValueError`` on an empty sequence — a piano roll of
    nothing is not a claim worth making.
    """

    if not sequence.events:
        raise ValueError("piano_roll_descriptor needs a sequence with events.")

    notes = _note_rects(sequence)
    midis = [n.midi for n in notes]
    overlays = (
        _chord_overlays(sequence, analytical_context, key_regions)
        if chord_overlays
        else []
    )
    bands = (
        [
            KeyBand(
                tonic_pc=region.tonic_pc,
                mode=region.mode,
                start_beats=region.start_beats,
                end_beats=region.end_beats,
                start_seconds=region.start_seconds,
                end_seconds=region.end_seconds,
                mean_margin=region.mean_margin,
            )
            for region in key_regions.regions
        ]
        if key_regions is not None
        else []
    )

    duration_beats = sequence.duration_beats
    return PianoRollDescriptor(
        spec_level="registered_time",
        low_midi=min(midis),
        high_midi=max(midis),
        duration_beats=duration_beats,
        duration_seconds=sequence.seconds_at(duration_beats),
        notes=notes,
        chord_regions=overlays,
        key_bands=bands,
    )


__all__ = [
    "ChordRegionOverlay",
    "KeyBand",
    "NoteRect",
    "PianoRollDescriptor",
    "piano_roll_descriptor",
]
