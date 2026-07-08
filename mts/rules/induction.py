"""Ruleset induction: mine a corpus for the rules it follows (Phase 4.6).

**Version-space mining, not learning** (Decision 8): exact, interpretable,
no ML. Given a corpus of sequences, discover the statistically significant
compositional rules the corpus obeys and emit them in the engine's existing
ruleset DSL — closing the extract/impose/compare loop (the caller proposes
rules via the DSL; the engine *induces* them too, and verifies either way).

Slice 1 pipeline (per atom family, over the **categorical / bool / low-card-int**
fields — the idiom-bearing ones):

1. **Transactions.** Each atom item (from the evaluator's per-family streams) →
   a frozenset of ``(field, value)`` literals over the mineable fields. A
   ``None`` field contributes no literal (mirrors the evaluator's "no claim").
2. **Apriori over the `where`-lattice** (closed, arity-capped). Frequency is
   **piece-presence** support — the honest unit (one piece can't manufacture
   frequency). Anti-monotonic pruning + a same-field guard; closed-itemset
   condensation collapses the redundant `C / C∧L` fan.
3. **Rule formation + Fisher's exact.** For a closed context C and a frequent
   consequent literal L, a 2×2 contingency over items *carrying a claim on L's
   field*; ``leverage``'s sign picks ``require`` (positive association) vs
   ``forbid`` (negative); a **one-sided Fisher's exact test** (exact rational
   arithmetic, no SciPy) scores it against an independence-given-marginals null.
4. **BH-FDR** over the realized search space; only significant survivors emit.

Output is a **validated soft `Ruleset`** (induced regularities carry a false-
discovery rate — they are preferences, not axioms) plus a per-rule evidence
sidecar (support, confidence, leverage, p/q). Everything is deterministic
(canonical ordering throughout) and reproducible (the scoring config is a
versioned prior cited in the result). Honest bound: below the prior's
``exploratory_floor_pieces`` the result is flagged ``exploratory``.

Deferred (recorded, ROADMAP 4.6): float-field bucketing + high-card ints; the
disjunction/exception merge pass; S/G generality labeling; MDL rule-set scoring;
cross-family / phrase / global scope; hard-rule promotion.
"""

from __future__ import annotations

import dataclasses
import math
from collections import defaultdict
from collections.abc import Iterable, Sequence as SequenceABC
from dataclasses import dataclass
from fractions import Fraction

from ..temporal import Sequence
from .evaluator import _build_stream
from .schema import (
    FAMILIES,
    Condition,
    Rule,
    Ruleset,
    ruleset_to_payload,
    validation_errors,
)

# Bounded low-cardinality int fields worth mining as eq-literals (0..11 domains).
# Everything else int/float is an explosion vector and is excluded; its
# idiom-bearing projection (approach_class, interval_class) is already a field.
_BOUNDED_INT_FIELDS = {
    "voice_motion": {"interval_class_from", "interval_class_to"},
    "melody": {"pc"},
    "rhythm": set(),
}

Literal = tuple[str, object]  # (field, value)


def _mineable_fields(family: str) -> list[str]:
    fields = []
    for name, spec in FAMILIES[family].items():
        if spec.kind == "bool" or (spec.kind == "str" and spec.values is not None):
            fields.append(name)
        elif spec.kind == "int" and name in _BOUNDED_INT_FIELDS.get(family, set()):
            fields.append(name)
    return fields


def _value_rank(family: str, field: str, value: object) -> object:
    spec = FAMILIES[family][field]
    if spec.kind == "str" and spec.values is not None:
        return spec.values.index(value)
    if spec.kind == "bool":
        return int(value)  # type: ignore[arg-type]
    return value


def _lit_key(family: str, literal: Literal) -> tuple:
    field, value = literal
    return (field, _value_rank(family, field, value))


def _itemset_key(family: str, itemset: frozenset[Literal]) -> tuple:
    return tuple(_lit_key(family, lit) for lit in sorted(itemset, key=lambda l: _lit_key(family, l)))


# --- Fisher's exact (one-sided, exact rational) -----------------------------------------


def _fisher_one_sided(a: int, b: int, c: int, d: int, *, right_tail: bool) -> float:
    """One-sided Fisher's exact p for a 2x2 table with fixed margins.

    ``right_tail`` sums P(i) for i >= a (enrichment, the require direction);
    otherwise i <= a (depletion, the forbid direction). Exact via the
    hypergeometric recurrence in :class:`~fractions.Fraction`; ``math.comb`` seeds
    one point only, so there is no factorial/bignum blow-up.
    """

    n = a + b + c + d
    row1, col1 = a + b, a + c
    lo = max(0, col1 - (c + d))
    hi = min(row1, col1)
    # Seed at i = lo, then walk the recurrence P(i+1)/P(i).
    p_lo = Fraction(math.comb(row1, lo) * math.comb(c + d, col1 - lo), math.comb(n, col1))
    probs: dict[int, Fraction] = {lo: p_lo}
    current = p_lo
    for i in range(lo, hi):
        # P(i+1) = P(i) * (row1 - i)(col1 - i) / [(i+1)(c+d - col1 + i + 1)]
        current = current * Fraction((row1 - i) * (col1 - i), (i + 1) * (c + d - col1 + i + 1))
        probs[i + 1] = current
    if right_tail:
        tail = sum((probs[i] for i in range(a, hi + 1)), Fraction(0))
    else:
        tail = sum((probs[i] for i in range(lo, a + 1)), Fraction(0))
    return float(min(tail, Fraction(1)))


def _bh_qvalues(pvalues: list[float]) -> list[float]:
    """Benjamini–Hochberg adjusted q-values, aligned to the input order.

    Standard step-up: sort ascending, ``q = min over j>=rank of (m/j · p_j)``
    via a right-to-left running minimum, clamped to ≤ 1.
    """

    m = len(pvalues)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: (pvalues[i], i))
    q = [1.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        idx = order[rank - 1]
        running = min(running, pvalues[idx] * m / rank)
        q[idx] = min(running, 1.0)
    return q


# --- result types -----------------------------------------------------------------------


@dataclass(frozen=True)
class RuleEvidence:
    """The statistical evidence behind one induced rule (Decision 7)."""

    rule_id: str
    where: dict
    check_kind: str            # "forbid" | "require"
    check: dict
    support_pieces: int
    support_items: int         # a — items matching where AND check
    items_considered: int      # N — items carrying a claim on the check field
    context_items: int         # a+b — items matching where (within the claim universe)
    confidence: float          # P(L|C)
    base_rate: float           # P(L)
    leverage: float
    contingency: dict          # {a, b, c, d, n}
    p_value: float
    q_value: float
    significant: bool
    merged: bool = False       # a disjunction (`in`) of merged single-value rules

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class InductionResult:
    """Induced soft ruleset + per-rule evidence (Phase 4.6, slice 1)."""

    family: str
    ruleset: Ruleset
    evidence: list[RuleEvidence]
    scoring_prior: dict
    tests_performed: int       # m — realized search-space size (BH correction factor)
    pieces: int
    items: int
    exploratory: bool
    caveat: str | None

    def to_dict(self) -> dict:
        return {
            "family": self.family,
            "ruleset": ruleset_to_payload(self.ruleset),
            "evidence": [e.to_dict() for e in self.evidence],
            "scoring_prior": self.scoring_prior,
            "tests_performed": self.tests_performed,
            "pieces": self.pieces,
            "items": self.items,
            "exploratory": self.exploratory,
            "caveat": self.caveat,
        }


# --- the pipeline -----------------------------------------------------------------------


def _build_transactions(
    sequences: list[Sequence], family: str, harmony: list | None
) -> tuple[list[frozenset[Literal]], list[int]]:
    """Per-item literal sets + the piece index each item came from."""

    fields = _mineable_fields(family)
    transactions: list[frozenset[Literal]] = []
    piece_of: list[int] = []
    for p, sequence in enumerate(sequences):
        spans = harmony[p] if harmony is not None else None
        stream = _build_stream(family, sequence, spans)
        for item, _location in stream.items:
            literals = {
                (f, getattr(item, f))
                for f in fields
                if getattr(item, f) is not None
            }
            transactions.append(frozenset(literals))
            piece_of.append(p)
    return transactions, piece_of


def induce_ruleset(
    sequences: Iterable[Sequence],
    *,
    family: str,
    harmony: list | None = None,
    scoring_prior: str | None = None,
    merge_disjunctions: bool = True,
    name: str | None = None,
    version: str = "induced.1",
) -> InductionResult:
    """Induce a soft ruleset from *sequences* for one atom ``family``.

    ``family`` is ``"voice_motion"`` / ``"melody"`` / ``"rhythm"``. ``harmony``,
    when given, is a per-sequence list of ``(start, end, pcs)`` span lists (only
    melody's ``nht_type`` / ``is_chord_tone`` consult it). Raises on an unknown
    family. Below the prior's ``exploratory_floor_pieces`` the result is flagged
    ``exploratory`` but still returned (surfaced, never hidden).

    ``merge_disjunctions`` (default on): collapse same-``(where, kind, field)``
    single-value rules into one ``in``-rule (``forbid ic in {0, 7}`` rather than
    two forbids), re-tested with Fisher's exact so rigor is preserved — the
    human-readable form. Set ``False`` for the raw single-value rules.
    """

    if family not in FAMILIES:
        known = ", ".join(sorted(FAMILIES))
        raise ValueError(f"Unknown family {family!r} (known: {known}).")
    if family == "harmony":
        # gap B slice 1 ships harmony *evaluation*; mining it needs a chord-stream
        # corpus interface (harmony atoms come from chords+key, not the note
        # Sequence this induction consumes) — the recorded slice-1b follow-on.
        raise ValueError(
            "harmony-family induction is not yet supported: harmony atoms derive "
            "from an explicit chord stream + key, not the note Sequence corpus this "
            "miner reads (gap B slice-1b — the chord-stream corpus interface)."
        )

    from ..io.loaders import load_scoring_prior

    prior = load_scoring_prior(scoring_prior)
    sequences = list(sequences)
    name = name or f"induced-{family}"

    transactions, piece_of = _build_transactions(sequences, family, harmony)
    n_tx = len(transactions)

    # Vertical (tidset) index: transaction indices containing each literal, and
    # the transactions carrying *any* claim on each field.
    tids: dict[Literal, set[int]] = {}
    claim_tids: dict[str, set[int]] = {}
    for t, literals in enumerate(transactions):
        for lit in literals:
            tids.setdefault(lit, set()).add(t)
            claim_tids.setdefault(lit[0], set()).add(t)

    def pieces_of(tidset: set[int]) -> int:
        return len({piece_of[t] for t in tidset})

    # --- Apriori over the where-lattice (piece-support floor) ---
    floor = prior.min_support_pieces
    # L1: frequent single literals.
    l1: dict[frozenset[Literal], set[int]] = {}
    for lit, tidset in tids.items():
        if pieces_of(tidset) >= floor:
            l1[frozenset({lit})] = tidset
    levels: list[dict[frozenset[Literal], set[int]]] = [l1]
    for _k in range(2, prior.arity_cap + 1):
        prev = levels[-1]
        prev_sets = list(prev)
        candidates: dict[frozenset[Literal], set[int]] = {}
        for i in range(len(prev_sets)):
            for j in range(i + 1, len(prev_sets)):
                union = prev_sets[i] | prev_sets[j]
                if len(union) != _k:
                    continue
                if len({f for f, _ in union}) != _k:
                    continue  # two literals on one field — never co-occur
                if union in candidates:
                    continue
                if any(frozenset(union - {lit}) not in prev for lit in union):
                    continue  # anti-monotone prune
                tidset = set.intersection(*(tids[lit] for lit in union))
                if pieces_of(tidset) >= floor:
                    candidates[union] = tidset
        if not candidates:
            break
        levels.append(candidates)

    frequent: dict[frozenset[Literal], set[int]] = {}
    for level in levels:
        frequent.update(level)

    # --- closed condensation: drop P if a superset has equal (pieces, items) ---
    def closed(P: frozenset[Literal]) -> bool:
        sp, si = pieces_of(frequent[P]), len(frequent[P])
        for Q, qtids in frequent.items():
            if len(Q) > len(P) and P < Q and len(qtids) == si and pieces_of(qtids) == sp:
                return False
        return True

    contexts = [P for P in frequent if closed(P)]

    # --- rule formation + Fisher's exact, over frequent consequent literals ---
    consequents = [next(iter(s)) for s in l1]  # the frequent single literals
    raw: list[dict] = []
    for context in contexts:
        ctx_fields = {f for f, _ in context}
        ctx_tids = frequent[context]
        for lit in consequents:
            field_l, _val = lit
            if field_l in ctx_fields:
                continue
            universe = claim_tids[field_l]
            n = len(universe)
            if n == 0:
                continue
            l_tids = tids[lit]
            a = len(ctx_tids & l_tids)
            a_b = len(ctx_tids & universe)
            a_c = len(l_tids)  # l_tids ⊆ universe by construction
            if a_b == 0:
                continue
            b = a_b - a
            c = a_c - a
            d = n - a - b - c
            leverage = float(Fraction(a, n) - Fraction(a_b, n) * Fraction(a_c, n))
            if leverage == 0.0:
                continue
            right_tail = leverage > 0
            p = _fisher_one_sided(a, b, c, d, right_tail=right_tail)
            raw.append({
                "context": context, "lit": lit, "a": a, "b": b, "c": c, "d": d, "n": n,
                "a_b": a_b, "a_c": a_c, "leverage": leverage, "p": p,
                "check_kind": "require" if right_tail else "forbid",
                "support_pieces": pieces_of(ctx_tids & l_tids),
            })

    # --- BH-FDR over the realized search space ---
    m = len(raw)
    qvalues = _bh_qvalues([r["p"] for r in raw])
    for i in range(m):
        raw[i]["q"] = qvalues[i]
        raw[i]["significant"] = qvalues[i] <= prior.fdr_q

    survivors = [r for r in raw if r["significant"]]

    # --- disjunction (`in`) merge pass: collapse same-(context, kind, field)
    # single-value rules into one `in`-rule, re-tested with Fisher so rigor is
    # preserved (pooling already-significant findings; never re-FDR'd, never
    # pooling a non-significant value in to rescue a borderline one). ---
    def _record(field, values, kind, context, cells, lev, p, q, merged):
        a, b, c, d, n_, a_b, a_c = cells
        vtids = set().union(*(tids[(field, v)] for v in values))
        return {
            "context": context, "check_kind": kind, "field": field,
            "values": tuple(values), "merged": merged,
            "a": a, "b": b, "c": c, "d": d, "n": n_, "a_b": a_b, "a_c": a_c,
            "leverage": lev, "p": p, "q": q,
            "support_pieces": pieces_of(frequent[context] & vtids),
        }

    def _singleton(r):
        cells = (r["a"], r["b"], r["c"], r["d"], r["n"], r["a_b"], r["a_c"])
        return _record(r["lit"][0], (r["lit"][1],), r["check_kind"], r["context"],
                       cells, r["leverage"], r["p"], r["q"], False)

    records: list[dict] = []
    if merge_disjunctions:
        groups: dict = defaultdict(list)
        for r in survivors:
            groups[(r["context"], r["check_kind"], r["lit"][0])].append(r)
        for (context, kind, field), members in groups.items():
            if len(members) < 2:
                records.append(_singleton(members[0]))
                continue
            values = sorted({m["lit"][1] for m in members},
                            key=lambda v: _value_rank(family, field, v))
            ctx_tids, universe = frequent[context], claim_tids[field]
            merged_tids = set().union(*(tids[(field, v)] for v in values))
            n_, a_b, a_c = len(universe), len(ctx_tids & universe), len(merged_tids)
            a = len(ctx_tids & merged_tids)
            b, c = a_b - a, a_c - a
            d = n_ - a - b - c
            lev = float(Fraction(a, n_) - Fraction(a_b, n_) * Fraction(a_c, n_))
            right_tail = kind == "require"
            if lev == 0.0 or (lev > 0) != right_tail:
                records.extend(_singleton(m) for m in members)
                continue
            p = _fisher_one_sided(a, b, c, d, right_tail=right_tail)
            # RE-3d: the merged rule must be at least as significant as the
            # weakest member it replaces (matching the q assigned below).
            # Comparing raw p against the FDR q-threshold was *more lenient*
            # than the singleton test (a member's p ≤ its q ≤ fdr_q).
            if p > max(m["p"] for m in members):
                records.extend(_singleton(m) for m in members)
                continue
            q = max(m["q"] for m in members)  # ≥ as significant as the weakest replaced
            records.append(_record(field, values, kind, context,
                                   (a, b, c, d, n_, a_b, a_c), lev, p, q, True))
    else:
        records = [_singleton(r) for r in survivors]

    records.sort(key=lambda r: (-abs(r["leverage"]), r["q"], _itemset_key(family, r["context"]),
                                _lit_key(family, (r["field"], r["values"][0]))))

    rules: list[Rule] = []
    evidence: list[RuleEvidence] = []
    for n_idx, r in enumerate(records):
        rule_id = f"induced-{family}-{n_idx}"
        where = tuple(
            Condition(f, "eq", v)
            for f, v in sorted(r["context"], key=lambda l: _lit_key(family, l))
        )
        if r["merged"]:
            check = (Condition(r["field"], "in", tuple(r["values"])),)
            check_payload = {r["field"]: {"in": list(r["values"])}}
        else:
            check = (Condition(r["field"], "eq", r["values"][0]),)
            check_payload = {r["field"]: r["values"][0]}
        weight = round(1.0 + prior.weight_scale * abs(r["leverage"]), 3)
        rules.append(Rule(
            id=rule_id, family=family, where=where, check_kind=r["check_kind"],
            check=check, polarity="soft", weight=weight,
        ))
        evidence.append(RuleEvidence(
            rule_id=rule_id,
            where={f: v for f, v in sorted(r["context"], key=lambda l: _lit_key(family, l))},
            check_kind=r["check_kind"],
            check=check_payload,
            support_pieces=r["support_pieces"],
            support_items=r["a"],
            items_considered=r["n"],
            context_items=r["a_b"],
            confidence=round(r["a"] / r["a_b"], 6),
            base_rate=round(r["a_c"] / r["n"], 6),
            leverage=round(r["leverage"], 6),
            contingency={"a": r["a"], "b": r["b"], "c": r["c"], "d": r["d"], "n": r["n"]},
            p_value=r["p"],
            q_value=round(r["q"], 6),
            significant=True,
            merged=r["merged"],
        ))

    ruleset = Ruleset(name=name, version=version, description=(
        f"Induced from {len(sequences)} piece(s) over the {family} family "
        f"({prior.version}; soft rules, Fisher's exact + BH-FDR q={prior.fdr_q})."
    ), rules=tuple(rules))
    # Valid by construction when non-empty; an empty result (no significant
    # rules) is a legitimate outcome but not a usable DSL ruleset (the schema
    # requires ≥1 rule), so we only assert validity when rules were emitted.
    if rules:
        errors = validation_errors(ruleset_to_payload(ruleset))
        assert not errors, f"induced ruleset is invalid: {errors}"

    exploratory = len(sequences) < prior.exploratory_floor_pieces
    caveat = (
        f"Exploratory: {len(sequences)} piece(s) is below the "
        f"{prior.exploratory_floor_pieces}-piece floor for confirmatory induction; "
        "treat rules as hypotheses (Fisher has little power on a handful of pieces)."
    ) if exploratory else None

    return InductionResult(
        family=family,
        ruleset=ruleset,
        evidence=evidence,
        scoring_prior=dataclasses.asdict(prior),
        tests_performed=m,
        pieces=len(sequences),
        items=n_tx,
        exploratory=exploratory,
        caveat=caveat,
    )


__all__ = ["induce_ruleset", "InductionResult", "RuleEvidence"]
