"""Events and sequences: the time-bearing layer over the identity model.

An :class:`Event` places a single :class:`~mts.core.pitch.Pitch` at a musical
position (onset + duration, in quarter-note beats). A :class:`Sequence` collects
events with a tempo map and meter, and — crucially — lets you read the pitches
sounding across any time window as a :class:`~mts.core.realization.Realization`,
which reduces to an identity key. This is the core-data-model chain made temporal:
**event → realization → identity key** (ROADMAP Decision 2).

The realization read from a window is rootless (a registered voicing template):
the timeline says *which pitches sound where*, not *which is the root* — naming is
a downstream, register-free act (segmentation in Slice 2 feeds these into
``interpret_chord``).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core.pitch import Pitch
from ..core.realization import Realization
from .meter import MeterMap, MetricPosition
from .tempo import TempoMap

_EPS = 1e-9


@dataclass(frozen=True)
class Event:
    """A single pitched event at a musical position (quarter-note beats).

    ``voice`` is an optional part label (Phase 4.6 Workstream 0: voice
    identity) — "which voice moved" is the prerequisite for counterpoint
    rules. MIDI ingestion seeds it per (track, channel) as ``t{n}c{n}``;
    ``None`` means unvoiced (the engine never invents a voice assignment —
    explicit voice separation of merged material is a recorded refinement).
    """

    onset: float
    duration: float
    pitch: Pitch
    voice: str | None = None

    def __post_init__(self) -> None:
        if self.onset < -_EPS:
            raise ValueError("Event onset must be non-negative.")
        if self.duration <= _EPS:
            raise ValueError("Event duration must be positive.")

    @property
    def offset(self) -> float:
        """The beat at which the event stops sounding (exclusive)."""

        return self.onset + self.duration

    def sounds_at(self, beat: float) -> bool:
        """True if the event is sounding at ``beat`` (half-open [onset, offset)).

        The epsilon is inclusion tolerance at the *owned* (onset) boundary
        only. The old form subtracted it from the offset too, which shifted
        the whole window left: an event "sounded" before its onset while a
        beat strictly inside it (within eps of the offset) reported silent —
        so an event barely longer than eps had a mostly-dead interior
        (RE-3g). A beat exactly at the offset belongs to the successor.
        """

        return self.onset - _EPS <= beat < self.offset


@dataclass(frozen=True)
class Sequence:
    """An ordered set of events with a tempo map and meter. Frozen and hashable."""

    events: tuple[Event, ...]
    tempo: TempoMap
    meter: MeterMap

    @classmethod
    def from_events(
        cls,
        events,
        *,
        tempo: TempoMap | None = None,
        meter: MeterMap | None = None,
        bpm: float = 120.0,
        time_signature: tuple[int, int] = (4, 4),
    ) -> "Sequence":
        """Build a sequence, sorting events and defaulting tempo/meter."""

        ordered = tuple(sorted(events, key=lambda e: (e.onset, e.pitch.midi)))
        return cls(
            events=ordered,
            tempo=tempo if tempo is not None else TempoMap.constant(bpm),
            meter=meter if meter is not None else MeterMap.constant(*time_signature),
        )

    def sounding_at(self, beat: float) -> tuple[Event, ...]:
        """Events sounding at ``beat`` (low pitch first)."""

        active = [e for e in self.events if e.sounds_at(beat)]
        active.sort(key=lambda e: e.pitch.midi)
        return tuple(active)

    def realization_at(self, beat: float) -> Realization | None:
        """The sounding pitches at ``beat`` as a rootless realization.

        Returns ``None`` during silence (no pitches sounding). The result is a
        voicing template (``root_pc=None``) that reduces to an identity key.
        """

        active = self.sounding_at(beat)
        if not active:
            return None
        return Realization(tuple(e.pitch for e in active), root_pc=None)

    def metric_position(self, beat: float) -> MetricPosition:
        """Where ``beat`` falls in the metric grid (bar / beat-in-bar / downbeat)."""

        return self.meter.metric_position(beat)

    def seconds_at(self, beat: float) -> float:
        """Wall-clock seconds from the start to ``beat`` via the tempo map."""

        return self.tempo.seconds_at(beat)

    def pc_weights(
        self, start: float | None = None, end: float | None = None
    ) -> tuple[float, ...]:
        """Duration-weighted pitch-class content: 12 weights, index = pc.

        The salience input for key induction (``mts.analysis.key_induction.
        infer_key`` accepts a ``Sequence`` directly via this method). Octave
        doublings accumulate — register reduces to pc, per the core model.

        With ``start``/``end`` (beats), only the portion of each event
        overlapping the half-open window ``[start, end)`` contributes — the
        windowed form local key tracking slides over.
        """

        weights = [0.0] * 12
        for event in self.events:
            lo = event.onset if start is None else max(event.onset, start)
            hi = event.offset if end is None else min(event.offset, end)
            if hi - lo > _EPS:
                weights[event.pitch.pc] += hi - lo
        return tuple(weights)

    def pc_weights_windows(
        self, windows: list[tuple[float, float]]
    ) -> list[tuple[float, ...]]:
        """``pc_weights(start, end)`` for many ascending windows in one sweep.

        The windowed key/meter trackers slide overlapping windows and used to
        re-scan every event per window (O(windows x events) — RE-5d). Here the
        onset-sorted events are swept once: an active list gains events as their
        onset enters reach and sheds them once their offset falls before the
        window start (monotone, since window starts only increase). Byte-identical
        to calling ``pc_weights`` per window. ``windows`` must be sorted by start.
        """

        results: list[tuple[float, ...]] = []
        active: list[Event] = []  # events not yet fully behind the window start
        i = 0
        n = len(self.events)
        for start, end in windows:
            while i < n and self.events[i].onset < end - _EPS:
                active.append(self.events[i])
                i += 1
            active = [e for e in active if e.offset > start + _EPS]
            weights = [0.0] * 12
            for event in active:
                lo = max(event.onset, start)
                hi = min(event.offset, end)
                if hi - lo > _EPS:
                    weights[event.pitch.pc] += hi - lo
            results.append(tuple(weights))
        return results

    def voices(self) -> tuple[str, ...]:
        """The distinct voice labels present, sorted (unvoiced events excluded)."""

        return tuple(sorted({e.voice for e in self.events if e.voice is not None}))

    def filter_voice(self, voice: str) -> "Sequence":
        """A sequence of just one voice's events (tempo/meter maps shared)."""

        return Sequence(
            events=tuple(e for e in self.events if e.voice == voice),
            tempo=self.tempo,
            meter=self.meter,
        )

    @property
    def duration_beats(self) -> float:
        """End of the last-sounding event, in beats (0.0 if empty)."""

        return max((e.offset for e in self.events), default=0.0)

    @property
    def duration_seconds(self) -> float:
        """Total wall-clock duration in seconds."""

        return self.seconds_at(self.duration_beats)


__all__ = ["Event", "Sequence"]
