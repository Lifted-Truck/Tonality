"""Rulesets: a declarative constraint syntax over the analytical vocabulary.

Phase 4.6, first slice (schema + evaluator). A *ruleset* is a named,
versioned, JSON-serializable collection of rules; each rule quantifies over
one atom family from the Workstream 0 vocabulary (voice-pair motion, melodic
atoms, rhythmic atoms) and either *forbids* a pattern or *requires* one,
hard or soft. No code execution anywhere — rules are data, validation is
strict enough that a blind LLM's translation is mechanically checkable, and
evaluation is deterministic (no new theory; the atoms carry the facts).
"""

from .schema import (
    FAMILIES,
    Rule,
    Ruleset,
    RulesetValidationError,
    parse_ruleset,
    validation_errors,
)
from .evaluator import (
    ConformanceReport,
    RuleResult,
    Violation,
    evaluate,
)

__all__ = [
    "FAMILIES",
    "Rule",
    "Ruleset",
    "RulesetValidationError",
    "parse_ruleset",
    "validation_errors",
    "ConformanceReport",
    "RuleResult",
    "Violation",
    "evaluate",
]
