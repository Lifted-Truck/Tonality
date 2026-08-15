---
id: audiology-unmatched-naming
from: Tonality
to: Audiology (A6)
status: filed
ball: consumer (adopt at leisure — additive, nothing breaks)
filed: 2026-08-15
---

> **Origin:** Tonality resident session, 2026-08-15, from Julian's report out
> of a live Audiology session: played chords with "no suggested analyses".
> Motivating decision: ROADMAP gap 33 (delivered same date). Authored by an
> agent; the human merges.

# Notice: naming no longer goes silent — `unmatched` on the no-match path

## What you saw, and why

F-C-G♯-B, D-E-F, D-A-F-G♯ all returned `{chosen: null, alternatives: []}`,
and your UI honestly rendered nothing. Half of that was correct: none of
those is a registered chord quality (65 tertian/common shapes; D-E-F is a
cluster), and the namer refuses to invent — that part stands. The bug was the
**empty shell**: this engine can never truly have "no known identity" — every
pc set has a set-class identity, quality subsets, near-misses, and containing
scales — and none of it was reaching the naming result.

## What the same calls return now

`name_pcs` (and every `ChordNaming` payload) carries `unmatched`, populated
**only when `chosen` is null** — so your existing rendering of matched chords
is untouched, and the field is `null` there. For F-C-G♯-B it contains:

- `prime_form: [0,1,4,7]`, `normal_order`, `interval_vector` — and note your
  first and third reported chords are the **same set class**; the surface can
  now say so.
- `quality_subsets` (maximal, aliases collapsed): **F dim + added C** ·
  **F min + added B** — the "suggested analyses" you expected, with the
  unexplained tones flagged per reading.
- `near_qualities` (one pc-swap away; capped at 12 with the TRUE total in
  `near_quality_count`; roots the player actually struck sort first):
  F dim7, F min6, F min7, …, each carrying `swap_from_pc`/`swap_to_pc`.
- `containing_scales` (tightest first; capped at 8, total alongside):
  **F Minor Blues** leads — arguably the natural hearing of that voicing.

D-E-F shows the honest cluster case: `quality_subsets` is empty (no triad
lives inside [0,1,3]) but near-misses (D dim / D min / D sus2, one swap away)
and containing scales (Hirajoshi, In-Sen, …) still populate.

## Rendering suggestions, take or leave

The distinction worth preserving in the UI: `quality_subsets` are *partial
readings of what was played* ("this contains an F dim triad, plus a C");
`near_qualities` are *what it almost is* ("one note away from F min7"). The
two answer different user questions, and the swap fields let you render the
near-miss as an actionable diff. `is_ambiguous` semantics are unchanged;
counts are true totals so a "show all N" affordance is safe.

Contract notes: additive only — no existing field changed, no signature
changed. The capped lists follow our no-silent-caps discipline (totals always
ride along). Your bridge needs no changes; the field flows through `to_dict`.

Ball: consumer, at leisure — nothing breaks if you ignore it; your
"no suggested analyses" state just has strictly more to say now.
