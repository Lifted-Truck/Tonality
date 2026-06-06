"""The realization: an ordered list of actual pitches, sibling to the identity key.

A *realization* is the register-bearing representation of musical material — an
ordered tuple of :class:`~mts.core.pitch.Pitch` with octaves, doublings, and a
bass. It is the richer cousin of the identity key (a 12-bit pitch-class bitmask):
you can always **reduce** a realization to its key, but you can never *invent* a
realization from a key without choosing a voicing — a generative act, not an
analytical one (ROADMAP "cardinal rule").

The lattice cell of a realization is always ``REGISTERED``; whether it is
``ROOTED`` depends on ``root_pc``:

- ``root_pc`` set      → a real **voicing** (``SpecLevel.VOICING``)
- ``root_pc is None``  → a **voicing template** (``SpecLevel.VOICING_TEMPLATE``),
  the registered-but-rootless corner that ``scope`` could never express.

The only 12-TET-specific code here is :meth:`reduce_to_key`, which crosses the
reduction boundary into the bitmask substrate (ROADMAP Decision 6).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .bitmask import mask_from_pcs, validate_pc
from .pitch import Pitch
from .spec_level import SpecLevel


@dataclass(frozen=True)
class Realization:
    """An ordered set of registered pitches, with an optional fixed root.

    Frozen and hashable. ``pitches`` is kept in caller-supplied order (voicing
    order); register-aware analysis reads that order, while the bass is derived
    from absolute pitch height. Doublings are expressed naturally as repeated
    pitch classes within ``pitches``.
    """

    pitches: tuple[Pitch, ...]
    root_pc: int | None = None

    def __post_init__(self) -> None:
        if not self.pitches:
            raise ValueError("A Realization needs at least one pitch.")
        if self.root_pc is not None:
            validate_pc(self.root_pc)

    @classmethod
    def from_midi(
        cls,
        values: Iterable[int],
        *,
        root_pc: int | None = None,
    ) -> "Realization":
        """Build a realization from raw MIDI note numbers (voicing order)."""

        return cls(tuple(Pitch.from_midi(int(v)) for v in values), root_pc=root_pc)

    @property
    def is_rooted(self) -> bool:
        """True when a fixed root is assigned (a voicing, not a template)."""

        return self.root_pc is not None

    @property
    def spec_level(self) -> SpecLevel:
        """A realization is always REGISTERED; ROOTED iff ``root_pc`` is set."""

        return SpecLevel.classify(rooted=self.is_rooted, registered=True)

    @property
    def bass(self) -> Pitch:
        """The lowest-sounding pitch (least MIDI value)."""

        return min(self.pitches, key=lambda p: p.midi)

    @property
    def pcs(self) -> tuple[int, ...]:
        """Pitch classes in voicing order, doublings preserved."""

        return tuple(p.pc for p in self.pitches)

    @property
    def distinct_pcs(self) -> tuple[int, ...]:
        """The sorted, de-duplicated pitch classes present."""

        return tuple(sorted(set(self.pcs)))

    @property
    def doublings(self) -> tuple[int, ...]:
        """Pitch classes that appear more than once (sorted)."""

        seen: dict[int, int] = {}
        for pc in self.pcs:
            seen[pc] = seen.get(pc, 0) + 1
        return tuple(sorted(pc for pc, count in seen.items() if count > 1))

    def reduce_to_key(self) -> int:
        """Reduce this realization to its identity key (12-bit PC bitmask).

        This is the one-directional reduction (realization → key) and the only
        12-TET-aware operation on the type — the reduction boundary of
        ROADMAP Decision 6.
        """

        return mask_from_pcs(self.distinct_pcs)


__all__ = ["Realization"]
