"""Voice-pair motion classification: the "which voice moved" primitive.

Phase 4.6 Workstream 0 (voice identity), first consumer. Counterpoint rules
are predicates over *how voice pairs move*; this module extracts those moves
from a voiced :class:`Sequence` and classifies each pair transition as
``parallel`` / ``similar`` / ``contrary`` / ``oblique``, with the intervals
as evidence. The rules themselves (e.g. "no parallel fifths") are **not**
baked in here — they are one-line filters over these transitions and belong
to the Phase 4.6 ruleset DSL. This layer only reports what moved, where,
and how.

Classification (register-level — direction needs octaves, so this reads
actual MIDI pitches):

- both voices stand still → no transition is emitted (nothing moved);
- exactly one moves → ``oblique``;
- opposite directions → ``contrary``;
- same direction, harmonic interval class preserved (mod 12 — compound
  intervals count, so P5 → P12 is still parallel) → ``parallel``;
- same direction otherwise → ``similar``.

Moments are the distinct event onsets. At each moment a voice's position is
its single sounding pitch (held notes keep sounding — that is what makes
oblique motion visible). A voice sounding more than one pitch at a moment
has no single position; it makes no claim there (honest skip, recorded in
the transition's absence), and unvoiced events (``voice=None``) are outside
this analysis entirely.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from itertools import combinations

from .sequence import Sequence

_EPS = 1e-9


@dataclass(frozen=True)
class VoicePairMotion:
    """One voice pair's move between two adjacent moments, with evidence.

    Intervals are signed semitones ``pitch_b - pitch_a``; the ``*_class``
    fields reduce them mod 12 (what "parallel fifths" filters match on).
    """

    from_beat: float
    to_beat: float
    voice_a: str
    voice_b: str
    a_from_midi: int
    a_to_midi: int
    b_from_midi: int
    b_to_midi: int
    motion: str  # parallel | similar | contrary | oblique
    interval_from: int
    interval_to: int
    interval_class_from: int
    interval_class_to: int

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class VoiceMotionResult:
    """All classified voice-pair transitions of a sequence."""

    transitions: list[VoicePairMotion]
    voices: list[str]

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def _classify(a_from: int, a_to: int, b_from: int, b_to: int) -> str | None:
    da = a_to - a_from
    db = b_to - b_from
    if da == 0 and db == 0:
        return None  # nothing moved
    if da == 0 or db == 0:
        return "oblique"
    if (da > 0) != (db > 0):
        return "contrary"
    if (b_to - a_to) % 12 == (b_from - a_from) % 12:
        return "parallel"
    return "similar"


def _positions(sequence: Sequence, beat: float) -> dict[str, int]:
    """Each voice's single sounding MIDI pitch at *beat* (ambiguous → absent)."""

    pitches: dict[str, set[int]] = {}
    for event in sequence.events:
        if event.voice is not None and event.sounds_at(beat):
            pitches.setdefault(event.voice, set()).add(event.pitch.midi)
    return {voice: next(iter(p)) for voice, p in pitches.items() if len(p) == 1}


def voice_motion(sequence: Sequence) -> VoiceMotionResult:
    """Classify every voice-pair transition between adjacent onset moments.

    Raises ``ValueError`` if the sequence carries fewer than two voices —
    pair motion needs pairs (unvoiced events don't count; the engine does
    not invent voice assignments).
    """

    voices = sequence.voices()
    if len(voices) < 2:
        raise ValueError(
            "voice_motion needs at least two voiced parts "
            "(set Event.voice; unvoiced events make no motion claims)."
        )

    moments = sorted({e.onset for e in sequence.events if e.voice is not None})
    transitions: list[VoicePairMotion] = []
    for from_beat, to_beat in zip(moments, moments[1:]):
        before = _positions(sequence, from_beat)
        after = _positions(sequence, to_beat)
        for voice_a, voice_b in combinations(voices, 2):
            if not {voice_a, voice_b} <= before.keys() & after.keys():
                continue
            motion = _classify(
                before[voice_a], after[voice_a], before[voice_b], after[voice_b]
            )
            if motion is None:
                continue
            interval_from = before[voice_b] - before[voice_a]
            interval_to = after[voice_b] - after[voice_a]
            transitions.append(
                VoicePairMotion(
                    from_beat=from_beat,
                    to_beat=to_beat,
                    voice_a=voice_a,
                    voice_b=voice_b,
                    a_from_midi=before[voice_a],
                    a_to_midi=after[voice_a],
                    b_from_midi=before[voice_b],
                    b_to_midi=after[voice_b],
                    motion=motion,
                    interval_from=interval_from,
                    interval_to=interval_to,
                    interval_class_from=interval_from % 12,
                    interval_class_to=interval_to % 12,
                )
            )
    return VoiceMotionResult(transitions=transitions, voices=list(voices))


__all__ = ["VoiceMotionResult", "VoicePairMotion", "voice_motion"]
