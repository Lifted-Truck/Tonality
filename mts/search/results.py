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
    not just a yes. ``dft_magnitudes`` is the full ``|f1..f6|`` interval-content
    spectrum (the ``df1..df6`` fields), always present so a caller can *rank*
    matches by graded diatonicity/etc., not merely filter on a threshold.
    """

    mask: int
    pcs: tuple[int, ...]
    cardinality: int
    interval_vector: tuple[int, int, int, int, int, int]
    rotational_period: int
    is_achiral: bool
    dft_magnitudes: tuple[float, float, float, float, float, float]
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


@dataclass(frozen=True)
class VoicingMatch:
    """One concrete registered voicing satisfying the search constraints.

    ``midi`` is ascending. ``intervals_over_bass`` are the directed pc-intervals
    (1..11) of the upper voices above the bass. ``voicing_type`` is the named
    shape (closed / drop2 / …) when the spacing matches the root-position
    registry exactly, else ``None`` (inversions are unlabeled in slice 1); it is
    always ``None`` for a rootless template. ``vl_from`` is the exact realized
    voice-leading cost from the caller's reference voicing (``doubling.1``),
    ``None`` when no reference was given — matches are *sorted* by it when
    present (the ranking half of gap 17), and it stays a continuous signal the
    caller can re-rank (rule 7: plural outputs).
    """

    midi: tuple[int, ...]
    spread: int
    bass_pc: int
    top_pc: int
    top_midi: int
    center: float
    intervals_over_bass: tuple[int, ...]
    voicing_type: str | None
    vl_from: int | None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class VoicingSearchResult:
    """The full, exact result set of one voicing search.

    ``space`` is the raw register-assignment space that was enumerated (the
    product of per-pc candidate counts inside the window) — reported so the
    caller sees the search's true extent. ``count`` is the total number of
    matches (independent of ``limit``); ``truncated`` means only that ``limit``
    cut the *reported* list. ``root`` is ``None`` for a voicing-template search
    (the registered+rootless lattice corner).
    """

    pcs: tuple[int, ...]
    root: int | None
    constraints: dict
    from_voicing: tuple[int, ...] | None
    space: int
    count: int
    matches: tuple[VoicingMatch, ...]
    truncated: bool = False

    def to_dict(self) -> dict:
        return {
            "pcs": list(self.pcs),
            "root": self.root,
            "constraints": self.constraints,
            "from_voicing": list(self.from_voicing) if self.from_voicing else None,
            "space": self.space,
            "count": self.count,
            "truncated": self.truncated,
            "matches": [m.to_dict() for m in self.matches],
        }


__all__ = ["IdentityMatch", "IdentitySearchResult", "VoicingMatch", "VoicingSearchResult"]
