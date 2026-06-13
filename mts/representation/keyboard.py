"""Keyboard / piano diagram descriptor (Phase 5 slice 1 — A6's first feed).

Describes a span of piano keys with scale-membership and activation data —
the render-agnostic form of Audiology's keyboard coloring (and any other
keyboard renderer): per key, its pitch identity, standard keyboard topology
(black/white), where it sits in a tonal context, and whether it is active.

Specification levels, made explicit (the lattice, applied to a view):

- **Scale membership** (``in_scale`` / ``degree_index`` / ``is_tonic``) is
  register-less — a key's pc either is in the context's scale or isn't.
  Without a context these fields are ``None`` (no context, no claim).
- **Exact activation** (``active="exact"``) requires register: real MIDI
  notes light exactly their keys.
- **Pitch-class activation** (``active="pc"``) is the octave-invariant
  projection: every key of that pc lights, *by declaration* — the
  descriptor's ``spec_level`` says which projection was used, so a renderer
  can show the difference instead of guessing. Supplying both activation
  forms is a caller error (they answer different questions).

The descriptor is numeric/structural only. Labels, note spellings, and
colors are the renderer's (display-edge) business.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from collections.abc import Iterable

from ..core.bitmask import validate_pc
from ..core.scale import Scale

_BLACK_PCS = frozenset({1, 3, 6, 8, 10})


@dataclass(frozen=True)
class KeyboardKey:
    """One key on the described span."""

    midi: int
    pc: int
    octave: int  # MIDI convention: octave = midi // 12 - 1 (60 -> 4)
    is_black: bool
    in_scale: bool | None  # None = no context supplied (no claim)
    degree_index: int | None  # 0-based index into the scale's degrees
    is_tonic: bool | None
    active: str | None  # "exact" | "pc" | None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class KeyboardDescriptor:
    """A described keyboard span, with the consumed spec level declared."""

    low_midi: int
    high_midi: int
    spec_level: str  # "registered" | "pc_projection" | "identity_only"
    tonic_pc: int | None
    scale_name: str | None
    scale_degrees: list[int] | None
    keys: list[KeyboardKey]

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def keyboard_descriptor(
    low_midi: int,
    high_midi: int,
    *,
    tonic_pc: int | None = None,
    scale: Scale | None = None,
    active_midi: Iterable[int] | None = None,
    active_pcs: Iterable[int] | None = None,
) -> KeyboardDescriptor:
    """Describe the keys in ``[low_midi, high_midi]`` (inclusive).

    ``tonic_pc`` + ``scale`` form the tonal context (a scale needs a tonic
    to land on actual keys — supplying one without the other is an error,
    same rule as ``AnalyticalContext``). ``active_midi`` lights exact keys
    (register); ``active_pcs`` lights every key of those pcs (the declared
    octave-invariant projection); supplying both is an error.
    """

    if not 0 <= low_midi <= high_midi <= 127:
        raise ValueError(
            f"Key range must satisfy 0 <= low <= high <= 127, got [{low_midi}, {high_midi}]."
        )
    if (scale is None) != (tonic_pc is None):
        raise ValueError(
            "A tonal context needs both tonic_pc and scale (a scale only lands "
            "on keys once it has a tonic); supply both or neither."
        )
    if active_midi is not None and active_pcs is not None:
        raise ValueError(
            "Supply active_midi (exact keys, register) OR active_pcs (every "
            "octave, declared projection) — not both; they answer different questions."
        )

    if tonic_pc is not None:
        validate_pc(tonic_pc)
    exact: set[int] = set()
    if active_midi is not None:
        exact = {int(m) for m in active_midi}
        for m in exact:
            if not 0 <= m <= 127:
                raise ValueError(f"active_midi note out of range: {m}")
    pc_lit: set[int] = set()
    if active_pcs is not None:
        pc_lit = {int(pc) % 12 for pc in active_pcs}

    scale_pcs: dict[int, int] = {}  # absolute pc -> degree index
    if scale is not None and tonic_pc is not None:
        for index, degree in enumerate(scale.degrees):
            scale_pcs[(tonic_pc + degree) % 12] = index

    if active_midi is not None:
        spec_level = "registered"
    elif active_pcs is not None:
        spec_level = "pc_projection"
    else:
        spec_level = "identity_only"

    keys: list[KeyboardKey] = []
    for midi in range(low_midi, high_midi + 1):
        pc = midi % 12
        if scale is None:
            in_scale = degree_index = is_tonic = None
        else:
            in_scale = pc in scale_pcs
            degree_index = scale_pcs.get(pc)
            is_tonic = pc == tonic_pc
        if midi in exact:
            active: str | None = "exact"
        elif pc in pc_lit:
            active = "pc"
        else:
            active = None
        keys.append(
            KeyboardKey(
                midi=midi,
                pc=pc,
                octave=midi // 12 - 1,
                is_black=pc in _BLACK_PCS,
                in_scale=in_scale,
                degree_index=degree_index,
                is_tonic=is_tonic,
                active=active,
            )
        )

    return KeyboardDescriptor(
        low_midi=low_midi,
        high_midi=high_midi,
        spec_level=spec_level,
        tonic_pc=tonic_pc,
        scale_name=scale.name if scale is not None else None,
        scale_degrees=list(scale.degrees) if scale is not None else None,
        keys=keys,
    )


__all__ = ["KeyboardDescriptor", "KeyboardKey", "keyboard_descriptor"]
