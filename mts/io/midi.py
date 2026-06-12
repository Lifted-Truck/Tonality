"""MIDI I/O: Standard MIDI Files ↔ temporal ``Event`` / ``Sequence``.

A **thin adapter** over the `mido` library (Phase 2 Slice 3 decision: Mido). The
rest of the engine depends only on ``mts.temporal`` types — never on mido — so the
adapter stays swappable. Responsibilities here:

- read: convert ticks to quarter-note beats, pair ``note_on`` / ``note_off``
  (and ``note_on`` velocity-0) into ``Event``s, read ``set_tempo`` /
  ``time_signature`` meta into a ``TempoMap`` / ``MeterMap``;
- write (Phase 2 addendum): the mirror — ``Sequence`` → single-track SMF,
  preserving tempo/meter maps and per-pitch velocity/channel. Round-trip
  (read → write → read) is the tested invariant.

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


_DEFAULT_VELOCITY = 64


def sequence_to_midi_file(
    sequence: Sequence, path: str, *, ticks_per_beat: int = 480
) -> None:
    """Write a :class:`Sequence` to a Standard MIDI File (the read mirror).

    Single track; tempo and meter maps become ``set_tempo`` /
    ``time_signature`` meta events; each event's pitch keeps its velocity and
    channel when present (``64`` / channel ``0`` otherwise). Onsets and
    durations are quantized to ``ticks_per_beat`` — values representable in
    480ths of a beat round-trip exactly; tempo round-trips to within the SMF
    format's integer microseconds-per-beat resolution (~1e-4 bpm).
    """

    midi_file_from_sequence(sequence, ticks_per_beat=ticks_per_beat).save(path)


def midi_file_from_sequence(
    sequence: Sequence, *, ticks_per_beat: int = 480
) -> "mido.MidiFile":
    """Build the in-memory :class:`mido.MidiFile` for a :class:`Sequence`."""

    def ticks(beat: float) -> int:
        return int(round(beat * ticks_per_beat))

    # (tick, sort_rank, message) — rank orders simultaneous messages: meta
    # first, then note_offs (so re-struck notes re-trigger), then note_ons.
    timed: list[tuple[int, int, "mido.Message"]] = []

    for change in sequence.tempo.changes:
        timed.append(
            (
                ticks(change.beat),
                0,
                mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(change.bpm)),
            )
        )

    beat = 0.0
    changes = sequence.meter.changes
    for i, change in enumerate(changes):
        timed.append(
            (
                ticks(beat),
                0,
                mido.MetaMessage(
                    "time_signature",
                    numerator=change.signature.numerator,
                    denominator=change.signature.denominator,
                ),
            )
        )
        if i + 1 < len(changes):
            beat += (changes[i + 1].bar - change.bar) * change.signature.beats_per_bar

    for event in sequence.events:
        velocity = event.pitch.velocity if event.pitch.velocity is not None else _DEFAULT_VELOCITY
        channel = event.pitch.channel if event.pitch.channel is not None else 0
        timed.append(
            (
                ticks(event.onset),
                2,
                mido.Message(
                    "note_on", note=event.pitch.midi, velocity=velocity, channel=channel
                ),
            )
        )
        timed.append(
            (
                ticks(event.offset),
                1,
                mido.Message("note_off", note=event.pitch.midi, velocity=0, channel=channel),
            )
        )

    timed.sort(key=lambda item: (item[0], item[1]))

    midi = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    midi.tracks.append(track)
    previous_tick = 0
    for tick, _, message in timed:
        track.append(message.copy(time=tick - previous_tick))
        previous_tick = tick
    return midi


def _sequence_from_mido(midi: "mido.MidiFile") -> Sequence:
    """Walk tracks individually (not ``merge_tracks``) so track identity
    survives: each (track, channel) pair becomes a voice label ``t{n}c{n}``
    (Phase 4.6 Workstream 0 — voice identity; SMF type 1 keeps one part per
    track by convention, channels split parts within a track). Per-track
    walking also pairs note_on/note_off within their own track — a stray
    note_off in another track can no longer close a note it didn't open.
    Tempo/meter meta is collected from every track.
    """

    ticks_per_beat = midi.ticks_per_beat or 480
    events: list[Event] = []
    tempo_changes: list[tuple[float, float]] = []
    time_signatures: list[tuple[float, int, int]] = []

    for track_index, track in enumerate(midi.tracks):
        open_notes: dict[tuple[int, int], tuple[float, int]] = {}
        abs_tick = 0
        for msg in track:
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
                                voice=f"t{track_index}c{msg.channel}",
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
    "sequence_to_midi_file",
    "midi_file_from_sequence",
]
