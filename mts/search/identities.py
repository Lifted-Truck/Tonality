"""``search_identities`` — exact, exhaustive constraint search over identities.

Enumerates every pitch-class-set identity satisfying a constraint object, over
the whole 4096-mask universe. Default universe is the 223 set classes (prime-form
representatives); ``expand_transpositions=True`` widens to every rooted image.

The constraint object is ``{field: condition}`` where ``field`` is drawn from
:data:`~mts.search.fields.IDENTITY_FIELDS` (scalar: a bare literal for equality,
``{"in": [...]}``, ``{"gte": x}``, or ``{"lte": x}``) or
:data:`~mts.search.fields.STRUCTURAL_FIELDS` (``contains`` / ``contained_in``: a
pitch-class set, matched transpositionally). Conditions AND together. Validation
is **strict and total** — every problem is collected and raised at once, so a
blind agent repairs its query in one round trip (the ruleset-validator contract).
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache

from ..core.bitmask import interval_vector_from_mask, is_subset, pcs_from_mask
from ..core.setclass import chirality_sign, prime_form_mask
from ..core.symmetry import rotational_period
from ..rules.schema import Condition
from .fields import (
    IDENTITY_FIELDS,
    STRUCTURAL_FIELDS,
    ScalarField,
    contained_in_roots,
    contains_roots,
)
from .results import IdentityMatch, IdentitySearchResult

_NUMERIC_OPS = ("gte", "lte")


class SearchConstraintError(ValueError):
    """Every problem with a constraint object, collected. ``errors`` is the list."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("Invalid search constraints:\n- " + "\n- ".join(errors))


@lru_cache(maxsize=1)
def _set_class_masks() -> tuple[int, ...]:
    """Ascending distinct prime-form masks — one representative per set class."""

    return tuple(sorted({prime_form_mask(m) for m in range(1, 4096)}))


def _check_scalar_value(spec: ScalarField, value: object, ctx: str, errors: list[str]) -> None:
    if spec.kind == "bool":
        if not isinstance(value, bool):
            errors.append(f"{ctx}: expected bool, got {type(value).__name__} {value!r}")
    else:  # int
        if isinstance(value, bool) or not isinstance(value, int):
            errors.append(f"{ctx}: expected int, got {type(value).__name__} {value!r}")
        elif spec.values is not None and value not in spec.values:
            errors.append(f"{ctx}: {value!r} is not one of {list(spec.values)}")


def _parse_scalar(field: str, spec: ScalarField, raw: object, errors: list[str]) -> Condition | None:
    ctx = f"{field}"
    if isinstance(raw, dict):
        if len(raw) != 1 or next(iter(raw)) not in ("in", *_NUMERIC_OPS):
            errors.append(f"{ctx}: operator object must have exactly one of ['in', 'gte', 'lte']")
            return None
        op, value = next(iter(raw.items()))
        if op == "in":
            if not isinstance(value, list) or not value:
                errors.append(f"{ctx}.in: must be a non-empty list")
                return None
            for i, entry in enumerate(value):
                _check_scalar_value(spec, entry, f"{ctx}.in[{i}]", errors)
            return Condition(field, "in", tuple(value))
        # gte / lte
        if spec.kind != "int":
            errors.append(f"{ctx}.{op}: field is {spec.kind}, not numeric")
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            errors.append(f"{ctx}.{op}: expected an int, got {value!r}")
            return None
        return Condition(field, op, value)
    _check_scalar_value(spec, raw, ctx, errors)
    return Condition(field, "eq", raw)


def _parse_structural(field: str, raw: object, errors: list[str]) -> int | None:
    if not isinstance(raw, (list, tuple)) or not raw:
        errors.append(f"{field}: must be a non-empty list of pitch classes (0..11)")
        return None
    mask = 0
    for i, pc in enumerate(raw):
        if isinstance(pc, bool) or not isinstance(pc, int) or not 0 <= pc < 12:
            errors.append(f"{field}[{i}]: pitch class must be an int in 0..11, got {pc!r}")
            continue
        mask |= 1 << pc
    return mask


def _validate(constraints: Mapping) -> tuple[list[Condition], dict[str, int], list[str]]:
    errors: list[str] = []
    if not isinstance(constraints, Mapping):
        return [], {}, [f"constraints must be a mapping, got {type(constraints).__name__}"]
    conditions: list[Condition] = []
    structural: dict[str, int] = {}
    for field, raw in constraints.items():
        if field in IDENTITY_FIELDS:
            cond = _parse_scalar(field, IDENTITY_FIELDS[field], raw, errors)
            if cond is not None:
                conditions.append(cond)
        elif field in STRUCTURAL_FIELDS:
            mask = _parse_structural(field, raw, errors)
            if mask:
                structural[field] = mask
        else:
            known = ", ".join(sorted([*IDENTITY_FIELDS, *STRUCTURAL_FIELDS]))
            errors.append(f"{field!r}: unknown field (known: {known})")
    if not conditions and not structural and not errors:
        errors.append("constraints must name at least one field")
    return conditions, structural, errors


def _normalize(conditions: list[Condition], structural: dict[str, int]) -> dict:
    """Echo the applied query as a JSON-clean dict (transparency for the caller)."""

    out: dict = {}
    for c in conditions:
        if c.op == "eq":
            out[c.field] = c.value
        elif c.op == "in":
            out[c.field] = {"in": list(c.value)}  # type: ignore[arg-type]
        else:
            out[c.field] = {c.op: c.value}
    for field, mask in structural.items():
        out[field] = pcs_from_mask(mask)
    return out


def search_identities(
    constraints: Mapping,
    *,
    expand_transpositions: bool = False,
    limit: int | None = None,
) -> IdentitySearchResult:
    """Return every identity satisfying *constraints* (see the module docstring).

    ``expand_transpositions`` widens the default set-class universe to every
    rooted image. ``limit`` caps the *reported* matches (``count`` stays the true
    total; ``truncated`` flags the cut). Raises :class:`SearchConstraintError`
    with the full error list on an invalid constraint object.
    """

    conditions, structural, errors = _validate(constraints)
    if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 0):
        errors.append(f"limit: must be a non-negative int or None, got {limit!r}")
    if errors:
        raise SearchConstraintError(errors)

    contains_q = structural.get("contains")
    contained_q = structural.get("contained_in")
    universe = _set_class_masks() if not expand_transpositions else range(1, 4096)
    # Containment granularity follows universe granularity: set classes fold
    # inversions (a shape and its mirror are one class), rooted masks do not.
    include_inversion = not expand_transpositions

    matches: list[IdentityMatch] = []
    for mask in universe:
        if not all(cond.matches(IDENTITY_FIELDS[cond.field].extract(mask)) for cond in conditions):
            continue
        roots = (
            contains_roots(mask, contains_q, include_inversion=include_inversion)
            if contains_q
            else None
        )
        if contains_q and not roots:
            continue
        if contained_q:
            # The enumerated identity is NEVER transposed. In all_masks it is a
            # literal rooted set, so contained_in is a literal subset test —
            # transposing M while reporting it unchanged returned matches that
            # contradicted their own echo (R1, Wend brief-2: (0,1,3) reported as
            # "⊆ C major" because (4,5,7) fit). In set_classes the identity is a
            # rootless class, so any T/I placement inside the outer set counts.
            if expand_transpositions:
                if not is_subset(mask, contained_q):
                    continue
            elif not contained_in_roots(mask, contained_q, include_inversion=True):
                continue
        matches.append(
            IdentityMatch(
                mask=mask,
                pcs=tuple(pcs_from_mask(mask)),
                cardinality=bin(mask).count("1"),
                interval_vector=interval_vector_from_mask(mask),
                rotational_period=rotational_period(mask),
                is_achiral=chirality_sign(mask) == 0,
                contains_roots=roots,
            )
        )

    matches.sort(key=lambda m: (m.cardinality, m.mask))
    count = len(matches)
    truncated = limit is not None and count > limit
    reported = tuple(matches[:limit]) if limit is not None else tuple(matches)
    return IdentitySearchResult(
        constraints=_normalize(conditions, structural),
        universe="all_masks" if expand_transpositions else "set_classes",
        count=count,
        matches=reported,
        truncated=truncated,
    )


__all__ = ["search_identities", "SearchConstraintError"]
