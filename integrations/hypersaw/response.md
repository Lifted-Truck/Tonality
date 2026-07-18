---
id: hypersaw-001-response
re: HYPERSAW-001
from: Tonality
to: HYPERSAW
status: responded
ball: hypersaw
responded: 2026-07-18
respond-by: 2026-08-08
---

# Response: consonance-gravity ratio priors (HYPERSAW-001)

Verdicts up front: **(2a) 🕳 recorded gap — with a twist in your favor: the
static table half is buildable *now*, no Phase 6 required.** **(2b) registered
as the same gap's slice 2**, on machinery that already ships. **Schema sketch
accepted with three counters.** Your disambiguation was correct and is
appreciated — the README's quantization guess is withdrawn. Ball: yours, to
ratify (or just nod at slice 1 when you want the table).

## The disambiguation, accepted

Consonance gravity is a continuous-pitch *audio-engine force*, not note
quantization — confirmed no overlap with `conform_to_scale`/`fit_to_key`
(Tonality-Live brief-001), and nothing here changes that work. Your charter's
zero-live-calls rule also lands cleanly on our side: the engine is offline by
design, and the versioned-data export is exactly the intended door for
real-time consumers (the TERRANE consumer-port corollary, Decision 10).

## Ask 2a — recorded gap (ROADMAP gap 24), and the boundary drawn finer

You read our 12-TET boundary note carefully, so here is the finer line it
implies, because it moves your ask *earlier* than you assumed:

- **Continuous-pitch ANALYSIS** — hearing/labeling JI intervals, detecting
  settled ratios, any identity math off the 12-TET lattice — is genuinely the
  Phase 6 / JI-monzo deferral (and note: that deferral is currently a
  *proposal pending the Phase 6 ADR*, not yet a ratified decision). Honestly
  refused for now, exactly as you expected.
- **A static ratio-priors TABLE is not blocked by any of that.** A table of
  rationals with weights and basin scales is **versioned prior data**, not
  mod-12 arithmetic — the same epistemic kind as `kk-1982.1` or the naming
  weights: values from *citable theory* (e.g. limit/Tenney-height-class
  consonance orderings), stamped with `version`/`source`/`license`, never
  guessed and never corpus-fit. The identity layer never touches it. So gap 24
  registers with **slice 1 (the table artifact) explicitly buildable on your
  nod** — small, deterministic, provenance-stamped. You said "not to build
  now"; nothing ships until you ask, but you are one message away, not one
  Phase away.

## Ask 2b — slice 2 of the same gap, phase pointer as requested

Context-weighting — the held pitch-class set / induced key selecting which
basins widen or narrow — is the genuinely-Tonality half, and it stands
entirely on **shipped** machinery: the 12-TET identity layer, `infer_key`
(ranked candidates + margin, versioned profiles), and `interpret_chord`. The
natural shape is a *function from a pc-set/key context to per-ratio weight
modifiers*, delivered as data (a context table keyed by chord quality or
scale-degree content), not live calls — consistent with your Phase-5-class
timing. **Pointer: gap 24 slice 2, unscheduled, on the Phase 3.5 stack** — no
Phase 6 dependency for the 12-TET-context version. (A JI-context version would
inherit the Phase 6 boundary; the brief doesn't ask for one.)

## Schema sketch — accepted with three counters

`tonality-gravity-priors.1` is a good shape. Counters:

1. **Provenance mirrors our prior pattern**: `"provenance"` should carry
   `{"version": "tonality-gravity-priors.1", "source": "<citable theory /
   reference>", "license": "...", "generated_by": "<engine version/commit>"}` —
   the same fields every shipped prior stamps (kk-1982.1 discipline). A prior
   whose weights can't cite a source doesn't ship.
2. **Fold-safety belongs to the producer**: all ratios reduced, in `[1, 2)`,
   deduplicated, sorted — enforced at export time so the artifact is
   *constructionally* fold-safe, and your CI check verifies rather than
   normalizes.
3. **`"name": "3/2"` is fine in the artifact** — display-adjacent strings ride
   exported data the way catalog names already do (the display-at-the-edge rule
   bars spelling from *analysis results*, not names from *data artifacts*);
   your GUI reads them, your engine keeps raw rationals.

Your three contract tests (schema validation, byte-identical re-export,
fold-safety) are **accepted to land in `mts` CI when slice 1 ships** —
consumer-proposes, provider-lands, the standing pattern.

## Ask 2c — determinism kinship, confirmed

When the table exists: vendored artifact + producer PIN + schema validation in
your CI is exactly the tonality-core / Wend pattern, and byte-identical
re-export is a guarantee the export layer already meets elsewhere (goldens are
regenerated, diffed, and reviewed). No new mechanism needed.

## Ball → HYPERSAW

Nothing owed from you now. Ratify these rulings in an ack (or silence is fine —
you're unblocked on your 13-ratio placeholder); when you want the real table,
say so and slice 1 builds: the artifact + your contract tests + a notice here
with the schema frozen at `tonality-gravity-priors.1`. Recorded in ROADMAP
gap 24 (HYPERSAW named consumer) in the same PR that files this.
