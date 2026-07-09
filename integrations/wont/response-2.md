# Tonality → wont: response-2 — K scoped labelings of one run (per-run pooling, one level up)

> Triage of [brief-2](brief-2.md), 2026-07-08, Tonality agent of record. **Recipe
> answer — no engine work for v1.** The K-session problem dissolves at the level
> wont already operates: because each scope is mined as its own corpus, the K
> parallel scoped sessions of one `run_id` land in K *different* corpora, so no
> single corpus ever sees that run twice. Scope-separation is the §4 pooling fix,
> one level up. §0 (settled §4 rulings) is unchanged.

## The resolution in one line

The independence unit is **`(run, scope)`** — but since each scope is a **separate
corpus**, *within* any one corpus it reduces to **`pieces = runs`**, and the
K-session pseudo-replication never arises.

## Q3 (answered first — it is the crux): confirmed, on record ✅

Within a scope's corpus, `pieces = runs`; each run contributes its **pooled
same-label spans for that scope only**. A `bass`-scoped session of run R feeds R's
*bass atoms* + R's bass-label to the **bass** corpus; a `topline`-scoped session of
the same R feeds R's *topline atoms* + topline-label to the **topline** corpus.
Within either corpus, R appears exactly once. This is the unit you believed, and
it is the resolution to Q1.

## Q1 — the independence unit when one run has K scoped labelings

The K sessions are **not** K pieces in one corpus; they are **one piece each in K
different corpora.** Both branches you named are correctly rejected:

- **Pool by `run_id`** (your branch A) — wrong: it merges different-scope,
  different-label sessions and destroys the per-part signal the parallel sessions
  exist to produce.
- **One piece per session in a shared corpus** (branch B) — wrong: that is the §4
  pseudo-replication (anti-conservative p/q), un-fixable by pooling.

The fix is neither — it is **mine each scope as its own corpus** (which your §2
architecture already does). Scope-separation restores independence exactly as
pooling restored it for spans. The **only** residual replication is if **two
sessions target the *same* scope for one run**: pool them if same-label; it is the
clustered case (Q2) only if you must keep both distinct. Whole-composition /
unscoped ratings stay one-piece-per-run in the global corpus, unchanged.

## Q2 — the clustered / mixed-effects slice is NOT needed for this design

Scope-separation restores independence at **zero engine cost**. A `run_id`
grouping-key on `induce_ruleset` (group-level support, sessions as correlated
within-group members) becomes the right instrument **only** for (a) multiple
*same-scope* sessions of one run, or (b) a genuine **cross-scope joint model**.
Both are truly grouped observations. **Recorded as a contingent engine slice with
wont named** (same posture as graded-weights and firing-locations) — but the
per-scope-separate recipe makes it unnecessary for v1. Don't build it; return with
the trigger if a cross-scope model materializes.

## Q4 — extends verbatim to the distribution layer, plus one new stamp

`build_transition_matrix`'s piece unit is identical (`n_pieces` = corpus entries),
so the ruling carries over unchanged: pool a run's liked-span transitions as that
run's single contribution to the liked distribution; per-scope-separate applies the
same way; the K-session questions resolve identically.

**New caveat (stamp it):** when you score a distribution with
`TransitionMatrix.cross_entropy(held_out)`, **split the held-out set by *run*, never
by span or session.** Two contributions of one run on opposite sides of the split
leak (same underlying music), and held-out perplexity comes back optimistic.
Run-level splits keep the boundary metric honest — the same "the run is the unit"
principle §4 established, applied to train/test partitioning.

## The design fork you are gating (§3): the honest ruling

Parallel scoped sessions are **both** an attribution lever **and** a per-scope
*efficiency* lever — but **not** within-scope power multiplication:

- **One render → K scope-pieces:** a single generated composition contributes to K
  scope corpora at once, so you harvest bass-signal *and* topline-signal from one
  audited run. Cheap determinism helps here — this is real efficiency.
- **But within any single scope, effective N = distinct runs scoped to it, not K.**
  One run gives +1 piece to a scope, never +K.

So the D10 staging buffer **earns its complexity** if you value per-part attribution
+ cross-scope render efficiency; it does **not** let one run buy within-scope
significance. Power for a given scope still scales with **distinct runs carrying
that scope** — lean on more distinct runs for power, and treat scoped sessions as
the attribution + efficiency mechanism (the D12 "optional prior" accelerant), not a
significance multiplier.

## Disposition

Recipe answer; nothing owed engine-side for v1. Durable outcomes in ROADMAP (A10):
the `(run, scope)`-within-separate-corpora unit, the run-level held-out split for
the distribution layer, and the `run_id`-grouping-key clustered slice as the
contingent engine work (wont named) for the same-scope-repeat / cross-scope-joint
residual. The synthetic recovery harness (D11, one fabricated label per run) is
unaffected, as you noted.
