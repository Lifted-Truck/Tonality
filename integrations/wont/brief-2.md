# wont → Tonality: brief-2 — per-run pooling meets the principal client (parallel scoped sessions)

> **DRAFT — prepared 2026-07-08 by the wont agent for Julian's review; NOT yet
> filed/committed.** A follow-up to **response §4** ("span independence: the
> recipe is per-run pooling") and the Markov-alignment notice, which reconfirmed
> `pieces = runs` in its glossary. We adopted that ruling — and binding it to
> wont's principal client, **Wend**, surfaced one case §4 could not have
> anticipated: Wend produces **multiple labelings of a single `run_id`**. This
> brief asks how `pieces = runs` extends there. Nothing is owed urgently — the
> learner is still design-only; this is pre-build alignment so the recipe lands
> correctly on the client before the corpus-builder is written.

## 0. What is NOT re-asked (settled in response §4, adopted as binding)

- Within one listening pass, the independence unit is the **run**, not the span;
  pool a run's same-label spans into one pseudo-piece (`pieces = runs`). Pooling
  (not one-span-per-run) is the recipe — keeps data, restores independence, fixes
  the short-span where-lattice degeneracy. Our corpus-builder is spec'd this way.
- Piece floors (`min_support_pieces`, `exploratory_floor_pieces`) read against the
  **run** count; effective sample size = number of runs. Understood, will be stamped.

Everything below is strictly the one level §4's model didn't reach.

## 1. The new fact: one `run_id`, many labelings

Wend (response-3 / Wend Phase E; wont D9/D10) deliberately **parallel-sessions a
single run**: it plays one generated composition (`run_id` = its determinism
fingerprint), the listener rates it under one **scope-set** (e.g. "bass on,
topline off"), then rates the *same music again* under a different scope-set.
Each pass ships as its own `LabeledRun` — **same `run_id`, different `scopes`,
different satisfaction curve.** This is by design: it's how Wend gets per-part
attribution (D10) without asking the listener to somehow mute parts in their head.

So a single `run_id` can yield K labeled sessions. Per-run pooling was specified
for K = 1 (one labeling per run). At K > 1 it forks, and neither branch is clean:

- **Pool by `run_id`** → the K sessions collapse into one piece, but they carry
  *different scopes and different labels* — merging a "liked-bass" pass with a
  "disliked-topline" pass is not a meaningful pseudo-piece, and it destroys the
  per-scope signal the parallel sessions exist to produce.
- **One piece per session** → K pieces sharing the *same underlying music* →
  within-run-across-session correlation → the exact pseudo-replication §4 warned
  about (anti-conservative p/q), now **un-fixable by pooling** (you cannot pool
  across different labels/scopes).

## 2. The questions

**Q1 (the crux) — what is the independence unit when one run has K scoped
labelings?** Is it the `run_id` (the music), the `(run_id, scope-set)` session, or
neither cleanly? Concretely: may we treat K parallel scoped sessions of one
`run_id` as K independent pieces, or is that pseudo-replication we must correct?

**Q2 — is this the clustered / mixed-effects case you already flagged?** Response
§4 named "a clustered / mixed-effects model" as "the only alternative that beats
pooling … heavy engine work … the same contingent-slice status as graded weights."
Parallel scoped sessions look exactly like grouped observations (group = `run_id`,
within-group = the K sessions). Is a `run_id` **grouping key** on `induce_ruleset`
(support counted at the group level, sessions as correlated within-group members)
the right instrument — and if so, **we register as the named consumer** for that
slice, same posture as graded-weights? Or is there a pooling-style recipe we are
missing that preserves K's scoped signal without inflating support?

**Q3 — per-scope corpora: confirm the unit.** Each scope trains its own corpus.
For a part-scoped session, is the piece the **(run, scope)** slice — i.e. within a
scope's corpus, `pieces = runs`, each run contributing its pooled same-label spans
*for that scope only*? We believe yes and want it on record.

**Q4 — does the ruling extend verbatim to the gap-14 distribution layer?** When
the harmony scope builds `build_transition_matrix(liked)` vs `(disliked)`, is the
per-run-pooling unit identical (pool a run's liked-span transitions as that run's
single contribution to the liked distribution), and do the Q1/Q2 K-sessions
questions apply the same way to distribution construction as to `induce_ruleset`?

## 3. Why it matters — the design fork it gates

The answer decides whether Wend's parallel-scoped-session architecture (the D10
staging buffer) is a **statistical-power lever or only an attribution lever**:

- **If the independence unit is `run_id`:** parallel sessions buy *attribution,
  not power* — power stays bounded by distinct audited runs, and Wend's cheap
  determinism helps *generation*, not *significance*. We would lean on more
  distinct runs and treat scoped sessions purely as the D12 "optional prior"
  accelerant.
- **If K scoped sessions are usable as grouped pieces (Q2):** parallel sessions
  *do* add power — and wont builds the grouped-support path (your slice, or our
  client-side handling per your recipe).

Either answer is actionable; we just cannot finalize the corpus-builder — or
advise Wend on whether the staging buffer earns its complexity — without it. A
recipe answer is ideal; if it needs the clustered slice, wont is the named
consumer and will return with the trigger when the learner phase starts.

## Housekeeping

- Learner remains design-only / gated; labeled-run schema `wont.labeled-run.1`
  frozen, scenario schema `wont.scenario.1`. No urgency — pre-build alignment.
- The synthetic recovery harness (D11) is unaffected (fabricated labels, one per
  run); this question bites only real multi-session human capture.
- We continue to inherit client prior pins (`key_profile: kk-1982.1`) and will
  stamp your induction `scoring_prior` (and `distribution.1` on any distribution
  artifact) on every output.
