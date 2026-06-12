"""Ruleset schema: the rule model and its strict validator.

The DSL is deliberately small (v1). A rule is a JSON object:

    {
      "id": "no-parallel-fifths",
      "family": "voice_motion",
      "where": {"motion": "parallel"},            # optional AND-filter
      "forbid": {"interval_class_to": {"in": [0, 7]}},
      "polarity": "hard"                           # or "soft" (+ "weight")
    }

- ``family`` names the atom stream the rule quantifies over (see
  :data:`FAMILIES`) — the scope is the family's natural item (a voice-pair
  transition, one voice's note).
- ``where`` filters items; only matching items are *considered*.
- Exactly one of ``forbid`` (a considered item matching it is a violation)
  or ``require`` (a considered item NOT matching it is a violation).
- Conditions AND over fields. A condition value is a bare literal
  (equality), ``{"in": [...]}``, ``{"gte": x}``, or ``{"lte": x}``.
  A ``None`` field value (a line edge, a note outside harmony coverage)
  never matches any condition: in ``where`` that excludes the item, and an
  item whose *check* references a ``None`` field is excluded from
  consideration entirely — absence of evidence is not a violation.
- ``polarity``: ``hard`` (the rule must hold) or ``soft`` (a weighted
  preference; ``weight`` > 0, default 1.0; hard rules take no weight).

Validation is **strict and total**: unknown keys, families, fields,
operators, or enum values are each reported with an actionable message, and
*all* errors are collected (not just the first) so a blind LLM can repair a
translation in one round trip.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldSpec:
    kind: str  # "str" | "int" | "float" | "bool"
    values: tuple | None = None  # closed vocabulary, when the field is an enum


_MOTION = ("parallel", "similar", "contrary", "oblique")
_CLASSES = ("unison", "step", "skip", "leap")
_NHT = ("pedal", "suspension", "anticipation", "passing", "neighbor",
        "appoggiatura", "escape", "free")
_PLACEMENT = ("downbeat", "beat", "offbeat", "subdivision")

# The atom vocabulary rules may reference, per family. Field names mirror the
# WS0 result dataclasses exactly (the rule engine reads them via getattr).
FAMILIES: dict[str, dict[str, FieldSpec]] = {
    "voice_motion": {
        "motion": FieldSpec("str", _MOTION),
        "interval_from": FieldSpec("int"),
        "interval_to": FieldSpec("int"),
        "interval_class_from": FieldSpec("int"),
        "interval_class_to": FieldSpec("int"),
        "voice_a": FieldSpec("str"),
        "voice_b": FieldSpec("str"),
        "a_from_midi": FieldSpec("int"),
        "a_to_midi": FieldSpec("int"),
        "b_from_midi": FieldSpec("int"),
        "b_to_midi": FieldSpec("int"),
        "from_beat": FieldSpec("float"),
        "to_beat": FieldSpec("float"),
    },
    "melody": {
        "midi": FieldSpec("int"),
        "pc": FieldSpec("int"),
        "onset": FieldSpec("float"),
        "duration": FieldSpec("float"),
        "approach_interval": FieldSpec("int"),
        "departure_interval": FieldSpec("int"),
        "approach_class": FieldSpec("str", _CLASSES),
        "departure_class": FieldSpec("str", _CLASSES),
        "is_chord_tone": FieldSpec("bool"),
        "nht_type": FieldSpec("str", _NHT),
    },
    "rhythm": {
        "midi": FieldSpec("int"),
        "onset": FieldSpec("float"),
        "duration_beats": FieldSpec("float"),
        "bar": FieldSpec("int"),
        "beat_in_bar": FieldSpec("float"),
        "beat_unit": FieldSpec("float"),
        "placement": FieldSpec("str", _PLACEMENT),
        "is_syncopated": FieldSpec("bool"),
        "ioi_to_next": FieldSpec("float"),
    },
}

# Fields whose claims depend on caller-provided harmony (evaluator
# applicability: referencing these without harmony spans → not applicable).
HARMONY_DEPENDENT_FIELDS = {"melody": {"is_chord_tone", "nht_type"}}

_CONDITION_OPS = ("in", "gte", "lte")
_RULE_KEYS = {"id", "family", "where", "forbid", "require", "polarity", "weight"}
_RULESET_KEYS = {"name", "version", "description", "rules"}


@dataclass(frozen=True)
class Condition:
    field: str
    op: str  # "eq" | "in" | "gte" | "lte"
    value: object

    def matches(self, actual: object) -> bool:
        if actual is None:
            return False  # absent claims never match (see module doc)
        if self.op == "eq":
            return actual == self.value
        if self.op == "in":
            return actual in self.value  # type: ignore[operator]
        if self.op == "gte":
            return actual >= self.value  # type: ignore[operator]
        return actual <= self.value  # "lte"


@dataclass(frozen=True)
class Rule:
    id: str
    family: str
    where: tuple[Condition, ...]
    check_kind: str  # "forbid" | "require"
    check: tuple[Condition, ...]
    polarity: str  # "hard" | "soft"
    weight: float

    def referenced_fields(self) -> set[str]:
        return {c.field for c in self.where} | {c.field for c in self.check}


@dataclass(frozen=True)
class Ruleset:
    name: str
    version: str
    description: str
    rules: tuple[Rule, ...] = field(default_factory=tuple)


class RulesetValidationError(ValueError):
    """All validation problems, collected. ``errors`` is the full list."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("Invalid ruleset:\n- " + "\n- ".join(errors))


def _check_value_kind(spec: FieldSpec, value: object, ctx: str, errors: list[str]) -> None:
    expected = {"str": str, "int": int, "float": (int, float), "bool": bool}[spec.kind]
    if isinstance(value, bool) and spec.kind != "bool":
        errors.append(f"{ctx}: expected {spec.kind}, got bool {value!r}")
    elif not isinstance(value, expected):
        errors.append(f"{ctx}: expected {spec.kind}, got {type(value).__name__} {value!r}")
    elif spec.values is not None and value not in spec.values:
        errors.append(f"{ctx}: {value!r} is not one of {list(spec.values)}")


def _parse_conditions(
    payload: object, family: str, ctx: str, errors: list[str]
) -> tuple[Condition, ...]:
    if not isinstance(payload, dict) or not payload:
        errors.append(f"{ctx}: must be a non-empty object of field conditions")
        return ()
    fields = FAMILIES.get(family, {})
    conditions: list[Condition] = []
    for field_name, raw in payload.items():
        fctx = f"{ctx}.{field_name}"
        spec = fields.get(field_name)
        if spec is None:
            known = ", ".join(sorted(fields))
            errors.append(f"{fctx}: unknown field for family {family!r} (known: {known})")
            continue
        if isinstance(raw, dict):
            if len(raw) != 1 or next(iter(raw)) not in _CONDITION_OPS:
                errors.append(
                    f"{fctx}: operator object must have exactly one of {list(_CONDITION_OPS)}"
                )
                continue
            op, value = next(iter(raw.items()))
            if op == "in":
                if not isinstance(value, list) or not value:
                    errors.append(f"{fctx}.in: must be a non-empty list")
                    continue
                for i, entry in enumerate(value):
                    _check_value_kind(spec, entry, f"{fctx}.in[{i}]", errors)
                conditions.append(Condition(field_name, "in", tuple(value)))
            else:  # gte / lte
                if spec.kind not in ("int", "float"):
                    errors.append(f"{fctx}.{op}: field is {spec.kind}, not numeric")
                    continue
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    errors.append(f"{fctx}.{op}: expected a number, got {value!r}")
                    continue
                conditions.append(Condition(field_name, op, value))
        else:
            _check_value_kind(spec, raw, fctx, errors)
            conditions.append(Condition(field_name, "eq", raw))
    return tuple(conditions)


def _parse_rule(payload: object, index: int, seen_ids: set[str], errors: list[str]) -> Rule | None:
    ctx = f"rules[{index}]"
    if not isinstance(payload, dict):
        errors.append(f"{ctx}: must be an object")
        return None
    unknown = set(payload) - _RULE_KEYS
    if unknown:
        errors.append(f"{ctx}: unknown keys {sorted(unknown)} (allowed: {sorted(_RULE_KEYS)})")

    rule_id = payload.get("id")
    if not isinstance(rule_id, str) or not rule_id.strip():
        errors.append(f"{ctx}.id: required, a non-empty string")
        rule_id = f"<rules[{index}]>"
    elif rule_id in seen_ids:
        errors.append(f"{ctx}.id: duplicate id {rule_id!r}")
    seen_ids.add(rule_id)
    ctx = f"rule {rule_id!r}"

    family = payload.get("family")
    if family not in FAMILIES:
        errors.append(f"{ctx}.family: must be one of {sorted(FAMILIES)}, got {family!r}")
        return None

    has_forbid = "forbid" in payload
    has_require = "require" in payload
    if has_forbid == has_require:
        errors.append(f"{ctx}: exactly one of 'forbid' or 'require' is required")
        return None
    check_kind = "forbid" if has_forbid else "require"
    check = _parse_conditions(payload[check_kind], family, f"{ctx}.{check_kind}", errors)

    where: tuple[Condition, ...] = ()
    if "where" in payload:
        where = _parse_conditions(payload["where"], family, f"{ctx}.where", errors)

    polarity = payload.get("polarity", "hard")
    if polarity not in ("hard", "soft"):
        errors.append(f"{ctx}.polarity: must be 'hard' or 'soft', got {polarity!r}")
        polarity = "hard"
    weight = payload.get("weight")
    if weight is not None:
        if polarity == "hard":
            errors.append(f"{ctx}.weight: hard rules take no weight")
        elif isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight <= 0:
            errors.append(f"{ctx}.weight: must be a positive number, got {weight!r}")
    final_weight = float(weight) if isinstance(weight, (int, float)) and not isinstance(weight, bool) and weight > 0 else 1.0

    return Rule(
        id=rule_id,
        family=family,
        where=where,
        check_kind=check_kind,
        check=check,
        polarity=polarity,
        weight=final_weight if polarity == "soft" else 1.0,
    )


def validation_errors(payload: object) -> list[str]:
    """Every problem with *payload* as a ruleset (empty list = valid)."""

    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"ruleset must be a JSON object, got {type(payload).__name__}"]
    unknown = set(payload) - _RULESET_KEYS
    if unknown:
        errors.append(f"unknown keys {sorted(unknown)} (allowed: {sorted(_RULESET_KEYS)})")
    for key in ("name", "version"):
        if not isinstance(payload.get(key), str) or not payload.get(key, "").strip():
            errors.append(f"{key}: required, a non-empty string")
    rules = payload.get("rules")
    if not isinstance(rules, list) or not rules:
        errors.append("rules: required, a non-empty list")
    else:
        seen: set[str] = set()
        for i, rule_payload in enumerate(rules):
            _parse_rule(rule_payload, i, seen, errors)
    return errors


def parse_ruleset(payload: object) -> Ruleset:
    """Parse and strictly validate a ruleset, collecting **all** errors.

    Raises :class:`RulesetValidationError` carrying the full error list.
    """

    errors = validation_errors(payload)
    if errors:
        raise RulesetValidationError(errors)
    assert isinstance(payload, dict)
    seen: set[str] = set()
    silent: list[str] = []
    rules = tuple(
        rule
        for i, rule_payload in enumerate(payload["rules"])
        if (rule := _parse_rule(rule_payload, i, seen, silent)) is not None
    )
    return Ruleset(
        name=payload["name"],
        version=payload["version"],
        description=str(payload.get("description", "")),
        rules=rules,
    )


__all__ = [
    "FAMILIES",
    "HARMONY_DEPENDENT_FIELDS",
    "Condition",
    "FieldSpec",
    "Rule",
    "Ruleset",
    "RulesetValidationError",
    "parse_ruleset",
    "validation_errors",
]
