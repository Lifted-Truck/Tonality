"""Identity field vocabulary for constraint search.

Each **scalar** field extracts one property of a pitch-class-set identity (its
12-bit mask) that a search ``Condition`` (eq / in / gte / lte) can test; each
**structural** field names a set-predicate (``contains`` / ``contained_in``)
evaluated against a caller-supplied pitch-class set. The scalar predicate
machinery is deliberately the ruleset engine's :class:`~mts.rules.schema.Condition`
— a search constraint and a checkable rule are the same predicate pointed in
opposite directions (ROADMAP Phase 4: "build the constraint vocabulary once").

Every property here is a pure, cached function of the mask (the set-class
substrate in :mod:`mts.core.setclass` / :mod:`mts.core.bitmask`), so search is
exact and reproducible over the whole 4096-mask universe.

**Set-class well-definedness.** In the default (prime-form) universe every field
must be a genuine T/I-invariant of the set class. ``is_achiral`` qualifies
(inversional symmetry is T/I-invariant); *signed* chirality does **not** — a
chiral set class folds both handednesses together — so it is deliberately absent
from v1 and belongs to a future register/orientation-aware search.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..core.bitmask import (
    interval_vector_from_mask,
    invert_mask,
    is_subset,
    pcs_from_mask,
    rotate_mask,
)
from ..core.setclass import chirality_sign, dft_magnitudes
from ..core.symmetry import rotational_period


@dataclass(frozen=True)
class ScalarField:
    """A queryable scalar property of an identity mask.

    ``kind`` is the value type a condition is checked against; ``extract`` maps a
    mask to that value; ``values`` (when set) is the closed vocabulary an
    ``eq`` / ``in`` condition must draw from.
    """

    kind: str  # "int" | "bool"
    extract: Callable[[int], object]
    doc: str
    values: tuple | None = None


def _no_consecutive_semitones(mask: int) -> bool:
    """True iff the set's step pattern has no two semitone steps in a row.

    "Consecutive semitones" = a 3-note chromatic run (two adjacent half-step
    steps), the standard scale-construction constraint. This is *not* "no
    semitones at all" — use ``ic1 == 0`` for that. Computed on the circular gap
    sequence of the sorted pitch classes.
    """

    pcs = pcs_from_mask(mask)
    if len(pcs) < 2:
        return True
    gaps = [(pcs[(i + 1) % len(pcs)] - pcs[i]) % 12 for i in range(len(pcs))]
    return not any(gaps[i] == 1 and gaps[(i + 1) % len(gaps)] == 1 for i in range(len(gaps)))


def _ic(index: int) -> Callable[[int], int]:
    return lambda mask: interval_vector_from_mask(mask)[index]


def _df(index: int) -> Callable[[int], float]:
    return lambda mask: dft_magnitudes(mask)[index]


# Interpretive shorthand for the DFT-magnitude fields (|f_k|, from
# core.setclass.dft_magnitudes) — the T/I-invariant interval-content spectrum.
_DF_DOC = {
    1: "chromatic clustering (|f1|)",
    2: "quartal/whole-tone-cluster balance (|f2|)",
    3: "hexatonicity (|f3|)",
    4: "octatonicity (|f4|)",
    5: "diatonicity / fifthiness (|f5|)",
    6: "whole-tone-ness (|f6|)",
}


# The identity field vocabulary. Scalar fields carry an extractor + kind; the two
# structural fields (contains / contained_in) are named here for validation but
# evaluated separately (they take a pc-set argument, not a scalar condition).
IDENTITY_FIELDS: dict[str, ScalarField] = {
    "cardinality": ScalarField(
        "int", lambda m: bin(m).count("1"), "number of pitch classes (1..12)"
    ),
    "ic1": ScalarField("int", _ic(0), "interval-vector entry: semitone (ic1) count"),
    "ic2": ScalarField("int", _ic(1), "interval-vector entry: whole-tone (ic2) count"),
    "ic3": ScalarField("int", _ic(2), "interval-vector entry: minor-third (ic3) count"),
    "ic4": ScalarField("int", _ic(3), "interval-vector entry: major-third (ic4) count"),
    "ic5": ScalarField("int", _ic(4), "interval-vector entry: perfect-fourth (ic5) count"),
    "ic6": ScalarField("int", _ic(5), "interval-vector entry: tritone (ic6) count"),
    "rotational_period": ScalarField(
        "int", rotational_period,
        "smallest transposition mapping the set to itself (12 = no symmetry)",
    ),
    "is_achiral": ScalarField(
        "bool", lambda m: chirality_sign(m) == 0,
        "inversionally symmetric (equal to its own mirror)",
    ),
    "no_consecutive_semitones": ScalarField(
        "bool", _no_consecutive_semitones,
        "no two semitone steps in a row (no 3-note chromatic run)",
    ),
    # DFT-magnitude fields — the interval-content spectrum, T/I-invariant (so
    # genuine set-class fields). Floats: range-queried with gte/lte only (an
    # equality test on an irrational magnitude is a footgun). Full |f1..f6| is
    # also reported on every match as `dft_magnitudes`, so a caller can *rank*
    # by graded diatonicity, not merely filter (A9 Wend's surprise-budget use).
    **{
        f"df{k}": ScalarField("float", _df(k - 1), f"DFT magnitude — {_DF_DOC[k]}")
        for k in range(1, 7)
    },
}

# Structural set-predicate fields: value is a pitch-class set, matched
# transpositionally (see identities.py). Named separately from the scalar
# vocabulary so the validator can route them.
STRUCTURAL_FIELDS: dict[str, str] = {
    "contains": "some transposition of the given pc-set is a subset (reports the roots)",
    "contained_in": "the identity, at some transposition, is a subset of the given pc-set",
}


def contains_roots(
    container_mask: int, query_mask: int, *, include_inversion: bool
) -> tuple[int, ...]:
    """Roots ``t`` at which the query, transposed to ``t``, is a subset of the
    container — i.e. where "the query shape rooted at ``t``" appears in the set.

    The transpositional-containment primitive behind the ``contains`` field.
    (The reverse orientation of :func:`mts.analysis.pcset_math.containing_roots`,
    which transposes the container; here the query moves, the natural reading of
    "scales containing this shape at these roots".)

    ``include_inversion`` — set in the **set-class** universe, where a shape and
    its mirror are the same class — also counts roots at which the query's
    *inversion* fits, so containment is well-defined regardless of which
    handedness Rahn's prime form happens to name (a chiral set class would
    otherwise answer differently for a shape than for its mirror). In the
    rooted ``all_masks`` universe it is off: ``[0,4,7]`` means the major triad,
    not the minor.
    """

    shapes = (query_mask, invert_mask(query_mask)) if include_inversion else (query_mask,)
    return tuple(
        t
        for t in range(12)
        if any(is_subset(rotate_mask(shape, t), container_mask) for shape in shapes)
    )


def contained_in_roots(
    inner_mask: int, outer_mask: int, *, include_inversion: bool
) -> tuple[int, ...]:
    """Roots ``t`` at which the identity (or, when ``include_inversion``, its
    mirror) transposed to ``t`` fits inside the given outer pc-set — the
    ``contained_in`` field's primitive. ``include_inversion`` follows the same
    set-class-vs-rooted rule as :func:`contains_roots`."""

    shapes = (inner_mask, invert_mask(inner_mask)) if include_inversion else (inner_mask,)
    return tuple(
        t
        for t in range(12)
        if any(is_subset(rotate_mask(shape, t), outer_mask) for shape in shapes)
    )


__all__ = [
    "IDENTITY_FIELDS",
    "STRUCTURAL_FIELDS",
    "ScalarField",
    "contains_roots",
    "contained_in_roots",
]
