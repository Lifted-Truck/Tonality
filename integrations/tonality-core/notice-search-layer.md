# NOTICE — Tonality → tonality-core: conformance.json drift (search_identities case added) + new `mts/search/` layer (future slice)

> 2026-07-07, dev loop. Your `tools/refresh_fixtures.sh --check` reports drift
> in `conformance.json` against engine `8122d9b` (current main) and points here.
> **Short version: benign for your current slices — the drift is one new,
> purely-additive tool case; nothing you have ported moved.**

## Cause

Phase 4 landed `search_identities` (constraint search / inverse analysis, PR
#147), and per the harness contract its conformance case was added and the
golden regenerated. The diff is **purely additive**: one new case, `+148 / -0`,
**no existing case changed**. The set-class export table and every currently
**pinned** conformance case are byte-identical — `tests/test_port_pin.py` is
green on our side, so `port/pin.json` did not move.

**Action for you: none required beyond re-baselining the `--check` against
`8122d9b`.** The new `search_identities` case is out of scope for your ported
slices; vendor it only when you take on `search/` (below). If your `--check`
compares the whole `conformance.json`, expect exactly this one added block.

## New layer: `mts/search/` (a future port slice, not an ask)

Registering the shape now so it's not a surprise later — it ports cleanly because
it stands almost entirely on substrate you already have parity on:

- **What it is.** `search_identities(constraints)` — exact, exhaustive
  enumeration over the 4096-mask identity universe ("which set classes satisfy
  these constraints?"). Generative-side, identity-level, register-free.
- **Determinism (all satisfied — port-friendly).** Pure functions of the mask;
  **no RNG, no wall-clock**; output ordered deterministically by
  `(cardinality, mask)`; `count` is the true total independent of any `limit`.
- **Dependencies — mostly already ported.** It reuses the set-class substrate
  from **slice 1**: `interval_vector`, `prime_form_mask` (for the set-class
  universe), `rotational_period`, `chirality_sign` (→ `is_achiral`), plus
  `is_subset` / `rotate_mask` / `invert_mask`. The only genuinely new code to
  port is (a) the scalar predicate primitive — the ruleset engine's `Condition`
  (`eq`/`in`/`gte`/`lte` + `matches`), ~15 lines if `rules/` isn't ported yet;
  (b) the field-extractor table; (c) the enumeration loop + strict-total
  validation.
- **Result schema** (the fixture rows you'd vendor): `IdentitySearchResult` →
  `{constraints, universe, count, truncated, matches[]}`; each match
  `{mask, pcs, cardinality, interval_vector, rotational_period, is_achiral,
  contains_roots}`.

## One semantic you must reproduce exactly (Decision 12)

Containment granularity follows universe granularity, and it is **not** a free
choice — a conformant engine must match it:

- **`universe == "set_classes"` (default):** `contains` / `contained_in` fold
  inversions — a match at transposition `t` counts if the query **or its
  inversion**, rotated to `t`, is a subset. (A set class and its mirror are one
  class, so a rooted test against Rahn's arbitrarily-handed prime form would be
  ill-posed for chiral sets.)
- **`universe == "all_masks"` (`expand_transpositions=True`):** strictly rooted —
  the query only, no inversion (`[0,4,7]` is the major triad, not the minor).

Corollary: signed chirality is deliberately **not** a set-class field (only
`is_achiral`, a true T/I-invariant, is). Full rationale: ROADMAP Decision 12.

## Heads-up on what's next

`search_voicings` (register enumerator, gap 17) is the planned sibling under the
same predicate contract — it will introduce register-dependent fields and is the
first `search/` piece that leaves pure mask space. No timeline pinned; you'll get
a notice when it lands. No response needed to this one unless the `--check`
re-baseline surfaces something unexpected.
