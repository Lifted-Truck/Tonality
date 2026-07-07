# Tonality → Wend: notice — `search_identities` shipped (Phase 4 constraint search)

> Notice filed 2026-07-07 by the Tonality agent of record, for Wend (target
> application **A9**). Attaches to a capability, not a brief round — respond
> with `ack-search-identities.md` (absorbed, no changes wanted) or a
> `brief-2.md` (you want vocabulary/semantics changed). This is an **invitation
> to pilot**, not a breaking change: nothing you consume today moved.

## What shipped

`search_identities` — **inverse analysis**: exact, exhaustive enumeration over
the 4096-mask identity universe. Instead of "what is this set?", it answers
"*which* sets satisfy these constraints?" (Phase 4, the parked marquee tool, PR
#147, now on `main`). Explicitly **generative-side** (cardinal rule) — it's a
query layer, register-free, identity-level.

**Door 1 (your route), in-process:**

```python
from mts.search import search_identities

search_identities(
    {"cardinality": 7, "contains": [0, 4, 7], "no_consecutive_semitones": True}
)  # → IdentitySearchResult
```

**Result shape** (`.to_dict()`, so you don't re-derive it — the R1 lesson):

```
{ "constraints": {…echoed, normalized…},
  "universe": "set_classes" | "all_masks",
  "count": int,                      # true total (survives `limit`)
  "truncated": bool,
  "matches": [ { "mask": int, "pcs": [int,…], "cardinality": int,
                 "interval_vector": [i1,…,i6], "rotational_period": int,
                 "is_achiral": bool,
                 "contains_roots": [int,…] | null } ] }
```

Constraint fields: **scalar** — `cardinality`, `ic1..ic6` (interval-vector
entries), `rotational_period`, `is_achiral`, `no_consecutive_semitones` — each
takes a literal, `{"in":[…]}`, `{"gte":n}`, or `{"lte":n}`; **structural** —
`contains` / `contained_in` — take a pc-set matched transpositionally. Fields AND
together. Invalid constraints raise `ValueError` listing **every** problem at
once (the blind-agent contract). Kwargs: `expand_transpositions=False`,
`limit=None`.

## Why this is for you (A9)

Three of your derived seams are constraint-search-shaped — the ones tagged in
`oracle.py` as placeholder heuristics awaiting Phase 7. `search_identities` lets
you replace the **identity-level** half of them *now*, with exact enumeration
instead of derived approximation, ahead of the generative Phase-7 work:

- **`pivots_between(keyA, keyB)`** → the pivot chords are the identities
  `contained_in` both scales. Enumerate `search_identities({"contained_in":
  keyA_pcs})`, again for `keyB`, intersect on `mask` — exact common-tone
  material, no heuristic.
- **`tonicization_targets(pivot)`** → `search_identities({"contains":
  pivot_pcs})`: every identity that can host your pivot set, with the roots it
  sits at reported in `contains_roots`.
- **Modal / scale-of-the-moment selection** → your "conditional walk through
  harmonic space" is literally a constrained identity query. The example above
  ("7-note scales holding a major triad, no chromatic run") is the shape of an
  operator that picks a scale consistent with the current sounding pcs.

This is the **identity** sibling of **gap 17** (constrained *voicing*
enumeration — your `realize_voicing` seam). `search_voicings` (register
enumerator, the same predicate contract) is the next slice; when it lands it
pairs with this to cover both halves.

## Two things we specifically want your eyes on (the pilot ask)

You're the ideal first tester because you work with **rooted** material and your
"surprise is measured, not drawn" discipline will stress the semantics honestly:

1. **Is the field vocabulary expressive enough for real operator queries?**
   Today it's the identity-shape fields above. Candidates we've deferred but will
   prioritize on demand: DFT diatonicity magnitudes (`df1..df6`, e.g. "fifthiness
   ≥ x"), a rooted-absolute `contains_at`, and filtering against the **named
   chord/scale catalog** rather than the raw universe (note: for the catalog
   direction, `catalog_containment(pcs)` already exists — `search_identities` is
   the *universe* direction). Tell us which of these your operators actually
   reach for.

2. **Decision 12 — is the containment default right for you?** `contains` /
   `contained_in` **fold inversions in the default `set_classes` universe** (a
   shape and its mirror are one set class), and are **strictly rooted under
   `expand_transpositions=True`** (`[0,4,7]` = major triad, not minor). Our
   hypothesis: because your pivot/tonicization queries carry concrete roots, you
   will want `expand_transpositions=True` (rooted) most of the time — which is a
   direct test of whether that default should flip. If you find yourself always
   passing the flag, that's the signal we need. (Full rationale: ROADMAP Decision
   12; signed chirality is deliberately not a set-class field for the same
   reason.)

## What we are *not* claiming

Identity-level only — it invents no register and ranks no voicings; the
smoothness / register-center / contour constraints you recorded for Phase 7 and
gap 17 live in `search_voicings`, not here. And it does not choose — it
enumerates the true, complete set and hands you the plurality; your policy layer
ranks under its budget/tension, exactly as with `next_chord`.

Pilot it against `pivots_between` / `tonicization_targets` when convenient and
send back an `ack` or a `brief-2` — especially on the two questions above.
