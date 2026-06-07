"""MIDI ingestion: Standard MIDI Files → temporal ``Event`` / ``Sequence``.

A **thin adapter** over the `mido` library (Phase 2 Slice 3 decision: Mido). The
rest of the engine depends only on ``mts.temporal`` types — never on mido — so the
parser stays swappable. Responsibilities here:

- convert MIDI ticks to quarter-note beats (``tick / ticks_per_beat``),
- pair ``note_on`` / ``note_off`` (and ``note_on`` velocity-0) into ``Event``s,
- read ``set_tempo`` / ``time_signature`` meta into a ``TempoMap`` / ``MeterMap``.

Live/streaming MIDI is out of scope; this handles files.
"""

from __future__ import annotations

from typing import Iterable

import mido

from ..core.pitch import Pitch
from ..temporal import (
    Event,
    MeterChange,
    MeterMap,
    Sequence,
    TempoChange,
    TempoMap,
    TimeSignature,
)

_EPS = 1e-9
_DEFAULT_BPM = 120.0


def sequence_from_midi_file(path: str) -> Sequence:
    """Parse a Standard MIDI File into a temporal :class:`Sequence`."""

    return _sequence_from_mido(mido.MidiFile(path))


def events_from_midi_file(path: str) -> list[Event]:
    """Parse a Standard MIDI File into a flat list of :class:`Event`."""

    return list(sequence_from_midi_file(path).events)


def events_from_live_midi(source: object) -> Iterable[Event]:
    """Live MIDI input — not implemented (streaming is out of scope for now)."""

    raise NotImplementedError(
        "Live MIDI ingestion is not implemented. Parse a file with "
        "sequence_from_midi_file / events_from_midi_file instead."
    )


def _sequence_from_mido(midi: "mido.MidiFile") -> Sequence:
    ticks_per_beat = midi.ticks_per_beat or 480
    events: list[Event] = []
    tempo_changes: list[tuple[float, float]] = []
    time_signatures: list[tuple[float, int, int]] = []
    open_notes: dict[tuple[int, int], tuple[float, int]] = {}

    abs_tick = 0
    for msg in mido.merge_tracks(midi.tracks):
        abs_tick += msg.time
        beat = abs_tick / ticks_per_beat

        if msg.type == "note_on" and msg.velocity > 0:
            open_notes[(msg.channel, msg.note)] = (beat, msg.velocity)
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            started = open_notes.pop((msg.channel, msg.note), None)
            if started is not None:
                onset, velocity = started
                duration = beat - onset
                if duration > _EPS:
                    events.append(
                        Event(
                            onset=onset,
                            duration=duration,
                            pitch=Pitch.from_midi(
                                msg.note, velocity=velocity, channel=msg.channel
                            ),
                        )
                    )
        elif msg.type == "set_tempo":
            tempo_changes.append((beat, mido.tempo2bpm(msg.tempo)))
        elif msg.type == "time_signature":
            time_signatures.append((beat, msg.numerator, msg.denominator))

    return Sequence.from_events(
        events,
        tempo=_build_tempo_map(tempo_changes),
        meter=_build_meter_map(time_signatures),
    )


def _build_tempo_map(changes: list[tuple[float, float]]) -> TempoMap:
    if not changes:
        return TempoMap.constant(_DEFAULT_BPM)
    ordered = sorted(changes, key=lambda c: c[0])
    if ordered[0][0] > _EPS:
        ordered = [(0.0, _DEFAULT_BPM)] + ordered
    # Collapse multiple tempi at the same beat (keep the last one).
    by_beat: dict[float, float] = {}
    for beat, bpm in ordered:
        by_beat[round(beat, 9)] = bpm
    return TempoMap(tuple(TempoChange(beat, by_beat[beat]) for beat in sorted(by_beat)))


def _build_meter_map(changes: list[tuple[float, int, int]]) -> MeterMap:
    if not changes:
        return MeterMap.constant(4, 4)
    ordered = sorted(changes, key=lambda c: c[0])
    if ordered[0][0] > _EPS:
        ordered = [(0.0, 4, 4)] + ordered

    meter_changes: list[MeterChange] = []
    prev_beat = 0.0
    prev_bar = 0
    prev_beats_per_bar: float | None = None
    for beat, numerator, denominator in ordered:
        signature = TimeSignature(numerator, denominator)
        if prev_beats_per_bar is None:
            bar = 0
        else:
            # Convert the change's beat position to a bar index (time-signature
            # changes are assumed to land on bar boundaries, as is conventional).
            bar = prev_bar + int(round((beat - prev_beat) / prev_beats_per_bar))
        meter_changes.append(MeterChange(bar, signature))
        prev_beat, prev_bar, prev_beats_per_bar = beat, bar, signature.beats_per_bar

    # Collapse duplicate bar indices (keep the last signature at that bar).
    by_bar: dict[int, MeterChange] = {}
    for change in meter_changes:
        by_bar[change.bar] = change
    return MeterMap(tuple(by_bar[bar] for bar in sorted(by_bar)))


__all__ = [
    "sequence_from_midi_file",
    "events_from_midi_file",
    "events_from_live_midi",
]
