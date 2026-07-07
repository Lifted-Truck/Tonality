"""Typed results for constraint search (generative-side; kept separate from
``analysis/results.py`` — search is the inverse of analysis, not part of it)."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass


@dataclass(frozen=True)
class IdentityMatch:
    """One identity satisfying the search constraints.

    ``mask`` / ``pcs`` are the set-class prime form by default, or a literal
    rooted image when ``expand_transpositions`` was set. ``contains_roots`` (when
    a ``contains`` constraint was given) reports the roots at which the queried
    shape appears in this identity — turning the match into a placement answer,
    not just a yes.
    """

    mask: int
    pcs: tuple[int, ...]
    cardinality: int
    interval_vector: tuple[int, int, int, int, int, int]
    rotational_period: int
    is_achiral: bool
    contains_roots: tuple[int, ...] | None = None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class IdentitySearchResult:
    """The full, exact result set of one identity search.

    ``constraints`` echoes the normalized query (so a blind agent sees exactly
    what was applied); ``universe`` is ``"set_classes"`` or ``"all_masks"``;
    ``truncated`` flags that ``limit`` cut the reported matches (``count`` is
    always the true total, so a truncated view never reads as "this is all").
    """

    constraints: dict
    universe: str
    count: int
    matches: tuple[IdentityMatch, ...]
    truncated: bool = False

    def to_dict(self) -> dict:
        return {
            "constraints": self.constraints,
            "universe": self.universe,
            "count": self.count,
            "truncated": self.truncated,
            "matches": [m.to_dict() for m in self.matches],
        }


__all__ = ["IdentityMatch", "IdentitySearchResult"]
