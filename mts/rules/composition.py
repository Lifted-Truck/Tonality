"""Ruleset composition + comparison (Phase 4.6 slice 2).

Rulesets are first-class artifacts, so they compose and compare as data — no
evaluation, no new theory, deterministic:

- :func:`combine` — union several rulesets into one (a style assembled from
  parts). Rules with the same id must be structurally identical, else it's a
  conflict you must resolve with :func:`specialize` instead of silently
  picking one.
- :func:`specialize` — a base ruleset overlaid by another: same-id overlay
  rules **replace** the base's (the "common-practice + these overrides" move),
  new ids append. Reports what was overridden vs added.
- :func:`compare` — the structural diff: which rules are shared, which differ
  under a shared id, which are unique to each, and which pairs **directly
  contradict** (same family + filter + check, one ``forbid`` vs one
  ``require`` — provably unsatisfiable together on any considered item).

Comparison is *structural*. Empirical comparison — "which conforms more on
this corpus" — is two :func:`~mts.rules.evaluator.evaluate` calls on the same
material, not a new primitive here.

Condition order within a rule's ``where``/``check`` is semantically
irrelevant (they AND), so structural identity compares condition **sets**,
not tuples.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from .schema import Rule, Ruleset, parse_ruleset, rule_to_payload


def _rule_identity(rule: Rule) -> tuple:
    """A rule's structural key, order-insensitive over its conditions."""

    return (
        rule.id,
        rule.family,
        frozenset(rule.where),
        rule.check_kind,
        frozenset(rule.check),
        rule.polarity,
        rule.weight,
        rule.max_rate,
    )


def _as_ruleset(rs: Ruleset | dict) -> Ruleset:
    return rs if isinstance(rs, Ruleset) else parse_ruleset(rs)


# --- combine -----------------------------------------------------------------------------


class RulesetConflictError(ValueError):
    """Same id, structurally different rules — combine can't choose. Use specialize."""

    def __init__(self, conflicts: list[str]):
        self.conflicts = list(conflicts)
        super().__init__(
            "Cannot combine — these rule ids appear with different definitions: "
            + ", ".join(conflicts)
            + " (use specialize() to let one ruleset override the other)."
        )


def combine(
    rulesets: list[Ruleset | dict], *, name: str, version: str, description: str = ""
) -> Ruleset:
    """Union of *rulesets* into one. Identical same-id rules dedup; conflicting
    same-id rules raise :class:`RulesetConflictError`."""

    parsed = [_as_ruleset(rs) for rs in rulesets]
    by_id: dict[str, Rule] = {}
    conflicts: list[str] = []
    for ruleset in parsed:
        for rule in ruleset.rules:
            existing = by_id.get(rule.id)
            if existing is None:
                by_id[rule.id] = rule
            elif _rule_identity(existing) != _rule_identity(rule):
                if rule.id not in conflicts:
                    conflicts.append(rule.id)
    if conflicts:
        raise RulesetConflictError(conflicts)
    return Ruleset(
        name=name, version=version, description=description, rules=tuple(by_id.values())
    )


# --- specialize --------------------------------------------------------------------------


@dataclass(frozen=True)
class SpecializeResult:
    """A specialized ruleset plus what the overlay changed."""

    ruleset_payload: dict  # the JSON DSL document of the result
    overridden: list[str]  # base ids the overlay replaced
    added: list[str]  # overlay ids new to the base

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def specialize(
    base: Ruleset | dict,
    overlay: Ruleset | dict,
    *,
    name: str,
    version: str,
    description: str = "",
) -> SpecializeResult:
    """Overlay *overlay* onto *base*: same-id overlay rules replace base rules
    (preserving base order), new overlay rules append."""

    base_rs = _as_ruleset(base)
    overlay_rs = _as_ruleset(overlay)
    overlay_by_id = {rule.id: rule for rule in overlay_rs.rules}

    overridden: list[str] = []
    rules: list[Rule] = []
    for rule in base_rs.rules:
        replacement = overlay_by_id.get(rule.id)
        if replacement is not None:
            rules.append(replacement)
            if _rule_identity(replacement) != _rule_identity(rule):
                overridden.append(rule.id)
        else:
            rules.append(rule)
    base_ids = {rule.id for rule in base_rs.rules}
    added = [rule.id for rule in overlay_rs.rules if rule.id not in base_ids]
    rules.extend(rule for rule in overlay_rs.rules if rule.id not in base_ids)

    result = Ruleset(name=name, version=version, description=description, rules=tuple(rules))
    from .schema import ruleset_to_payload

    return SpecializeResult(
        ruleset_payload=ruleset_to_payload(result),
        overridden=overridden,
        added=added,
    )


# --- compare -----------------------------------------------------------------------------


@dataclass(frozen=True)
class RuleContradiction:
    """Two rules that cannot both hold on any item they both consider."""

    a_id: str
    b_id: str
    family: str
    detail: str  # which forbids / which requires the same check

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class RulesetComparison:
    """The structural diff of two rulesets."""

    shared_ids: list[str]  # same id, structurally identical
    conflicting_ids: list[str]  # same id, structurally different
    only_in_a: list[str]
    only_in_b: list[str]
    contradictions: list[RuleContradiction]

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def compare(a: Ruleset | dict, b: Ruleset | dict) -> RulesetComparison:
    """Structurally compare two rulesets: shared / conflicting / unique ids,
    and directly-contradictory rule pairs."""

    a_rs = _as_ruleset(a)
    b_rs = _as_ruleset(b)
    a_by_id = {rule.id: rule for rule in a_rs.rules}
    b_by_id = {rule.id: rule for rule in b_rs.rules}

    shared, conflicting = [], []
    for rule_id in sorted(a_by_id.keys() & b_by_id.keys()):
        if _rule_identity(a_by_id[rule_id]) == _rule_identity(b_by_id[rule_id]):
            shared.append(rule_id)
        else:
            conflicting.append(rule_id)

    contradictions: list[RuleContradiction] = []
    for rule_a in a_rs.rules:
        for rule_b in b_rs.rules:
            if (
                rule_a.family == rule_b.family
                and frozenset(rule_a.where) == frozenset(rule_b.where)
                and frozenset(rule_a.check) == frozenset(rule_b.check)
                and rule_a.check_kind != rule_b.check_kind
            ):
                forbids, requires = (
                    (rule_a.id, rule_b.id)
                    if rule_a.check_kind == "forbid"
                    else (rule_b.id, rule_a.id)
                )
                contradictions.append(
                    RuleContradiction(
                        a_id=rule_a.id,
                        b_id=rule_b.id,
                        family=rule_a.family,
                        detail=f"{forbids!r} forbids what {requires!r} requires (same filter+check)",
                    )
                )

    return RulesetComparison(
        shared_ids=shared,
        conflicting_ids=conflicting,
        only_in_a=sorted(a_by_id.keys() - b_by_id.keys()),
        only_in_b=sorted(b_by_id.keys() - a_by_id.keys()),
        contradictions=contradictions,
    )


__all__ = [
    "RuleContradiction",
    "RulesetComparison",
    "RulesetConflictError",
    "SpecializeResult",
    "combine",
    "compare",
    "specialize",
]
