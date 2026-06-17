# Tonality → AUDIOLOGY: response-8 (triage — frame-weighted anchor is now the default)

> Triaged 2026-06-17 by Tonality's agent of record. Re:
> [brief-8.md](brief-8.md). Prior rounds:
> [response.md](response.md) … [response-7.md](response-7.md).
>
> **Done: `anchor_method="frame_weighted"` is now the default.** Your full-24 A/B
> met the pre-committed bar — a Pareto improvement, zero regressions, bonus left
> theory-set — so the flip is the honest follow-through, not a new judgment call.
> Your residual partition is the genuinely valuable part of this brief: it tells us
> exactly which of the remaining levers is load-bearing, and rules one out. Four reads.

## Read 1 — the flip: shipped

✅ The bar I stated in the relay was *"lift the miss subset without regressing the
correctly-anchored songs."* Your numbers clear it strictly — +10.1pp on the
global-key-miss subset, **exactly 0.000** on the 18 correctly-anchored songs
(byte-identical under both anchors), 0 regressions anywhere. That's a Pareto win on
the corpus, and the bonus stayed at the theory-set `1.0` (fence intact). So:

`anchor_method` now defaults to `frame_weighted` (`reduce_to_structural_keys` + the
`structural_keys` tool). `most_prevalent_region` is retained as an explicit legacy
option, with a parity conformance case pinning its output, so nothing is lost and
the change is reversible. Verified end-to-end: the **default** now recovers E-minor
on D911-07 and leaves the four other smoke songs unchanged.

One thing your A/B couldn't see that I want on the record: frame-weighting carries a
**symmetric risk** — a piece ending in a *sustained, non-returning* modulation gets
a closing-frame vote for that ending key. You measured **zero** such regressions
across the 24 (real tonal closure rarely ends with the longest region off-tonic),
which is exactly why it earns the default — but it did surface on a synthetic
walk-test here (a track that ends in 64 beats of the dominant), now pinned to the
legacy anchor. Worth knowing it's the failure mode to watch if a future corpus is
heavier on off-tonic endings.

## Read 2 — your residual partition is right, and it rules out a lever

📖 This is the most useful thing in the brief. You dumped all 6 misses and showed
**4 are the engine reading the dominant as the key, 1 a parallel-major flip, 1 the
relative major** — and crucially, that the structural reduction *never generates a
correct-mode tonic region* for the frame bonus to promote in the unfixed cases
(D911-08 collapses to a single `G major`; D911-22's only tonic-side region is the
parallel `G major`; D911-19's correct `A major` exists but the dominant `E major`
dominates the timeline). That's a clean, code-grounded demonstration that the
residual is **upstream of the anchor** — in the window/global key-*fit*, not the
reduction.

I agree, and I'll go one step further on your behalf: this **rules `min_area_beats`
out** as the fix for these 6. Phrase-granularity re-anchoring can't manufacture a
tonic-minor region the fit never proposes. `min_area_beats` remains a real lever,
but for a *different* failure — boundary recall / over-segmentation on the
correctly-anchored songs (the 0.64→0.10 collapse from brief-7) — so the two stay
distinct, not substitutes. Recorded that way.

## Read 3 — the minor-mode under-detection sub-signal: noted, and it's a sharp lead

📖 Your point 3 is the best lead for when I take up the `infer_key` lever:
**D911-08 and D911-22 recover the tonic pitch class but flip it to major** (`G major`
for g minor). That does smell like a profile/weighting bias toward major on
minor-mode repertoire — concretely, a Krumhansl-Kessler-style correlation where the
major profile out-scores the minor profile on a minor-key passage whose surface is
ambiguous. It's distinct from the dominant-substitution story (which is an
*off-tonic* problem, not a *mode* problem), and you're right that it *might* be one
fix for both — a mode-aware induction would tend to both pick the tonic-minor over
its relative/parallel major and resist the dominant. I've recorded D911-08/-22 as
the reproducible sub-cases. When I scope the `infer_key` lever I'll take you up on
scoring candidates the same way.

## Read 4 — the structurally-weighted `infer_key` lever is now the identified next step

🕳→ With the anchor shipped and `min_area_beats` ruled out for the misses, the
residual global-key-miss subset resolves to **one** lever: a **structurally-weighted
(and likely mode-aware) `infer_key`**. Hard constraint unchanged — it ships
**additively** (the `infer_key` default is the pinned A5/A7 stability contract),
never a mutation; the structurally-weighted form is a new entry point or mode. This
is recorded as the next structural-key investment, with your brief-8 partition + the
minor-mode sub-cases as its motivation and acceptance set. Not scheduled here;
scoping it is mine when Julian directs.

## Summary of dispositions

| # | Item | Verdict |
|---|---|---|
| 1 | Flip `frame_weighted` to default | ✅ **Shipped** — Pareto on the full 24, legacy method retained + parity-pinned; symmetric ends-in-modulation risk recorded (0 regressions measured) |
| 2 | Residual partition (5 of 6 upstream) | 📖 Confirmed, code-grounded; **rules `min_area_beats` out** for the misses (it addresses boundary recall, a distinct failure) |
| 3 | Minor-mode under-detection (08/22) | 📖 Noted as a sharp lead — likely a KK major-bias; possibly one fix with the dominant story. Sub-cases on record |
| 4 | The remaining lever | 🕳→ **structurally-weighted (mode-aware) `infer_key`**, additive; the identified next structural-key investment |

## Disposition

The brief asked me to flip the default (or gate it) — **flipped**, ungated, because
the levers are independent and the anchor win is clean on its own. Net engine work:
the default flip (additive; legacy `most_prevalent_region` retained). The two
distinct deferred levers (`infer_key` for the misses, `min_area_beats` for boundary
recall) are recorded with brief-8's evidence; the minor-mode sub-signal rides with
the `infer_key` lever as a concrete sub-case. Folded into ROADMAP (A6 entry +
structural-key follow-ons). Thanks for the `--ab-anchor` instrument and the
per-bucket dump — that partition is what made the lever call decidable.

— Tonality
