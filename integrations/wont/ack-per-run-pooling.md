# wont → Tonality: ack — per-run pooling & the K-scoped-session resolution (response-2)

> **DRAFT — prepared 2026-07-08 by the wont agent for Julian's review; NOT yet
> filed/committed.** Closes the brief-2 / response-2 thread. Recipe answer
> adopted; nothing owed either side for v1.

**Adopted, on record:**

- **The piece unit is `(run, scope)`, and scope-separation dissolves the
  K-session problem.** Because each scope is mined as its own corpus, K parallel
  scoped sessions of one `run_id` land in K *different* corpora, so within any one
  corpus `pieces = runs` and the pseudo-replication never arises. Our corpus
  builder mines one pooled pseudo-piece per run per scope; whole-composition /
  unscoped ratings stay one-piece-per-run in the global corpus. Both branches we
  named (pool-by-`run_id`, one-piece-per-session-in-a-shared-corpus) are dropped.
- **Held-out splits go by run.** `TransitionMatrix.cross_entropy(held_out)` — and
  the D11 recovery-harness metric built on it — will partition held-out material
  by **run**, never by span or session, so same-run material can't leak across the
  split. Stamped as the train/test corollary of "the run is the unit."
- **The distribution layer inherits the ruling verbatim** (`n_pieces` = corpus
  entries): pool a run's liked-span transitions as that run's single contribution;
  per-scope-separate applies identically.
- **The design fork is settled our side.** Parallel scoped sessions are an
  attribution + cross-scope render-efficiency lever, **not** within-scope power —
  a scope's effective N is the distinct runs carrying it. Wend's D10 staging buffer
  earns its keep for attribution + efficiency; for significance we lean on more
  distinct runs, treating scoped sessions as the D12 optional-prior accelerant.

**Deferred, with the trigger recorded (wont named consumer):** the `run_id`
grouping-key (clustered / mixed-effects) slice — needed only for multiple
*same-scope* sessions of one run, or a genuine cross-scope joint model. We won't
build toward it; we'll return with the trigger if a cross-scope model materializes
in the learner phase. Same contingent posture as graded-weights (gap 20) and the
`compare_transition_matrices` slice.

Learner remains design-only / gated; this is pre-build alignment. Thanks — the
scope-separation framing is cleaner than the fork we brought you.
