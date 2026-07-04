"""Groove extract / apply: a GrooveTemplate as a portable timing+accent feel (gap 10).

Ableton Live's *Extract Groove* / Groove Pool is the reference model. This is
one feature with halves on **opposite sides of the cardinal rule** (you can
always *reduce* a realization to an identity; *inventing* timing is generative):

- :func:`extract_groove` is **analysis** — it reduces a played loop to a
  ``GrooveTemplate``: per grid slot at a chosen base resolution, the signed
  onset offset (as a fraction of the grid unit) and the velocity accent. Like
  :func:`~mts.temporal.rhythmic.analyze_swing` (its one-parameter special case),
  it is honest about quantized input: a loop whose onsets all sit on the grid
  extracts to a **null groove** (every offset 0.0), because the feel must be in
  the onsets to be measured.
- :func:`apply_groove` is **generative** — A2's first concrete transformation.
  It builds a *new* ``Sequence`` by nudging onsets and velocities toward a
  template. Its six parameters map 1:1 onto Live's Groove Pool — Base /
  Quantize / Timing / Random / Velocity / Amount — so grooves round-trip
  conceptually with DAW workflows.

Both live here, in ``temporal/``, because ``apply_groove`` builds a ``Sequence``
and ``analysis/`` must never import the temporal layer upward (the layering
rule). ``apply_groove`` needs only onsets and velocities — never register
inference — so it does not trip the ``require_realization`` guard.

**Geometry vs. priors.** Base resolution and loop length are *caller geometry*
(cited in the result, like :func:`~mts.temporal.tolerance.coalesce`'s window),
**not** versioned empirical priors: extraction is pure arithmetic with no
recalibratable threshold. Null-ness is reported as raw ``max_abs_offset`` /
``max_abs_velocity_delta``; any "is this groove flat?" classification stays with
the caller.

**Base is an absolute beat lattice**, not the felt beat: a groove grid is a
fixed subdivision (1/16 = 0.25 beats), so unlike ``analyze_swing`` this module
does *not* consult :func:`~mts.temporal.rhythmic.beat_unit_of`. The line
*contract* differs too — a groove is read from possibly-polyphonic material
(chord stabs, drum hits share a slot), so extraction does not require a
monophonic line; it takes every onset (optionally filtered to one ``voice``).
"""

from __future__ import annotations

import dataclasses
import hashlib
import math
import struct
from dataclasses import dataclass, replace

from ..core.pitch import Pitch
from .sequence import Event, Sequence

_EPS = 1e-9


def _round_half_up(x: float) -> int:
    """Deterministic half-up rounding (extract and apply must agree exactly)."""

    return int(math.floor(x + 0.5))


@dataclass(frozen=True)
class GrooveSlot:
    """One grid slot's feel: signed onset offset and velocity accent.

    ``offset`` is a signed fraction of the base grid unit (0.0 = on the grid
    line, the null case). ``velocity_delta`` is a signed deviation from the
    loop's mean velocity (MIDI units), so flat dynamics extract to all-zero
    deltas. Both are ``None`` for an **empty** slot — one no onset ever landed
    on (a rest in the groove's rhythm), distinct from an on-grid onset
    (``offset == 0.0``). ``onset_count`` is the evidence.
    """

    index: int
    offset: float | None
    velocity_delta: float | None
    onset_count: int

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class GrooveTemplate:
    """A cyclic timing+accent feel distilled from a loop (gap 10).

    ``slots`` cycles over ``loop_length_beats``; ``base_unit_beats`` is the grid
    unit. ``mean_velocity`` is kept alongside the per-slot ``velocity_delta``\\ s
    so the absolute accent of a slot is ``mean_velocity + delta``.
    ``max_abs_offset`` / ``max_abs_velocity_delta`` make null-ness directly
    observable (both ~0 ⇒ :meth:`is_null`).
    """

    base_unit_beats: float
    n_slots: int
    loop_length_beats: float
    slots: tuple[GrooveSlot, ...]
    mean_velocity: float | None
    max_abs_offset: float
    max_abs_velocity_delta: float
    filled_slots: int
    source_voice: str | None

    def to_dict(self) -> dict:
        """Plain-dict (fully JSON; holds no Sequence)."""

        d = dataclasses.asdict(self)
        d["is_null"] = self.is_null()
        return d

    def is_null(self) -> bool:
        """True when the loop carried no measurable timing or accent feel."""

        return self.max_abs_offset <= _EPS and self.max_abs_velocity_delta <= _EPS

    @classmethod
    def from_dict(cls, payload: dict) -> "GrooveTemplate":
        """Reconstruct a template from :meth:`to_dict` output (MCP round-trip)."""

        try:
            slots = tuple(
                GrooveSlot(
                    index=int(s["index"]),
                    offset=None if s["offset"] is None else float(s["offset"]),
                    velocity_delta=(
                        None
                        if s["velocity_delta"] is None
                        else float(s["velocity_delta"])
                    ),
                    onset_count=int(s.get("onset_count", 0)),
                )
                for s in payload["slots"]
            )
            mean_v = payload.get("mean_velocity")
            return cls(
                base_unit_beats=float(payload["base_unit_beats"]),
                n_slots=int(payload["n_slots"]),
                loop_length_beats=float(payload["loop_length_beats"]),
                slots=slots,
                mean_velocity=None if mean_v is None else float(mean_v),
                max_abs_offset=float(payload.get("max_abs_offset", 0.0)),
                max_abs_velocity_delta=float(payload.get("max_abs_velocity_delta", 0.0)),
                filled_slots=int(payload.get("filled_slots", len(slots))),
                source_voice=payload.get("source_voice"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Malformed GrooveTemplate payload: {exc}") from exc


def _groove_events(sequence: Sequence, voice: str | None) -> tuple[Event, ...]:
    """Onsets to read a groove from: one voice if given, else all (polyphony OK)."""

    if voice is not None:
        voices = sequence.voices()
        if voice not in voices:
            raise ValueError(
                f"Voice {voice!r} not present (voices: {list(voices) or 'none'})."
            )
        events = sequence.filter_voice(voice).events
    else:
        events = sequence.events
    if not events:
        raise ValueError("extract_groove needs at least one event.")
    return tuple(sorted(events, key=lambda e: (e.onset, e.pitch.midi)))


def extract_groove(
    sequence: Sequence,
    *,
    base_unit_beats: float,
    loop_length_beats: float | None = None,
    voice: str | None = None,
) -> GrooveTemplate:
    """Distil a :class:`GrooveTemplate` from a loop's onset timing and velocity.

    ``base_unit_beats`` is the grid unit in quarter-note beats (e.g. ``0.25``
    for 1/16). ``loop_length_beats`` defaults to the sequence's duration rounded
    to a whole number of slots — **pass it explicitly** for anything but a loop
    that already fills a clean slot count. Polyphony is fine: simultaneous
    onsets share a slot and average. Raises on degenerate geometry.
    """

    if base_unit_beats <= _EPS:
        raise ValueError("base_unit_beats must be positive.")
    events = _groove_events(sequence, voice)

    if loop_length_beats is None:
        n_slots = max(1, _round_half_up(sequence.duration_beats / base_unit_beats))
        loop_length_beats = n_slots * base_unit_beats
    else:
        if loop_length_beats <= _EPS:
            raise ValueError("loop_length_beats must be positive.")
        ratio = loop_length_beats / base_unit_beats
        n_slots = _round_half_up(ratio)
        if abs(ratio - n_slots) > 1e-6 or n_slots < 1:
            raise ValueError(
                f"loop_length_beats ({loop_length_beats}) must be a positive whole "
                f"multiple of base_unit_beats ({base_unit_beats})."
            )
        loop_length_beats = n_slots * base_unit_beats

    raw_offsets: list[list[float]] = [[] for _ in range(n_slots)]
    velocities: list[list[float]] = [[] for _ in range(n_slots)]
    all_velocities: list[float] = []
    for event in events:
        phase = event.onset % loop_length_beats
        nearest = _round_half_up(phase / base_unit_beats)  # may equal n_slots
        grid_line = nearest * base_unit_beats
        raw_offsets[nearest % n_slots].append(phase - grid_line)
        v = event.pitch.velocity
        if v is not None:
            velocities[nearest % n_slots].append(float(v))
            all_velocities.append(float(v))

    mean_velocity = (
        sum(all_velocities) / len(all_velocities) if all_velocities else None
    )

    slots: list[GrooveSlot] = []
    max_abs_offset = 0.0
    max_abs_velocity_delta = 0.0
    filled = 0
    for i in range(n_slots):
        offs = raw_offsets[i]
        vels = velocities[i]
        if not offs:
            slots.append(GrooveSlot(index=i, offset=None, velocity_delta=None, onset_count=0))
            continue
        filled += 1
        offset = (sum(offs) / len(offs)) / base_unit_beats
        max_abs_offset = max(max_abs_offset, abs(offset))
        if vels and mean_velocity is not None:
            vel_delta: float | None = sum(vels) / len(vels) - mean_velocity
            max_abs_velocity_delta = max(max_abs_velocity_delta, abs(vel_delta))
        else:
            vel_delta = None
        slots.append(
            GrooveSlot(
                index=i,
                offset=offset,
                velocity_delta=vel_delta,
                onset_count=len(offs),
            )
        )

    return GrooveTemplate(
        base_unit_beats=base_unit_beats,
        n_slots=n_slots,
        loop_length_beats=loop_length_beats,
        slots=tuple(slots),
        mean_velocity=mean_velocity,
        max_abs_offset=max_abs_offset,
        max_abs_velocity_delta=max_abs_velocity_delta,
        filled_slots=filled,
        source_voice=voice,
    )


@dataclass(frozen=True)
class GrooveApplyResult:
    """The grooved sequence plus the cited parameters and what changed.

    Mirrors :class:`~mts.temporal.tolerance.CoalesceResult`: ``to_dict()`` omits
    the ``Sequence`` (not JSON); callers re-export its events.
    """

    sequence: Sequence
    base_unit_beats: float
    quantize: float
    timing: float
    random: float
    velocity: float
    amount: float
    seed: int | None
    moved_events: int
    max_onset_shift_beats: float
    voice: str | None = None

    def to_dict(self) -> dict:
        return {
            "base_unit_beats": self.base_unit_beats,
            "quantize": self.quantize,
            "timing": self.timing,
            "random": self.random,
            "velocity": self.velocity,
            "amount": self.amount,
            "seed": self.seed,
            "moved_events": self.moved_events,
            "max_onset_shift_beats": self.max_onset_shift_beats,
            "voice": self.voice,
        }


def _jitter(seed: int, tick: int) -> float:
    """Deterministic per-onset jitter in [-1, 1), a pure function of (seed, tick).

    Uses blake2b over packed ints — never the builtin ``hash`` (per-process
    salted). Keyed on the onset tick, not iteration order, so the result is
    order-independent and byte-reproducible across runs.
    """

    digest = hashlib.blake2b(
        struct.pack(">qq", int(seed), int(tick)), digest_size=8
    ).digest()
    h = int.from_bytes(digest, "big") / 2**64  # [0, 1)
    return 2.0 * h - 1.0


def apply_groove(
    sequence: Sequence,
    template: GrooveTemplate,
    *,
    quantize: float = 1.0,
    timing: float = 1.0,
    random: float = 0.0,
    velocity: float = 1.0,
    amount: float = 1.0,
    seed: int | None = None,
    voice: str | None = None,
) -> GrooveApplyResult:
    """Build a new grooved ``Sequence`` (generative — A2's first transformation).

    Live Groove Pool parameters: ``quantize`` ∈ [0,1] pre-pulls onsets toward
    the Base grid; ``timing`` scales the template's onset offsets (may exceed
    1.0 — Live allows >100%); ``random`` ∈ [0,1] adds deterministic jitter
    (requires ``seed`` when > 0); ``velocity`` is a signed scale on the accent
    contour (negative reverses); ``amount`` ∈ [0,1] is a global multiplier on
    all feel (timing + random + velocity). Onsets shift; **durations are
    preserved** (Live moves note starts). ``voice`` restricts the groove to one
    part: only that voice's events are transformed; every other event passes
    through untouched (the whole sequence is still re-emitted). *(RE-3b: this
    parameter was previously accepted, documented, and completely ignored.)*
    """

    if random > _EPS and seed is None:
        raise ValueError(
            "random > 0 requires an explicit seed (same input + same seed → "
            "same output is an engine invariant)."
        )
    if template.n_slots < 1 or template.base_unit_beats <= _EPS:
        raise ValueError("Degenerate template (n_slots < 1 or base_unit_beats <= 0).")

    base = template.base_unit_beats
    loop_len = template.loop_length_beats
    # A fine integer tick keys the jitter stably to the onset (not to ordering).
    fine = base / 64.0

    new_events: list[Event] = []
    moved = 0
    max_shift = 0.0
    for event in sequence.events:
        if voice is not None and event.voice != voice:
            new_events.append(event)  # other parts pass through untouched
            continue
        t_in = event.onset
        g = _round_half_up(t_in / base) * base
        t_q = t_in + quantize * (g - t_in)

        slot_index = _round_half_up((t_q % loop_len) / base) % template.n_slots
        slot = template.slots[slot_index]

        timing_shift = 0.0 if slot.offset is None else timing * slot.offset * base
        jitter = 0.0
        if random > _EPS:
            jitter = random * base * _jitter(seed, _round_half_up(t_in / fine))
        t_out = max(0.0, t_q + amount * (timing_shift + jitter))

        v_in = event.pitch.velocity
        if slot.velocity_delta is None:
            v_out = v_in  # template silent on velocity → leave the note's own
        else:
            v_base = float(v_in) if v_in is not None else (template.mean_velocity or 0.0)
            v_raw = v_base + amount * velocity * slot.velocity_delta
            v_out = max(0, min(127, _round_half_up(v_raw)))

        shift = abs(t_out - t_in)
        if shift > _EPS or v_out != v_in:
            moved += 1
            max_shift = max(max_shift, shift)
        pitch = event.pitch if v_out == v_in else replace(event.pitch, velocity=v_out)
        new_events.append(replace(event, onset=t_out, pitch=pitch))

    grooved = Sequence(
        events=tuple(sorted(new_events, key=lambda e: (e.onset, e.pitch.midi))),
        tempo=sequence.tempo,
        meter=sequence.meter,
    )
    return GrooveApplyResult(
        sequence=grooved,
        base_unit_beats=base,
        quantize=quantize,
        timing=timing,
        random=random,
        velocity=velocity,
        amount=amount,
        seed=seed,
        moved_events=moved,
        max_onset_shift_beats=max_shift,
        voice=voice,
    )


__all__ = [
    "GrooveSlot",
    "GrooveTemplate",
    "GrooveApplyResult",
    "extract_groove",
    "apply_groove",
]
