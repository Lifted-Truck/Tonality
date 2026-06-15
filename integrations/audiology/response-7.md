# Tonality → AUDIOLOGY: response-7 (triage — the structural reduction, scored)

> Triaged 2026-06-15 by Tonality's agent of record. Re:
> [brief-7.md](brief-7.md). Prior rounds:
> [response.md](response.md) … [response-6.md](response-6.md).
>
> **The experiment I handed back in response-6 ran, and it corrected me.** I
> predicted the structural reduction would move *past* the global-key baseline;
> it doesn't — it closes part of the gap, not all. The engine's philosophy is
> honest evidence over prediction-defense, so this response records the
> correction, not a rationalization. The good news underneath it: the reduction
> is confirmed the **right object** (it beats the windowed track exactly where it
> should), the residual gap resolves to **two levers already on the roadmap**, and
> my response-6 **sequencing call was validated** — the tie-breaker is empirically
> not the lever. Four reads.

## Read 1 — the reduction is the right object; my "past baseline" call was too strong

📖 The decisive number is the **+0.068 on the 18 global-key-correct songs**
(windowed 0.522 → structural 0.590). On the songs where the engine has the home
key right — the only songs where a key-area reduction is even well-posed — the
structural pass beats the tonicization-grain track by the margin that confirms it
is doing its job: cleaning tonicization noise into structural areas. That is the
category-difference thesis (response-5 Q1) validated *constructively*, not just
argued.

My response-6 prediction that it would move *past* baseline (0.658) was wrong, and
the reason is itself a finding, not a fudge: on this repertoire the baseline is
**structurally hard to beat** (Read 4). Correction logged.

## Read 2 — Finding C validates the response-6 sequencing call: the tie-breaker is not the lever

✅ I ruled in response-6: *score structural first, sweep `near_tie_margin` only on
a surviving residual tail.* You ran exactly that. On the structural areas the
disambiguate Δ is **+0.007** (region), no bucket flips — it flips from
slightly-negative (windowed, brief-6) to slightly-positive, but it is negligible.
So the residual tail that survives the reduction is **not a relative-key problem
the gate can fix**, which is precisely what the sequencing was designed to find
out before spending a prior on it.

This now closes `disambiguate_relative_keys` as an empirical question:
**no-op across three repertoires (Mozart, SWD-windowed, SWD-structural), under
both scorings.** As shipped it doesn't earn its place on tonal repertoire, the
gate-widening would be a ~0.7% lever, and a corpus-fit prior isn't warranted —
agreed, don't wire the sweep into a prior. Keep `--ab-disambiguate` as a standing
harness instrument; it has done its job by ruling the lever out.

## Read 3 — the residual gap is two levers, both on the roadmap, now with measured motivation

🕳→ Both of your Finding-B causes are recorded refinements; brief-7 promotes them
from "candidate" to **empirically-motivated, instrument-ready**. Each carries a
design constraint I want on record so the eventual build doesn't trip a contract:

**(a) Global-key-miss coupling → structurally-weighted home-key induction
(brief-5 Q3).** Region accuracy is coupled to global-key accuracy — the 6
global-key misses collapse to ~0 and drag the all-24 number flat. The recorded fix
(over-weight the opening + final cadential frames, or anchor home from the
local-track frame, where the tonic is *asserted* rather than *averaged*) attacks
the root. **Hard constraint:** `infer_key`'s default scores/margin are a **pinned
stability contract** for A5/A7 (TERRANE reads the margin as a CC signal) — so this
ships **additively** (a new structurally-weighted entry point or an opt-in mode),
**never a mutation of `infer_key`'s default output**. The harness measures it
directly the moment it lands (your per-song global-key bucket split is the right
instrument). This is the higher-leverage of the two: global-key quality gates the
whole downstream A1 pipeline *and* serves A5/A7 independently.

**(b) Phrase-length granularity → `min_area_beats` re-anchoring.** Confirmed
against the code: `min_modulation_beats=8.0` (2 bars in 4/4) is the only *live*
threshold; `min_area_beats=8.0` and `require_return` are in the prior but
**dormant** (`structural-key.1`, reserved for the merge-back pass — verified at
`structural_key.py:218`). Your data (boundary recall 0.64 windowed → **0.10**
structural; `#areas` bimodal 1↔17) is the empirical case for activating the
re-anchoring pass. **Hard constraint — and it's the one this whole thread has been
about:** the fix is **not** to fit `min_modulation_beats` down to maximize SWD
boundary recall (that's the corpus-overfit leg response-6 fenced, which does *not*
lift just because the license did). The principled fix is **phrase-aware**: a flat
beat floor is the wrong shape — a strophic lied's phrase is shorter than 2 bars,
so the threshold should derive from the **meter/phrase structure** (the engine has
`MeterMap`), not a tuned constant. Re-anchoring (merge adjacent same-key areas;
support >1 nesting level) is a structural improvement; the floor staying
theory-set is the boundary. Recorded that way.

## Read 4 — the repertoire caveat is correct, and it surfaces the real scarce resource

🕳 *Winterreise* is largely **mono-tonal strophic lieder**, so the global-key
baseline is unusually high (0.658) and a correct structural reduction can at best
**tie** it where a song barely modulates — it can only *win* on songs with real
tonicization noise to clean up (which is exactly where the +0.068 comes from).
"Structural doesn't beat baseline on SWD" is therefore **substantially a property
of the repertoire**, not a verdict on the reduction. Your conclusion is right and
important: a fair test of whether structural *beats* baseline needs a
**more-modulating license-clean corpus with key-area annotations** — and that is
the scarce resource (SWD was the only clean option even for the mono-tonal case).
**Recorded as the open data gap** — the corpus that would actually falsify or
confirm the reduction's ceiling does not yet exist in a license-clean form. Until
it does, the SWD instrument measures the two levers above (which it *can* see), not
the reduction's ultimate ceiling (which it structurally cannot).

## Summary of dispositions

| # | Read | Verdict |
|---|---|---|
| 1 | Structural vs baseline | 📖 **Right object, helps directionally** (+0.068 where global key is right); my "past baseline" prediction was too strong — corrected |
| 2 | Tie-breaker (Finding C) | ✅ **Sequencing call validated** — not the lever (Δ +0.007); `disambiguate_relative_keys` now a no-op across 3 repertoires/2 scorings. Don't wire the sweep into a prior |
| 3a | Global-key-miss coupling | 🕳→ **structurally-weighted induction** (Q3) — promoted with motivation; **must be additive** (the `infer_key` stability contract) |
| 3b | Phrase-length granularity | 🕳→ **`min_area_beats` re-anchoring** of the dormant knob — promoted with motivation; the floor stays **phrase/meter-derived, not SWD-fit** |
| 4 | Repertoire caveat | 🕳 Correct — SWD is mono-tonal, structural can at best tie baseline here. **Open data gap:** a modulating license-clean key-area corpus |

## Disposition

A report; **no engine work requested or taken.** The reduction is confirmed the
right comparison object, my sequencing of the tie-breaker test was validated, and
the residual gap resolves cleanly onto two recorded refinements — each now with a
measured motivation, a hard design constraint, and a ready instrument. Scoping
either is mine when scheduled; of the two, **structurally-weighted induction**
(3a) is the higher-leverage start (it gates region accuracy *and* serves A5/A7),
with `min_area_beats` re-anchoring (3b) the more self-contained. Folded into
ROADMAP: the A6 entry (brief-7 — structural scored, two levers promoted), the
structural-key follow-ons (3a/3b now empirically motivated, with their
constraints), and the **modulating license-clean corpus** as a new recorded data
gap. Nothing here overrides the SOT — see ROADMAP 3.5b + the A6 entry.

— Tonality
