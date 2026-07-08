"""The named ruleset library — citable rulesets shipped as data (gap D).

The rules infrastructure treats rulesets as versioned priors, but ships them as
hand-authored JSON in ``mts/data/rulesets/``. This module loads them by name,
validated through the same strict parser as any other ruleset (so a shipped
ruleset that drifts out of the DSL fails loudly, exactly like a caller's would).

The library's second purpose is a **stress test of DSL expressiveness**: each
authored ruleset documents, in its ``description``, the rules it could NOT
express in the current families — those omissions are recorded evidence for the
phrase/global scope, cross-field comparison, and pattern-layer gaps (ROADMAP
gap D), not failures.
"""

from __future__ import annotations

import json

from ..io.loaders import DATA_DIR
from .schema import Ruleset, parse_ruleset

_RULESETS_DIR = DATA_DIR / "rulesets"


def list_named_rulesets() -> list[str]:
    """The names (filename stems) of every shipped ruleset, sorted."""

    if not _RULESETS_DIR.is_dir():
        return []
    return sorted(p.stem for p in _RULESETS_DIR.glob("*.json"))


def load_named_ruleset(name: str) -> Ruleset:
    """Load and validate a shipped ruleset by name (its filename stem).

    Raises ``ValueError`` naming the known rulesets if *name* is unknown, or
    :class:`~mts.rules.schema.RulesetValidationError` if the shipped JSON is not
    a valid ruleset (a shipped ruleset is held to the same strict contract as a
    caller-supplied one — no exceptions for being in-repo).
    """

    path = _RULESETS_DIR / f"{name}.json"
    if not path.is_file():
        known = ", ".join(list_named_rulesets()) or "(none)"
        raise ValueError(f"Unknown ruleset {name!r} (known: {known}).")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return parse_ruleset(payload)


__all__ = ["list_named_rulesets", "load_named_ruleset"]
