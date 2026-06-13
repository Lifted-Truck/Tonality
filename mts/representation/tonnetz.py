"""Tonnetz descriptor (Phase 5 slice 3 — A6 brief-2).

Describes a pitch-class set on the neo-Riemannian Tonnetz: every pc placed at
its lattice coordinate (the engine's canonical layout — so a renderer's
diagram and the engine's analysis cannot disagree, which is what A6 asked
for), the active subset flagged, and — the genuinely new piece — the
**edges** among active pcs: which pairs are connected by the P5, M3, or m3
axis. Lit edges are what turn a node cloud into the triangles a Tonnetz reads
as triads.

Edges are derived from pitch-class interval, not from coordinate adjacency
(the coordinates are a spanning-tree assignment, so coordinate differences
between arbitrary pcs aren't axis vectors). Two pcs share an edge iff their
interval is the axis interval or its octave-complement: **P5** = 5/7,
**M3** = 4/8, **m3** = 3/9. Each qualifying pair is exactly one edge type.

Register-less (identity key): ``spec_level="identity_only"`` — the Tonnetz is
an octave-collapsed view. Numeric/structural only; the node coordinates are
integer lattice positions (the renderer projects them to its own plane).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from collections.abc import Iterable
from itertools import combinations

from ..analysis.pcset_math import tonnetz_coordinates
from ..core.bitmask import mask_from_pcs

# interval (mod 12) -> axis name; complements map to the same axis
_AXIS_BY_INTERVAL = {7: "P5", 5: "P5", 4: "M3", 8: "M3", 3: "m3", 9: "m3"}


@dataclass(frozen=True)
class TonnetzNode:
    """One pitch class at its lattice coordinate."""

    pc: int
    coordinate: tuple[int, int, int]  # (fifths, major-thirds, minor-thirds) from C
    is_active: bool


@dataclass(frozen=True)
class TonnetzEdge:
    """A lattice edge between two active pcs (lit when both ends are active)."""

    pc_a: int
    pc_b: int
    axis: str  # "P5" | "M3" | "m3"


@dataclass(frozen=True)
class TonnetzDescriptor:
    """A pc-set Tonnetz projection: all 12 nodes + the active-set edges."""

    spec_level: str  # always "identity_only"
    active_pcs: list[int]
    mask: int
    nodes: list[TonnetzNode]
    edges: list[TonnetzEdge]
    centroid: tuple[float, float, float] | None  # mean of active coords

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def tonnetz_descriptor(pcs: Iterable[int]) -> TonnetzDescriptor:
    """Describe ``pcs`` on the Tonnetz: all 12 node coordinates with the active
    subset flagged, the P5/M3/m3 edges among active pcs, and the active
    centroid. Raises on an empty set."""

    active = {int(pc) % 12 for pc in pcs}
    if not active:
        raise ValueError("tonnetz_descriptor needs at least one pitch class.")

    coords = tonnetz_coordinates()
    nodes = [
        TonnetzNode(pc=pc, coordinate=coords[pc], is_active=pc in active)
        for pc in range(12)
    ]

    edges: list[TonnetzEdge] = []
    for a, b in combinations(sorted(active), 2):
        axis = _AXIS_BY_INTERVAL.get((b - a) % 12)
        if axis is not None:
            edges.append(TonnetzEdge(pc_a=a, pc_b=b, axis=axis))

    totals = [0.0, 0.0, 0.0]
    for pc in active:
        for i, value in enumerate(coords[pc]):
            totals[i] += value
    centroid = (totals[0] / len(active), totals[1] / len(active), totals[2] / len(active))

    return TonnetzDescriptor(
        spec_level="identity_only",
        active_pcs=sorted(active),
        mask=mask_from_pcs(active),
        nodes=nodes,
        edges=edges,
        centroid=centroid,
    )


__all__ = ["TonnetzDescriptor", "TonnetzEdge", "TonnetzNode", "tonnetz_descriptor"]
