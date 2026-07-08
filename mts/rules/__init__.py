"""Rulesets: a declarative constraint syntax over the analytical vocabulary.

Phase 4.6: a *ruleset* is a named, versioned, JSON-serializable collection of
rules; each rule quantifies over one atom family from the Workstream 0
vocabulary (voice-pair motion, melodic atoms, rhythmic atoms) and either
*forbids* a pattern or *requires* one, hard or soft. No code execution
anywhere — rules are data, validation is strict enough that a blind LLM's
translation is mechanically checkable, evaluation is deterministic (no new
theory; the atoms carry the facts), and rulesets **compose and compare** as
data (combine / specialize / diff).
"""

from .schema import (
    FAMILIES,
    FIELD_MANIFEST_VERSION,
    Rule,
    Ruleset,
    RulesetValidationError,
    parse_ruleset,
    ruleset_field_manifest,
    rule_to_payload,
    ruleset_to_payload,
    validation_errors,
)
from .evaluator import (
    ConformanceReport,
    Firing,
    RuleResult,
    Violation,
    evaluate,
)
from .composition import (
    RuleContradiction,
    RulesetComparison,
    RulesetConflictError,
    SpecializeResult,
    combine,
    compare,
    specialize,
)
from .induction import InductionResult, RuleEvidence, induce_ruleset
from .library import list_named_rulesets, load_named_ruleset
from .transition import TransitionMatrix, build_transition_matrix

__all__ = [
    "InductionResult",
    "RuleEvidence",
    "induce_ruleset",
    "TransitionMatrix",
    "build_transition_matrix",
    "list_named_rulesets",
    "load_named_ruleset",
    "FAMILIES",
    "FIELD_MANIFEST_VERSION",
    "Rule",
    "Ruleset",
    "RulesetValidationError",
    "parse_ruleset",
    "ruleset_field_manifest",
    "rule_to_payload",
    "ruleset_to_payload",
    "validation_errors",
    "ConformanceReport",
    "Firing",
    "RuleResult",
    "Violation",
    "evaluate",
    "RuleContradiction",
    "RulesetComparison",
    "RulesetConflictError",
    "SpecializeResult",
    "combine",
    "compare",
    "specialize",
]
