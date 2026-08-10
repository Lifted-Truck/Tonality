"""Generative layer: note-out transforms (Phase 7 slices).

The other side of the cardinal rule from ``analysis/``: these functions CHOOSE
pitches. Everything here is deterministic and freezable (no RNG, no clock), and
each transform states what it preserves — the first residents, the conform
family, preserve everything except pitch class (register, onset, duration,
velocity, voice, order and count all held).

Sits beside ``search/`` (its constrained-re-pitch cousin ``repair_sequence``
imposes a ruleset; ``conform_to_scale`` imposes a scale — same act, simpler
oracle).
"""

from __future__ import annotations

from .conform import (
    Collision,
    ConformEdit,
    ConformResult,
    conform_to_scale,
    fit_to_key,
)
from .remap import (
    AbsorbedAlteration,
    InterscalarMap,
    RemapEdit,
    RemapResult,
    RetonicizeResult,
    remap_by_degree,
    retonicize,
)

__all__ = [
    "Collision",
    "ConformEdit",
    "ConformResult",
    "conform_to_scale",
    "fit_to_key",
    "AbsorbedAlteration",
    "InterscalarMap",
    "RemapEdit",
    "RemapResult",
    "RetonicizeResult",
    "remap_by_degree",
    "retonicize",
]
