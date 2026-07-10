"""Patterns (Phase 4.6, gap C): sequential templates as first-class objects.

Rules say what is *forbidden/required*; patterns say what is **characteristic**.
A :class:`Pattern` declares its abstraction level on two independent axes
(pitch: exact/degree/contour × time: exact/free — the identity lattice at
pattern grain) and :func:`find_pattern` locates every occurrence, exact under
that declaration. Slice 1 is the melodic domain; harmonic schemas, rhythmic
templates, rule-projection, and PrefixSpan-family induction are recorded
follow-ons (ROADMAP gap C).
"""

from .schema import (
    CONTOUR_MOVES,
    DOMAINS,
    PITCH_LEVELS,
    SCHEMA_VERSION,
    TIME_LEVELS,
    Pattern,
    PatternValidationError,
    parse_pattern,
    pattern_to_payload,
    pattern_validation_errors,
)
from .matcher import find_pattern
from .library import list_named_patterns, load_named_pattern
from .results import PatternMatches, PatternOccurrence

__all__ = [
    "SCHEMA_VERSION",
    "PITCH_LEVELS",
    "TIME_LEVELS",
    "DOMAINS",
    "CONTOUR_MOVES",
    "Pattern",
    "PatternValidationError",
    "parse_pattern",
    "pattern_to_payload",
    "pattern_validation_errors",
    "find_pattern",
    "list_named_patterns",
    "load_named_pattern",
    "PatternMatches",
    "PatternOccurrence",
]
