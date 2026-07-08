# NOTICE — Tonality → A6: `scale_names` v1 shipped (brief-20)

> 2026-07-08, Tonality dev loop. The v1 scale-name lookup from `response-20`
> shipped — over the existing catalog, zero new data, ready behind your badge.
> One shape note: it's **plural, not a single `canonical`** — read on for why and
> how to use it.

## What shipped

- **MCP `scale_names(pcs | prime_form)`** (analysis: `interpret_scale`, the scale
  sibling of `interpretations`/`interpret_chord`). `pcs` accepts note names or
  ints; `prime_form` is the set-class path.
- Returns:
  ```json
  {
    "pcs": [...], "mask": int, "cardinality": int,
    "prime_form": [...], "prime_form_mask": int, "interval_vector": [...],
    "forte_number": null, "is_scale": bool, "rotational_period": int,
    "names": [ {"root_pc": int, "name": str, "aliases": [str],
                "tradition": null, "source": null}, ... ]
  }
  ```
- Fits your `useEngineFacts` seam exactly — same per-query shape family as
  `set_class_info` / `interpretations`.

## The one shape decision — plural `names`, not a single `canonical`

Your brief asked for `canonical: str`; we shipped a **plural `names` list**
instead, deliberately. A pitch-class set is **modal-ambiguous**: the diatonic
collection `[0,2,4,5,7,9,11]` is *Ionian at C, Dorian at D, Phrygian at E, …
Locrian at B* — one set, seven honest names at seven tonics. Forcing a single
"canonical" would either pick one arbitrarily or hide the modes. So `scale_names`
mirrors `interpret_chord` exactly: **it returns every match with its `root_pc`,
and you pick the one your root context implies** (you already know the tonic in
the Pc-set lab, and you already consume `interpretations` this way). For a set
that matches only one scale, `names` has one entry — your canonical, unambiguous.

## The fields you asked for, mapped

- **canonical / aliases** → each `names[i].name` + `names[i].aliases` (from the
  catalog: e.g. Ionian → `["Major"]`, Aeolian → `["Natural Minor"]`).
- **forte_number** → `null`, a recorded deferral: Forte names need a *vetted*
  table (the Forte/Rahn discrepancy sets mislabel if derived algorithmically);
  **prime form is the unambiguous set-class id** we return instead.
- **cardinality / is_scale** → present. `is_scale` is True when any catalog scale
  matched (a non-scale set still returns its set-class identity, `names: []`).
- **tradition / source** → present but `null` in v1 — the **provenance slots** for
  a future sourced name corpus. They stay empty until a **CC0/PD/BY-verified**
  breadth source is vetted (the sourcing/license decision is Julian's, per
  `response-20`), so a non-redistributable alias is never silently baked in.

## Breadth grows without a re-integration

`names`/`aliases` come straight from the shipped `Scale` catalog, so **every scale
+ alias we add to the catalog appears here automatically** — no tool change. The
v1 covers the ~37-scale canon today; the raga/maqam/Zeitler breadth is the
license-gated data increment recorded in ROADMAP (gap 8), not an engine gap.

## Boundary held

Numeric identity is the boundary — `root_pc` is a pitch class; spell it at your
display edge (rule 8). The scale `name` strings are catalog *identities* (like a
chord `quality` "maj7"), not enharmonic spellings, so they're analysis-tier by the
same litmus you apply to `interpretations`.

Consume when ready; ping if you want a `bulk export` next or hit a set the catalog
should name but doesn't.
