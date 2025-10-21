"""MIDI integration scaffolding.

These helpers will eventually translate MIDI files/streams into the timeline
events consumed by `mts.analysis.timeline`.  For now they serve as placeholders
so other modules can prototype APIs without depending on an implementation.

TODO:
    - Parse SMF (Standard MIDI Files) into TimedEvent sequences.
    - Provide live MIDI input hooks for interactive analysis/generation.
    - Support velocity, channel, and control-change metadata propagation.
    - Normalize tempo/meter information for downstream analyses.
    - Offer convenience bridges that feed directly into analyze_timeline.
    - Allow round-tripping generated TimedEvent sequences back to MIDI.
"""

from __future__ import annotations

from typing import Iterable

from ..analysis.timeline import TimedEvent


def events_from_midi_file(path: str) -> list[TimedEvent]:
    """Return TimedEvent objects parsed from a MIDI file (placeholder)."""

    raise NotImplementedError(
        "MIDI ingestion is not yet implemented. "
        "TODO: integrate python-midi/mido or an in-house parser."
    )


def events_from_live_midi(source: object) -> Iterable[TimedEvent]:
    """Yield TimedEvent objects from a live MIDI source (placeholder)."""

    raise NotImplementedError(
        "Live MIDI ingestion is not yet implemented. "
        "TODO: bridge to an async/streaming MIDI backend."
    )
