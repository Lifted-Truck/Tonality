# mts/search — Constraint search (inverse analysis)

The *inverse* of `analysis/`: instead of "what is this set?", answer "which sets
satisfy these constraints?" by exact, exhaustive enumeration over the 4096-mask
identity universe (ROADMAP Phase 4, the marquee agent-facing tool).

**Generative-side, by the cardinal rule.** A search constraint and a checkable
rule are the same predicate pointed in opposite directions, so the scalar
predicate machinery *is* the ruleset engine's `Condition` (eq/in/gte/lte),
reused over an **identity** field vocabulary — this layer sits above `analysis/`
and `rules/` and never reimplements either.

- `fields.py` — `IDENTITY_FIELDS` (scalar extractors over the `core.setclass` /
  `core.bitmask` substrate: cardinality, ic1..ic6, rotational_period,
  is_achiral, no_consecutive_semitones) + the structural `contains` /
  `contained_in` predicates. Every field is a pure, cached mask function.
- `identities.py` — `search_identities(constraints)`: strict-total validation
  (the blind-agent ruleset contract — collect *all* errors), enumeration,
  typed result. Default universe is the 223 set classes; `expand_transpositions`
  widens to every rooted image.
- `results.py` — `IdentitySearchResult` / `IdentityMatch` (`to_dict()`).

**Decision 12 (containment granularity) — read before adding fields.** In the
set-class universe, `contains`/`contained_in` fold inversions (a shape and its
mirror are one class); in `all_masks` they are strictly rooted. Every field must
be a genuine invariant of the universe it is queried in — which is why *signed*
chirality is **not** a set-class field (only `is_achiral` is). Handedness- and
register-sensitive search belongs to the planned `search_voicings` slice.

Plans live in [ROADMAP.md](../../ROADMAP.md) (Phase 4) — link phases here; don't
record plans in this file.
