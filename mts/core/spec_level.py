"""The identity lattice: two independent reductions over a pitch-class identity.

A musical specification occupies a cell in a 2x2 lattice defined by two
*independent* axes (see ROADMAP "core data model"):

- **Transpositional** — is the root fixed (``ROOTED``), or is only the
  transposition-invariant *shape* known (``SHAPE``)?
- **Registral** — are octaves/spacing fixed (``REGISTERED``), or is the identity
  octave-invariant (``PC_SET``)?

The four corners:

==================  ==============  =====================
registral           transpositional  meaning
==================  ==============  =====================
``REGISTERED``      ``ROOTED``       a real **voicing**
``PC_SET``          ``ROOTED``       a named **chord**
``PC_SET``          ``SHAPE``        an interval **shape**
``REGISTERED``      ``SHAPE``        a **voicing template**
==================  ==============  =====================

These axes are deliberately **tuning-agnostic**: rooted-ness and register-ness
are not 12-TET concepts. Keep them that way (ROADMAP Decision 6) so the eventual
multi-system generalization (Phase 5) stays a localized change rather than a
rewrite. This module imports nothing from ``mts`` and knows nothing about the
number 12.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


class Transpositional(Enum):
    """Is the root fixed, or only the transposition-invariant shape known?"""

    ROOTED = "rooted"
    SHAPE = "shape"


class Registral(Enum):
    """Are octaves/spacing fixed, or is the identity octave-invariant?"""

    REGISTERED = "registered"
    PC_SET = "pc_set"


@dataclass(frozen=True)
class SpecLevel:
    """A cell in the transpositional × registral lattice.

    Frozen and hashable, so it can be used as a dict key and compared by value.
    Prefer the four named corners (:data:`VOICING`, :data:`NAMED_CHORD`,
    :data:`INTERVAL_SHAPE`, :data:`VOICING_TEMPLATE`) or :meth:`classify` over
    constructing instances directly.
    """

    transpositional: Transpositional
    registral: Registral

    # The four corners, attached after the class body for ergonomic access
    # (``SpecLevel.VOICING``). Declared here so type checkers see them.
    VOICING: ClassVar["SpecLevel"]
    NAMED_CHORD: ClassVar["SpecLevel"]
    INTERVAL_SHAPE: ClassVar["SpecLevel"]
    VOICING_TEMPLATE: ClassVar["SpecLevel"]

    @property
    def is_rooted(self) -> bool:
        """True when the root is fixed (``ROOTED``)."""

        return self.transpositional is Transpositional.ROOTED

    @property
    def is_registered(self) -> bool:
        """True when octaves/spacing are fixed (``REGISTERED``)."""

        return self.registral is Registral.REGISTERED

    @classmethod
    def classify(cls, *, rooted: bool, registered: bool) -> "SpecLevel":
        """Return the lattice cell for the given axis truth values."""

        return cls(
            Transpositional.ROOTED if rooted else Transpositional.SHAPE,
            Registral.REGISTERED if registered else Registral.PC_SET,
        )

    @property
    def label(self) -> str:
        """Human-readable name of this corner (e.g. ``"voicing template"``)."""

        return _LABELS[self]

    def __str__(self) -> str:
        return self.label


# The four corners of the lattice.
VOICING = SpecLevel(Transpositional.ROOTED, Registral.REGISTERED)
NAMED_CHORD = SpecLevel(Transpositional.ROOTED, Registral.PC_SET)
INTERVAL_SHAPE = SpecLevel(Transpositional.SHAPE, Registral.PC_SET)
VOICING_TEMPLATE = SpecLevel(Transpositional.SHAPE, Registral.REGISTERED)

_LABELS: dict[SpecLevel, str] = {
    VOICING: "voicing",
    NAMED_CHORD: "named chord",
    INTERVAL_SHAPE: "interval shape",
    VOICING_TEMPLATE: "voicing template",
}

SpecLevel.VOICING = VOICING
SpecLevel.NAMED_CHORD = NAMED_CHORD
SpecLevel.INTERVAL_SHAPE = INTERVAL_SHAPE
SpecLevel.VOICING_TEMPLATE = VOICING_TEMPLATE


__all__ = [
    "Transpositional",
    "Registral",
    "SpecLevel",
    "VOICING",
    "NAMED_CHORD",
    "INTERVAL_SHAPE",
    "VOICING_TEMPLATE",
]
