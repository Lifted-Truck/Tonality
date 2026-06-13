"""Chord-network descriptor: the voice-leading parsimony graph (Phase 5).

Given a chord vocabulary, emit the **voice-leading network** — nodes (each
chord + its symmetry) and undirected edges between chords whose minimal
voice-leading distance is within a threshold. This is the render-agnostic
form of the "Cube Dance"-family chord mandalas (Douthett & Steinbach
parsimonious-voice-leading graphs): the structural backbone where augmented
triads emerge as connective hubs (their high rotational symmetry gives them
many near neighbours).

Every edge is computed, not drawn by hand — it *is* the engine's
`voice_leading.distance` relation, so a renderer's diagram and the engine's
analysis cannot disagree (the Tonnetz-descriptor guarantee, applied to a
chord graph). Each edge carries the distance, shared-tone count, and root
interval so a consumer can threshold, weight, or tag it (these are exactly
the structural inputs the next-chord recommendation, gap 14, ranks on).

Scope: this is the **voice-leading** (parsimony) layer only — undirected,
key-free, register-less (`spec_level="identity_only"`). The diagram's
*functional-resolution* arrows (V7→I) are a different, directed, key-relative
relation (a fifth-related dominant resolution is not voice-leading-parsimonious
— G7→C is far in VL terms); that layer needs a key context and is recorded as
a gap-14 extension, not conflated here. Numeric/structural only.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from collections.abc import Iterable
from itertools import combinations

from ..analysis.voice_leading import voice_leading
from ..core.bitmask import mask_from_pcs
from ..core.chord import Chord
from ..core.quality import ChordQuality
from ..core.symmetry import mask_symmetry_order


@dataclass(frozen=True)
class ChordNetworkNode:
    """One chord in the network, with its symmetry (the hub signal)."""

    index: int
    root_pc: int
    quality: str
    pcs: list[int]
    mask: int
    cardinality: int
    symmetry_order: int  # rotational order; <12 marks a symmetric "hub" (aug=4, dim7=3)


@dataclass(frozen=True)
class ChordNetworkEdge:
    """A voice-leading edge: the minimal motion between two chords (undirected)."""

    source: int  # node index, < target
    target: int
    distance: int  # voice_leading distance (total semitone motion, mod-12 circular)
    common_tones: int
    root_interval: int  # (target.root - source.root) % 12


@dataclass(frozen=True)
class ChordNetwork:
    """The voice-leading parsimony graph over a chord vocabulary."""

    spec_level: str  # always "identity_only"
    max_distance: int
    nodes: list[ChordNetworkNode]
    edges: list[ChordNetworkEdge]

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def chord_network_descriptor(
    chords: Iterable[tuple[int, ChordQuality]],
    *,
    max_distance: int = 2,
) -> ChordNetwork:
    """Build the voice-leading network over *chords* (``(root_pc, quality)``).

    An undirected edge joins every pair whose voice-leading distance is
    ``<= max_distance``. Raises on an empty vocabulary or a non-positive
    threshold.
    """

    if max_distance < 1:
        raise ValueError("max_distance must be >= 1.")
    nodes: list[ChordNetworkNode] = []
    pcs_by_index: list[tuple[int, ...]] = []
    for index, (root_pc, quality) in enumerate(chords):
        chord = Chord.from_quality(int(root_pc) % 12, quality)
        pcs = tuple(chord.pcs)
        pcs_by_index.append(pcs)
        nodes.append(
            ChordNetworkNode(
                index=index,
                root_pc=chord.root_pc,
                quality=quality.name,
                pcs=list(pcs),
                mask=mask_from_pcs(pcs),
                cardinality=len(set(pcs)),
                symmetry_order=mask_symmetry_order(mask_from_pcs(pcs)),
            )
        )
    if not nodes:
        raise ValueError("chord_network_descriptor needs at least one chord.")

    edges: list[ChordNetworkEdge] = []
    for a, b in combinations(range(len(nodes)), 2):
        distance = voice_leading(list(pcs_by_index[a]), list(pcs_by_index[b])).distance
        if distance <= max_distance:
            edges.append(
                ChordNetworkEdge(
                    source=a,
                    target=b,
                    distance=distance,
                    common_tones=len(set(pcs_by_index[a]) & set(pcs_by_index[b])),
                    root_interval=(nodes[b].root_pc - nodes[a].root_pc) % 12,
                )
            )

    return ChordNetwork(
        spec_level="identity_only",
        max_distance=max_distance,
        nodes=nodes,
        edges=edges,
    )


__all__ = ["ChordNetwork", "ChordNetworkEdge", "ChordNetworkNode", "chord_network_descriptor"]
