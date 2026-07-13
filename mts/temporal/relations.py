"""Pairwise part-relation atoms (gap E slice 2): how two labeled parts *relate*.

Slice 1 (:mod:`mts.temporal.parts`) profiled each part alone. This slice relates
them *pairwise* — the step where "the relationship between the bass and the kick"
becomes an engine result. Same doctrine: **facts, never a verdict.** The engine
reports ``onset_synchrony 0.95, chord_tone_support 0.88, motion_mix {parallel:
6}`` — the caller concludes "the bass doubles the kick and outlines the harmony".
No ``doubles`` / ``call-response`` label is emitted.

Every unordered pair of parts (voice labels, sorted; unvoiced ``None`` last, as
in slice 1) gets a :class:`PartRelation` across two axes:

**Rhythmic** — an exact three-way partition of the pair's *combined distinct
onsets* (``synchrony + interlock + overlap == 1``):

- ``onset_synchrony`` — both parts onset at the same moment (unison attacks);
- ``interlock`` — one part onsets into the *other's rest* (hocket / call-and-
  response — the drum fill between kicks);
- ``overlap`` — one part onsets while the other is still *sounding* (a melody
  moving over a held pad).

plus ``groove_congruence`` (Jaccard of the two parts' beat-phase buckets — do
they hit the same subdivisions of the beat, even at different bars?) and
``density_ratio`` (onsets of ``b`` per onset of ``a``).

**Pitch / harmony** —

- ``register_gap_mean`` — mean signed pitch gap (``b`` mean − ``a`` mean) over
  moments both parts sound; ``register_crossing_rate`` — fraction of those
  moments the gap flips against its prevailing sign (voice crossing);
- ``chord_tone_support_a_vs_b`` / ``_b_vs_a`` — directional: of one part's
  onset pitches, the fraction that are chord tones of the *other* part's
  simultaneously-sounding pitch-class content ("does the topline stay
  chord-tone over the pad?"). Reuses no NHT typing — a plain pc-membership
  rate, harmony-relative and never guessed;
- ``motion_mix`` — the parallel/similar/contrary/oblique tally between the two
  parts (reuses :func:`voice_motion`; a part with no single sounding pitch at a
  moment makes no motion claim there, so chordal pairs report a sparse or empty
  mix — an honest refusal, not a zero).

A claim that cannot be made is ``None`` (no co-sounding moment → no register
gap; a pair touching an unvoiced part → empty ``motion_mix``), never a
fabricated zero. Fewer than two parts raises.

Slice 3 (recorded) is the ``texture`` rule family over these atoms; induction
inherits it free (Decision 8 corollary).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from .sequence import Sequence
from .voice_motion import voice_motion

_EPS = 1e-6
_MOTIONS = ("parallel", "similar", "contrary", "oblique")


@dataclass(frozen=True)
class PartRelation:
    """Relational facts between one unordered pair of parts ``(voice_a, voice_b)``."""

    voice_a: str | None
    voice_b: str | None
    # rhythmic — synchrony + interlock + overlap == 1 (exact partition)
    combined_onsets: int
    onset_synchrony: float
    interlock: float
    overlap: float
    groove_congruence: float
    n_onsets_a: int
    n_onsets_b: int
    density_ratio: float
    # pitch — over moments both parts sound (None when there are none)
    co_sounding_moments: int
    register_gap_mean: float | None
    register_crossing_rate: float | None
    # harmony — directional chord-tone membership (None when the ref never sounds)
    chord_tone_support_a_vs_b: float | None
    chord_tone_support_b_vs_a: float | None
    # motion — parallel/similar/contrary/oblique tally (empty if a part is unvoiced)
    motion_mix: dict
    motion_transitions: int

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class PartRelationsResult:
    """Every part pair's relation, in sorted (voice_a, voice_b) order."""

    relations: list[PartRelation]

    def to_dict(self) -> dict:
        return {"relations": [r.to_dict() for r in self.relations]}


def _onset_set(events) -> set[float]:
    """Distinct onset moments of *events*, bucketed to the pair tolerance."""

    # onset-sorted, so a new distinct moment need only be compared to the most
    # recent kept onset — a linear pass, not an O(n^2) scan over all prior
    # onsets (#206, same pattern as parts._profile).
    onsets: list[float] = []
    for e in sorted(events, key=lambda e: e.onset):
        if not onsets or abs(e.onset - onsets[-1]) > _EPS:
            onsets.append(e.onset)
    return set(onsets)


def _phase_buckets(events) -> set[int]:
    """Beat-phase (onset mod 1 beat) of each onset, bucketed onto a 48-EDO grid.

    Same-groove parts share subdivisions of the beat even when they never attack
    together; 48 ticks/beat resolves triplets and sixteenths without float noise.
    """

    return {round((e.onset % 1.0) * 48) % 48 for e in events}


_SOUND_EPS = 1e-9  # matches Event.sounds_at: onset - eps <= beat < offset


def _sounding_by_beat(events, beats):
    """For each beat in *beats* (any order), the events of *events* sounding at
    it — computed in ONE onset-sorted sweep with an offset-min-heap, instead of
    an O(events) scan per beat (#214). Aligned to *beats* positionally. Set-
    identical to ``[e for e in events if e.sounds_at(beat)]``; order is
    unspecified (every consumer here reduces order-free: sum / set / bool)."""
    import heapq

    ordered_events = sorted(events, key=lambda e: e.onset)
    order = sorted(range(len(beats)), key=beats.__getitem__)
    result: list[tuple] = [()] * len(beats)
    heap: list[tuple] = []  # (offset, tiebreak, event) — offset-min-heap of live notes
    i = 0
    for idx in order:
        beat = beats[idx]
        while i < len(ordered_events) and ordered_events[i].onset - _SOUND_EPS <= beat:
            heapq.heappush(heap, (ordered_events[i].offset, i, ordered_events[i]))
            i += 1
        while heap and heap[0][0] <= beat:  # offset <= beat → no longer sounding
            heapq.heappop(heap)
        result[idx] = tuple(event for _, _, event in heap)
    return result


def _relation(a, b, events_a, events_b, motion_index) -> PartRelation:
    onsets_a = _onset_set(events_a)
    onsets_b = _onset_set(events_b)
    union = onsets_a | onsets_b
    shared = onsets_a & onsets_b

    # One sweep per part over the union onsets feeds BOTH the rhythmic partition
    # and the register gaps (was two _sounds_at scans per onset — #214).
    union_sorted = sorted(union)
    sound_a = _sounding_by_beat(events_a, union_sorted)
    sound_b = _sounding_by_beat(events_b, union_sorted)

    # rhythmic partition: each distinct onset moment is synchronous (both onset),
    # interlock (one onsets, the other silent), or overlap (one onsets, the other
    # sounding). The three counts sum to |union| exactly.
    interlock = 0
    gaps: list[float] = []
    for t, sa, sb in zip(union_sorted, sound_a, sound_b):
        a_on, b_on = t in onsets_a, t in onsets_b
        if a_on != b_on:  # exactly one part onsets here
            other_sounding = sb if a_on else sa
            if not other_sounding:  # onset into the other's rest
                interlock += 1
        if sa and sb:  # both sounding → a register gap sample
            gaps.append(
                sum(e.pitch.midi for e in sb) / len(sb)
                - sum(e.pitch.midi for e in sa) / len(sa)
            )
    n = len(union)
    synchrony = round(len(shared) / n, 9)
    interlock_rate = round(interlock / n, 9)
    overlap_rate = round((n - len(shared) - interlock) / n, 9)

    pa, pb = _phase_buckets(events_a), _phase_buckets(events_b)
    congruence = round(len(pa & pb) / len(pa | pb), 9) if (pa | pb) else 0.0
    density_ratio = round(len(onsets_b) / len(onsets_a), 9)

    if gaps:
        gap_mean = sum(gaps) / len(gaps)
        prevailing = 1 if gap_mean >= 0 else -1
        crossings = sum(1 for g in gaps if g != 0 and (1 if g > 0 else -1) != prevailing)
        register_gap_mean: float | None = round(gap_mean, 9) + 0.0
        register_crossing_rate: float | None = round(crossings / len(gaps), 9)
    else:
        register_gap_mean = register_crossing_rate = None

    support_ab = _chord_tone_support(events_a, events_b)
    support_ba = _chord_tone_support(events_b, events_a)

    mix = {m: 0 for m in _MOTIONS}
    for tr in motion_index.get(frozenset({a, b}), ()):
        mix[tr.motion] += 1
    mix = {m: c for m, c in mix.items() if c}

    return PartRelation(
        voice_a=a,
        voice_b=b,
        combined_onsets=n,
        onset_synchrony=synchrony,
        interlock=interlock_rate,
        overlap=overlap_rate,
        groove_congruence=congruence,
        n_onsets_a=len(onsets_a),
        n_onsets_b=len(onsets_b),
        density_ratio=density_ratio,
        co_sounding_moments=len(gaps),
        register_gap_mean=register_gap_mean,
        register_crossing_rate=register_crossing_rate,
        chord_tone_support_a_vs_b=support_ab,
        chord_tone_support_b_vs_a=support_ba,
        motion_mix=mix,
        motion_transitions=sum(mix.values()),
    )


def _chord_tone_support(melody_events, harmony_events) -> float | None:
    """Fraction of *melody* onset pitches that are chord tones of *harmony*'s
    simultaneously-sounding pitch classes. ``None`` if the harmony part never
    sounds at any melody onset (no claim to make)."""

    melody = list(melody_events)
    harmony_by_onset = _sounding_by_beat(harmony_events, [e.onset for e in melody])
    tested = supported = 0
    for e, sounding in zip(melody, harmony_by_onset):
        if not sounding:
            continue
        tested += 1
        pcs = {h.pitch.pc for h in sounding}
        if e.pitch.pc in pcs:
            supported += 1
    return round(supported / tested, 9) if tested else None


def part_relations(sequence: Sequence) -> PartRelationsResult:
    """Pairwise relation atoms for every part pair in *sequence*.

    Parts are the sequence's voice labels (unvoiced events form the ``None``
    part, sorted last — as in :func:`part_profiles`). Raises on fewer than two
    parts: a relation needs a pair, and the engine never invents one.
    """

    by_voice: dict = {}
    for event in sequence.events:
        by_voice.setdefault(event.voice, []).append(event)
    if len(by_voice) < 2:
        raise ValueError(
            "part_relations needs at least two parts (distinct Event.voice values)."
        )

    # one voice_motion pass, indexed by unordered voice pair (labeled parts only;
    # a pair touching the None part simply finds nothing here → empty motion_mix).
    motion_index: dict = {}
    if sum(1 for v in by_voice if v is not None) >= 2:
        for tr in voice_motion(sequence).transitions:
            motion_index.setdefault(frozenset({tr.voice_a, tr.voice_b}), []).append(tr)

    order = sorted(by_voice, key=lambda v: (v is None, v))
    relations = [
        _relation(a, b, by_voice[a], by_voice[b], motion_index)
        for i, a in enumerate(order)
        for b in order[i + 1:]
    ]
    return PartRelationsResult(relations=relations)


__all__ = ["PartRelation", "PartRelationsResult", "part_relations"]
