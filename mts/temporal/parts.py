"""Part content descriptors (gap E slice 1): per-voice facts about *what kind
of content* a labeled part carries.

The first slice of the part-relationship / texture vocabulary (ROADMAP gap E,
from Julian's ask: relate MIDI sections — drums, harmony, topline, bass). Before
parts can be *related*, each part needs a **content profile**: continuous,
descriptive facts exposing how melodic / rhythmic / harmonic its material is.

**Facts, never a verdict** (the plural/evidenced doctrine): the engine reports
``simultaneity 2.9, distinct pitch classes 11, sustain ratio 1.9`` — the caller
judges "that's a harmony part". A hard ``kind: "harmony"`` label would be a
fabricated classification; none is emitted. The descriptors:

- ``onset_density`` — distinct onsets per beat of the part's active span (how
  *busy*);
- ``simultaneity`` — mean sounding notes per onset (1.0 = a pure line; ≫1 =
  chordal — the sharpest melodic-vs-harmonic discriminator);
- ``sustain_ratio`` — total sounding time / active span (percussive ≪ 1;
  legato ≈ 1; overlapping/pedaled > 1 — reported raw, a polyphony-weighted
  coverage, not clamped);
- ``pitch_mobility`` — mean |Δ| between successive *onset-group mean pitches*
  (how much the part's center moves — drums ≈ 0, a topline leaps);
- register band — ``lo/hi/mean`` MIDI — plus ``distinct_pcs`` and
  ``pc_entropy_norm`` (0 = one pitch class, 1 = uniform over those present ≥
  a drum hit vs a wandering line; normalized by log 12).

Slice 2 (recorded) relates profiles pairwise (onset synchrony, interlock,
chord-tone support, register separation); slice 3 is the ``texture`` rule
family over those atoms.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass

from .sequence import Sequence

_ONSET_TOL = 1e-6   # two onsets within this are the same attack moment
_MIN_SPAN = 1e-6    # below this a part has no temporal extent → density undefined


@dataclass(frozen=True)
class PartProfile:
    """Continuous content descriptors for one labeled part (voice)."""

    voice: str | None
    n_events: int
    n_onsets: int              # distinct onset moments
    span_beats: float          # first onset → last offset
    onset_density: float       # n_onsets / span
    simultaneity: float        # mean events per onset (1.0 = pure line)
    sustain_ratio: float       # Σ durations / span (raw; >1 = overlap/pedal)
    pitch_mobility: float      # mean |Δ onset-group mean pitch| (0.0 if 1 onset)
    register_lo: int
    register_hi: int
    register_mean: float
    distinct_pcs: int
    pc_entropy_norm: float     # 0..1, duration-weighted, normalized by log 12

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class PartProfilesResult:
    """Every part's profile, sorted by voice label (unvoiced part last)."""

    profiles: list[PartProfile]

    def to_dict(self) -> dict:
        return {"profiles": [p.to_dict() for p in self.profiles]}


def _profile(voice, events) -> PartProfile:
    events = sorted(events, key=lambda e: (e.onset, e.pitch.midi))
    # Events are onset-sorted, so an attack moment is a run of adjacent events
    # within tolerance of the run's first onset — a single linear pass. (Was an
    # O(n^2) scan over every prior onset group, quadratic at real-corpus scale;
    # #206.)
    onset_groups: list[list] = []
    for e in events:
        if onset_groups and abs(e.onset - onset_groups[-1][0].onset) <= _ONSET_TOL:
            onset_groups[-1].append(e)
        else:
            onset_groups.append([e])
    onset_times = [group[0].onset for group in onset_groups]

    first = events[0].onset
    last = max(e.offset for e in events)
    span = last - first
    if span < _MIN_SPAN:
        # A part collapsed to a single instant has no meaningful onset density
        # (n_onsets / span would blow up unbounded). Error, don't guess — the
        # same honesty as the empty-sequence guard (#207). Not reachable via MIDI
        # ingestion (which drops zero-length notes); a directly-built Sequence can.
        raise ValueError(
            f"part {voice!r} has a degenerate span ({span:g} beats): no temporal "
            "extent, so onset_density is undefined. part_profiles needs a part "
            "that actually spans time."
        )

    group_means = [
        sum(e.pitch.midi for e in group) / len(group) for group in onset_groups
    ]
    mobility = (
        sum(abs(b - a) for a, b in zip(group_means, group_means[1:])) / (len(group_means) - 1)
        if len(group_means) > 1 else 0.0
    )

    midis = [e.pitch.midi for e in events]
    # duration-weighted pc distribution → normalized entropy over the 12 classes
    weights = [0.0] * 12
    for e in events:
        weights[e.pitch.pc] += e.duration
    total = sum(weights)
    entropy = -sum(
        (w / total) * math.log(w / total) for w in weights if w > 0.0
    )
    return PartProfile(
        voice=voice,
        n_events=len(events),
        n_onsets=len(onset_times),
        span_beats=round(last - first, 9),
        onset_density=round(len(onset_times) / span, 9),
        simultaneity=round(len(events) / len(onset_times), 9),
        sustain_ratio=round(sum(e.duration for e in events) / span, 9),
        pitch_mobility=round(mobility, 9),
        register_lo=min(midis),
        register_hi=max(midis),
        register_mean=round(sum(midis) / len(midis), 9),
        distinct_pcs=len({m % 12 for m in midis}),
        pc_entropy_norm=round(entropy / math.log(12), 9) + 0.0,  # +0.0: never -0.0
    )


def part_profiles(sequence: Sequence) -> PartProfilesResult:
    """Content profiles for every labeled part in *sequence*.

    Parts are the sequence's voice labels (MIDI ingestion seeds these per
    track/channel); unvoiced events form their own part (``voice=None``, sorted
    last). Raises on an empty sequence — no material, no profile (never a
    fabricated zero-row).
    """

    if not sequence.events:
        raise ValueError("part_profiles needs a non-empty sequence.")
    by_voice: dict = {}
    for event in sequence.events:
        by_voice.setdefault(event.voice, []).append(event)
    ordered = sorted(by_voice, key=lambda v: (v is None, v))
    return PartProfilesResult(
        profiles=[_profile(v, by_voice[v]) for v in ordered]
    )


__all__ = ["PartProfile", "PartProfilesResult", "part_profiles"]
