"""Bracelet / pitch-class clock descriptor (Phase 5 slice 3 — A6 brief-2).

Describes a pitch-class set on the 12-position clock: the active set joined
into a polygon, an optional scale as a backdrop ring, and the structural
extras a clock diagram is the natural canvas for — **symmetry axes**
(reflection + rotational) and the **interval vector**. Audiology ships this
view client-side from pcs it already holds; the descriptor lets it draw the
symmetry an honest "is this set symmetric" rendering needs, from the engine's
computation rather than its own.

Register-less (identity key): ``spec_level="identity_only"``. A clock has no
register — it *is* the octave-collapsed view. Numeric/structural only;
spelling and color stay at the display edge.

Geometry note: the renderer owns angles (position *n* at *n*·30° is its
convention). Reflection-axis ``center`` is in pc units (0–11.5); a ``pitch``
axis passes through that pc and its tritone, a ``between`` axis through the
gaps either side — the renderer maps pc units to its own angle convention.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from collections.abc import Iterable

from ..analysis.pcset_math import interval_vector, reflection_axes
from ..core.bitmask import mask_from_pcs
from ..core.scale import Scale
from ..core.symmetry import rotational_period


@dataclass(frozen=True)
class BraceletPosition:
    """One of the 12 clock positions."""

    pc: int
    is_active: bool  # in the described set
    in_scale: bool | None  # backdrop-ring membership; None when no scale given


@dataclass(frozen=True)
class BraceletAxis:
    """A reflection axis of the active set, in pc units."""

    type: str  # "pitch" (through a pc + its tritone) | "between" (through gaps)
    center: float


@dataclass(frozen=True)
class BraceletDescriptor:
    """A pc-set clock projection: ring positions + symmetry + interval vector."""

    spec_level: str  # always "identity_only"
    active_pcs: list[int]
    mask: int
    cardinality: int
    positions: list[BraceletPosition]
    interval_vector: list[int]
    reflection_axes: list[BraceletAxis]
    rotational_period: int  # smallest self-mapping rotation; 12 = no symmetry, aug=4, dim7=3
    tonic_pc: int | None
    scale_name: str | None
    scale_degrees: list[int] | None

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def bracelet_descriptor(
    pcs: Iterable[int],
    *,
    tonic_pc: int | None = None,
    scale: Scale | None = None,
) -> BraceletDescriptor:
    """Describe ``pcs`` as a clock diagram. Symmetry and interval vector are of
    the active set; ``tonic_pc`` + ``scale`` (both or neither) add the backdrop
    ring. Raises on an empty set — a bracelet of nothing makes no claim."""

    active = {int(pc) % 12 for pc in pcs}
    if not active:
        raise ValueError("bracelet_descriptor needs at least one pitch class.")
    if (scale is None) != (tonic_pc is None):
        raise ValueError(
            "A backdrop scale needs both tonic_pc and scale; supply both or neither."
        )

    scale_pcs: set[int] = set()
    if scale is not None and tonic_pc is not None:
        scale_pcs = {(tonic_pc + d) % 12 for d in scale.degrees}

    positions = [
        BraceletPosition(
            pc=pc,
            is_active=pc in active,
            in_scale=(pc in scale_pcs) if scale is not None else None,
        )
        for pc in range(12)
    ]
    mask = mask_from_pcs(active)
    return BraceletDescriptor(
        spec_level="identity_only",
        active_pcs=sorted(active),
        mask=mask,
        cardinality=len(active),
        positions=positions,
        interval_vector=interval_vector(active),
        reflection_axes=[
            BraceletAxis(type=axis.type, center=axis.center)
            for axis in reflection_axes(active)
        ],
        rotational_period=rotational_period(mask),
        tonic_pc=tonic_pc,
        scale_name=scale.name if scale is not None else None,
        scale_degrees=list(scale.degrees) if scale is not None else None,
    )


__all__ = ["BraceletAxis", "BraceletDescriptor", "BraceletPosition", "bracelet_descriptor"]
