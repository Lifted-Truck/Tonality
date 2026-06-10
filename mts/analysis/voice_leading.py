"""Minimal voice-leading distance between pitch-class identities (Phase 3.5).

**Analytical, not generative** — this measures how far apart two identities
are under optimal voice leading; it does not realize voices in register
(that is Phase 7's job, which consumes this metric).

Method: total taxicab motion under the best non-crossing assignment, where
per-voice motion is circular pc distance (``min(d, 12-d)``). Voice leadings
between cyclically ordered pc sets can always be put in non-crossing form
without increasing total motion (Tymoczko), so:

- equal cardinality: the optimum is one of the *n* cyclic rotations of the
  sorted-to-sorted alignment;
- unequal cardinality: the optimum is a non-crossing surjection from the
  larger set onto the smaller — enumerated as contiguous circular blocks.

Both are exact; the test suite cross-validates against brute-force
enumeration of all bijections/surjections.

**Cardinality policy is a named choice, not a fact** (ROADMAP Phase 3.5):
``"doubling.1"`` requires every pc of *both* sets to participate, letting
pcs of the smaller set carry several voices (how a triad moves to a seventh
chord with one tone splitting). Alternatives (e.g. omission) can be added as
new policy ids; results cite the policy used so downstream numbers stay
reproducible.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache
from itertools import combinations

from ..core.bitmask import mask_from_pcs, pcs_from_mask
from .results import VoiceLeadingResult

POLICY_DOUBLING_V1 = "doubling.1"
_POLICIES = (POLICY_DOUBLING_V1,)


def _circular_distance(a: int, b: int) -> int:
    d = abs(a - b) % 12
    return min(d, 12 - d)


def _best_bijection(source: list[int], target: list[int]) -> tuple[int, tuple[tuple[int, int], ...]]:
    """Optimal non-crossing bijection between equal-cardinality sorted pc lists."""
    n = len(source)
    best_cost = None
    best_pairs: tuple[tuple[int, int], ...] = ()
    for offset in range(n):
        pairs = tuple((source[i], target[(i + offset) % n]) for i in range(n))
        cost = sum(_circular_distance(a, b) for a, b in pairs)
        if best_cost is None or cost < best_cost:
            best_cost = cost
            best_pairs = pairs
    return best_cost, best_pairs


def _best_surjection(larger: list[int], smaller: list[int]) -> tuple[int, tuple[tuple[int, int], ...]]:
    """Optimal non-crossing surjection from the larger onto the smaller pc list.

    A non-crossing surjection partitions the larger set (in circular order)
    into ``m`` contiguous non-empty blocks assigned, in circular order, to the
    smaller set's pcs. Enumerate every (larger-rotation, smaller-rotation,
    block-composition); sizes are ≤ 12 so this is small and exact.
    """
    n, m = len(larger), len(smaller)
    best_cost = None
    best_pairs: tuple[tuple[int, int], ...] = ()
    for big_offset in range(n):
        rotated = larger[big_offset:] + larger[:big_offset]
        for small_offset in range(m):
            anchors = smaller[small_offset:] + smaller[:small_offset]
            # Compositions of n into m positive parts: choose m-1 cut points.
            for cuts in combinations(range(1, n), m - 1):
                bounds = (0, *cuts, n)
                cost = 0
                pairs: list[tuple[int, int]] = []
                for block_index in range(m):
                    anchor = anchors[block_index]
                    for i in range(bounds[block_index], bounds[block_index + 1]):
                        cost += _circular_distance(rotated[i], anchor)
                        pairs.append((rotated[i], anchor))
                if best_cost is None or cost < best_cost:
                    best_cost = cost
                    best_pairs = tuple(pairs)
    return best_cost, best_pairs


@lru_cache(maxsize=16384)
def _vl_between_masks(source_mask: int, target_mask: int) -> tuple[int, tuple[tuple[int, int], ...]]:
    source = pcs_from_mask(source_mask)
    target = pcs_from_mask(target_mask)
    if len(source) == len(target):
        return _best_bijection(source, target)
    if len(source) > len(target):
        cost, pairs = _best_surjection(source, target)
        return cost, pairs
    cost, pairs = _best_surjection(target, source)
    # _best_surjection pairs run (larger_pc, smaller_pc); flip to (source, target).
    return cost, tuple((b, a) for a, b in pairs)


def voice_leading(
    source_pcs: Iterable[int],
    target_pcs: Iterable[int],
    *,
    policy: str = POLICY_DOUBLING_V1,
) -> VoiceLeadingResult:
    """Minimal voice leading from one pc-set identity to another.

    Returns the total motion in semitones *and* the optimal voice mapping
    (the evidence — also what generative consumers realize in register).
    Identity-level: inputs reduce to pc sets; multiplicity and register do
    not exist at this level. Raises ``ValueError`` on an empty side.
    """

    if policy not in _POLICIES:
        known = ", ".join(_POLICIES)
        raise ValueError(f"Unknown voice-leading policy {policy!r} (known: {known}).")
    source_mask = mask_from_pcs({int(pc) % 12 for pc in source_pcs})
    target_mask = mask_from_pcs({int(pc) % 12 for pc in target_pcs})
    if source_mask == 0 or target_mask == 0:
        raise ValueError("voice_leading requires at least one pitch class on each side.")
    distance, mapping = _vl_between_masks(source_mask, target_mask)
    return VoiceLeadingResult(
        distance=distance,
        mapping=[list(pair) for pair in mapping],
        policy=policy,
        source_pcs=pcs_from_mask(source_mask),
        target_pcs=pcs_from_mask(target_mask),
    )


__all__ = ["voice_leading", "POLICY_DOUBLING_V1"]
