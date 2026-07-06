"""Typed multi-step pipelines (RE-4b): the engine entry points behind the
``midi_file_analysis`` and ``piano_roll_view`` MCP tools.

These result shapes previously existed only as hand-built dicts in the MCP
layer — intelligence above the line, against Decision 5 and the typed-results
convention, and consequently the only two tools without a conformance golden.
The pipelines now live below the line as typed entry points; the tools are
one-liners, and the goldens follow.

Layering: ``dataset`` already composes analysis + temporal + context;
this module adds ``io.midi`` (file reads) and ``representation`` (the piano
roll descriptor) at the top of that stack — nothing imports back down into
it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..analysis.errors import InsufficientInformation
from ..analysis.key_induction import (
    candidate_context,
    disambiguate_relative_key,
    infer_key,
)
from ..io.midi import MidiReadLoss, read_midi_file
from ..temporal import coalesce, track_keys, track_meter
from .builders import dataset_from_sequence

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..io.loaders import KeyProfileSet


_FLAG_CONFLICT = (
    "key_inertia does not compose with disambiguate_relative_keys for "
    "the windowed tracking: the inertia path re-decodes from raw score "
    "vectors, so the relative-key tie-break cannot reach it. Choose one "
    "(the global-key disambiguation alone is fine — drop key_inertia, "
    "or drop disambiguate_relative_keys)."
)


@dataclass(frozen=True)
class MidiFileAnalysis:
    """The full A1 pipeline result: global key + enriched dataset + evidence.

    ``include_key_regions`` / ``include_meter_regions`` record whether the
    caller asked for those sections — ``to_dict()`` reproduces the tool's
    contract exactly (the key is present-and-null when asked-for-but-absent,
    and omitted entirely when not asked for)."""

    key: object  # KeyInductionResult
    dataset: object  # Dataset
    midi_read_losses: list[MidiReadLoss]
    coalesce: object | None  # CoalesceResult
    key_disambiguation: object | None  # RelativeKeyDisambiguation
    key_regions: object | None  # KeyTrackingResult
    include_key_regions: bool
    meter_regions: object | None  # MeterTrackingResult
    include_meter_regions: bool

    def to_dict(self) -> dict:
        """Exactly the ``midi_file_analysis`` tool's wire shape."""
        result: dict = {
            "key": self.key.to_dict(),
            "dataset": self.dataset.to_dict(),
            # Itemized read losses (RE-3a): always present, usually empty.
            "midi_read_losses": [loss.to_dict() for loss in self.midi_read_losses],
        }
        if self.coalesce is not None:
            result["coalesce"] = self.coalesce.to_dict()
        if self.key_disambiguation is not None:
            result["key_disambiguation"] = self.key_disambiguation.to_dict()
        if self.include_key_regions:
            result["key_regions"] = (
                self.key_regions.to_dict() if self.key_regions is not None else None
            )
        if self.include_meter_regions:
            result["meter_regions"] = (
                self.meter_regions.to_dict() if self.meter_regions is not None else None
            )
        return result


def analyze_midi_file(
    path: str,
    *,
    infer_context: bool = True,
    include_key_regions: bool = True,
    coalesce_window_beats: float | None = None,
    per_region_context: bool = True,
    disambiguate_relative_keys: bool = False,
    smooth_key_regions: bool = False,
    profiles: "KeyProfileSet | None" = None,
    key_inertia: bool = False,
    include_meter_regions: bool = False,
) -> MidiFileAnalysis:
    """Analyze a Standard MIDI File end-to-end (segment → infer key → enrich).

    The typed engine entry point behind the ``midi_file_analysis`` tool; see
    that tool's docstring for the parameter semantics. ``profiles`` is the
    loaded profile *object* (the tool translates its ``profile_version``
    string)."""

    if key_inertia and disambiguate_relative_keys:
        # Loud up front (RE-3c): never absorbed by the honest-absence handling.
        raise ValueError(_FLAG_CONFLICT)

    midi_read = read_midi_file(path)
    sequence = midi_read.sequence
    cleaned = None
    if coalesce_window_beats is not None:
        cleaned = coalesce(sequence, onset_window_beats=float(coalesce_window_beats))
        sequence = cleaned.sequence
    keys = infer_key(sequence, profiles=profiles)
    best = keys.best
    disambiguation = None
    if disambiguate_relative_keys:
        disambiguation = disambiguate_relative_key(keys)
        if disambiguation.applied and not disambiguation.is_ambiguous:
            best = disambiguation.chosen
    context = candidate_context(best) if infer_context else None

    regions = None
    if include_key_regions or (per_region_context and infer_context):
        try:
            regions = track_keys(
                sequence,
                disambiguate_relative=bool(disambiguate_relative_keys),
                smoothing=bool(smooth_key_regions),
                profiles=profiles,
                key_inertia=bool(key_inertia),
            )
        except InsufficientInformation:
            regions = None  # honest absence: no window carried tonal information

    meter_regions = None
    if include_meter_regions:
        try:
            meter_regions = track_meter(sequence)
        except InsufficientInformation:
            meter_regions = None  # honest absence: no window carried metric information

    dataset = dataset_from_sequence(
        sequence,
        analytical_context=context,
        key_regions=regions if (per_region_context and infer_context) else None,
    )
    return MidiFileAnalysis(
        key=keys,
        dataset=dataset,
        midi_read_losses=list(midi_read.losses),
        coalesce=cleaned,
        key_disambiguation=disambiguation,
        key_regions=regions,
        include_key_regions=bool(include_key_regions),
        meter_regions=meter_regions,
        include_meter_regions=bool(include_meter_regions),
    )


@dataclass(frozen=True)
class PianoRollView:
    """The piano-roll descriptor plus the itemized MIDI read losses."""

    descriptor: object  # PianoRollDescriptor
    midi_read_losses: list[MidiReadLoss]

    def to_dict(self) -> dict:
        """Exactly the ``piano_roll_view`` tool's wire shape."""
        result = self.descriptor.to_dict()
        # A rectangle that never appears should be explained, not invisible.
        result["midi_read_losses"] = [loss.to_dict() for loss in self.midi_read_losses]
        return result


def piano_roll_view_from_file(
    path: str,
    *,
    chord_overlays: bool = True,
    track_local_keys: bool = True,
    coalesce_window_beats: float | None = None,
    disambiguate_relative_keys: bool = False,
    smooth_key_regions: bool = False,
) -> PianoRollView:
    """Build the render-ready piano-roll descriptor for a Standard MIDI File.

    The typed engine entry point behind the ``piano_roll_view`` tool; see
    that tool's docstring for the parameter semantics."""

    from ..representation import piano_roll_descriptor

    midi_read = read_midi_file(path)
    sequence = midi_read.sequence
    if coalesce_window_beats is not None:
        sequence = coalesce(
            sequence, onset_window_beats=float(coalesce_window_beats)
        ).sequence

    regions = None
    context = None
    if track_local_keys:
        try:
            regions = track_keys(
                sequence,
                disambiguate_relative=bool(disambiguate_relative_keys),
                smoothing=bool(smooth_key_regions),
            )
        except InsufficientInformation:
            regions = None  # honest absence: no window carried tonal information
    if regions is None and chord_overlays:
        try:
            best = infer_key(sequence)
            chosen = best.best
            if disambiguate_relative_keys:
                rel = disambiguate_relative_key(best)
                if rel.applied and not rel.is_ambiguous:
                    chosen = rel.chosen
            context = candidate_context(chosen)
        except InsufficientInformation:
            context = None  # honest absence — intrinsic naming only

    descriptor = piano_roll_descriptor(
        sequence,
        analytical_context=context,
        key_regions=regions,
        chord_overlays=chord_overlays,
    )
    return PianoRollView(descriptor=descriptor, midi_read_losses=list(midi_read.losses))


__all__ = [
    "MidiFileAnalysis",
    "PianoRollView",
    "analyze_midi_file",
    "piano_roll_view_from_file",
]
