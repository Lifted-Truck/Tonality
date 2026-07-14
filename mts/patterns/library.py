"""The named pattern library — citable patterns shipped as data (gap C).

Mirrors the named-ruleset library: hand-authored JSON in ``mts/data/patterns/``,
loaded by name and validated through the same strict parser as a caller's
pattern — a shipped pattern that drifts out of the schema fails loudly.
"""

from __future__ import annotations

import json

from ..io.loaders import DATA_DIR
from .cross_part import CrossPartPattern, parse_cross_part_pattern
from .schema import Pattern, parse_pattern

_PATTERNS_DIR = DATA_DIR / "patterns"
_CROSS_PART_DIR = _PATTERNS_DIR / "cross_part"


def list_named_patterns() -> list[str]:
    """The names (filename stems) of every shipped melody pattern, sorted.

    Globs the top level only, so cross-part schemata (in the ``cross_part/``
    subdir, a different object) are not returned here — use
    :func:`list_named_cross_part_patterns`."""

    if not _PATTERNS_DIR.is_dir():
        return []
    return sorted(p.stem for p in _PATTERNS_DIR.glob("*.json"))


def load_named_pattern(name: str) -> Pattern:
    """Load and validate a shipped pattern by name (its filename stem).

    Raises ``ValueError`` naming the known patterns if *name* is unknown, or
    :class:`~mts.patterns.schema.PatternValidationError` if the shipped JSON is
    invalid (held to the same contract as a caller-supplied pattern).
    """

    path = _PATTERNS_DIR / f"{name}.json"
    if not path.is_file():
        known = ", ".join(list_named_patterns()) or "(none)"
        raise ValueError(f"Unknown pattern {name!r} (known: {known}).")
    return parse_pattern(json.loads(path.read_text()))


__all__ = [
    "list_named_patterns", "load_named_pattern",
    "list_named_cross_part_patterns", "load_named_cross_part_pattern",
]


def list_named_cross_part_patterns() -> list[str]:
    """The names of every shipped cross-part schema (``cross_part/`` subdir)."""

    if not _CROSS_PART_DIR.is_dir():
        return []
    return sorted(p.stem for p in _CROSS_PART_DIR.glob("*.json"))


def load_named_cross_part_pattern(name: str) -> CrossPartPattern:
    """Load and validate a shipped cross-part schema by name (its filename stem).

    Held to the same strict contract as a caller-supplied pattern (a shipped
    schema that drifts out of the schema fails loudly)."""

    path = _CROSS_PART_DIR / f"{name}.json"
    if not path.is_file():
        known = ", ".join(list_named_cross_part_patterns()) or "(none)"
        raise ValueError(f"Unknown cross-part pattern {name!r} (known: {known}).")
    return parse_cross_part_pattern(json.loads(path.read_text()))
