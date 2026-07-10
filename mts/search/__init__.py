"""Constraint search — exact, exhaustive queries over the identity universe.

The *inverse* of analysis: instead of "what is this set?", ask "which sets
satisfy these constraints?" and let the engine enumerate them exactly over the
4096-mask universe (Phase 4, the marquee agent-facing tool). This is
**generative-side** (ROADMAP cardinal rule): a search constraint and a
checkable rule are the same predicate pointed in opposite directions, so the
scalar predicate machinery is the ruleset engine's ``Condition`` (eq/in/gte/lte)
reused over an *identity* field vocabulary.

``search_identities`` is v1 (pitch-class-set identities). ``search_voicings``
(register enumeration, a bounded generative space) is the planned sibling under
the same predicate contract — see ROADMAP Phase 4.
"""

from __future__ import annotations

from .fields import IDENTITY_FIELDS
from .identities import search_identities
from .results import (
    IdentityMatch,
    IdentitySearchResult,
    Repair,
    RepairEdit,
    RepairResult,
    VoicingMatch,
    VoicingSearchResult,
)
from .repair import repair_sequence
from .voicings import VOICING_FIELDS, search_voicings

__all__ = [
    "IDENTITY_FIELDS",
    "IdentityMatch",
    "IdentitySearchResult",
    "VOICING_FIELDS",
    "VoicingMatch",
    "VoicingSearchResult",
    "search_identities",
    "search_voicings",
    "Repair",
    "RepairEdit",
    "RepairResult",
    "repair_sequence",
]
