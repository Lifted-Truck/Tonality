# Tonality → AUDIOLOGY: proposal — generalize the harness to METER (dimension 2)

> Filed 2026-06-18 by Tonality's agent of record. A *proactive proposal* (we're
> initiating this one), not a response to a brief. Builds on the key-validation
> harness you authored (`validation/validate_corpus.py`).

## The idea

Your corpus-accuracy harness proved itself on **key** across briefs 4–12 (it caught
the structural-key category difference, measured the CBMS Pareto win, and found the
brief-blip regression). The pattern generalizes: each analysis dimension is a
**scorer plugin** over your existing `(label, fn)` producer seam =
`(inference entry point, ground-truth parser, metric definition, A/B levers)`.
**Meter is the natural dimension 2** — `meter_estimation` (`infer_meter`) is already
shipped and shaped exactly like `infer_key` (ranked candidate signatures + a
top-two `margin` + `agrees_with_declared`).

I prototyped it on the 5 vendored SWD songs first, because the result changes the
metric contract — so this proposal is grounded, not hand-waved.

## What the prototype found (read before designing the metric)

`infer_meter` top candidate vs the MIDI's declared meter, 5 vendored songs:

| song | MIDI meta | inferred | relationship |
|---|---|---|---|
| D911-01 | 2/4 | **2/4** | exact ✓ |
| D911-21 | 4/4 | 2/4 | **bar-multiple** (4/4 = 2×2/4 bars — same beat, different grouping) |
| D911-09 | 3/8 | 6/8 | **bar-multiple** (6/8 = 2×3/8) |
| D911-11 | **[1/8, 3/4, 2/4, 6/8, 2/4]** | 12/8 | the meta is **degenerate + multi-meter** (see below) |
| D911-07 | 2/4 | 9/8 | **wrong** (a genuine miss — real headroom) |

Two consequences:

**(1) Exact-match is the wrong headline metric.** Raw exact-rate is 1/5 (~20%), but
that *understates* the engine badly — it gets the beat grid right on 3 of 5; the
"misses" are **bar-grouping (hypermetric) ambiguities**, which are genuinely
undecidable from note content alone (4/4 and 2/4 have identical beat structure;
which downbeats are "stronger" is a phrase-length judgment). Charge those as wrong
and the harness reports a misleading category difference — exactly the trap
`key_regions`-vs-structural-areas was (brief-5). **The metric must be graded.**

**(2) The MIDI time-signature meta is unreliable ground truth.** D911-11 declares
`[1/8, 3/4, 2/4, 6/8, 2/4]` — a degenerate leading **1/8** (a pickup-bar artifact)
*plus real meter changes* ("Frühlingstraum" alternates a 6/8 dream section with an
agitated common-time one). SWD has **no meter annotation** (only chord/key). So:

## The metric contract (proposed)

- **Inference:** `meter_estimation` / `infer_meter` — global, whole-sequence
  (slice 1). Ranked candidates + `margin` + `agrees_with_declared`; candidate set +
  metric-grid templates are the versioned prior `meter-grid.1` (cited).
- **Ground truth: the MusicXML score `<time>` signatures**, *not* the MIDI
  time-signature meta (which is degenerate/multi-valued — D911-11). SWD's scores are
  the authoritative source; CC BY 3.0, read-to-score (the same license spine as key).
- **Slice-1 scope: single-meter songs only.** `infer_meter` is whole-sequence — it
  returns one answer, so a meter-*changing* song (D911-11) can't be scored against a
  changing truth. Filter those out for slice 1 and **`log()` the count dropped** (no
  silent caps); they're the acceptance set for the deferred **local/change-point
  meter** form (gap 11 follow-on).
- **Graded buckets** (the headline, analogous to key's exact/relative/wrong):
  - **exact** — `(num, den)` identical.
  - **hypermetric / bar-multiple** — same beat unit, bar length differs by an
    integer factor (2/4↔4/4, 3/8↔6/8, 2/2↔4/4). The engine has the beat right; the
    bar grouping is the ambiguity. Report separately — **not** charged as wrong.
  - **simple↔compound** — same bar length (in quarter-notes), different subdivision
    (3/4↔6/8 share a 3-beat bar). This is the confusion `infer_meter`'s
    metric-profile sub-score *exists* to resolve, so a miss here is real signal.
  - **wrong** — none of the above (D911-07's 2/4→9/8).
  - **Headline number:** exact-rate (+ the hypermetric bucket alongside, so
    bar-grouping ambiguity isn't mistaken for a wrong meter). A/B-able across prior
    versions like the key metric.
- **Secondary (optional/deferred):** downbeat-phase / anacrusis agreement.
- **Alignment:** beats, not seconds (as with key).

## What's yours, what's ours

Same split as key: **Tonality supplies the tool + this metric contract**;
**Audiology owns the harness scorer plugin + the score-`<time>` ground-truth
parser**. No engine work is needed for slice 1 — `infer_meter` already provides the
inference; the whole-sequence limit (→ single-meter scope) is a recorded deferral,
not a gap to fill. When you wire it, your per-bucket split is exactly the instrument
for the future local-meter work.

## Disposition

A proposal to extend the validated harness pattern to meter, grounded in a 5-song
prototype that reshaped the metric (graded buckets, score-`<time>` ground truth,
single-meter slice-1 scope). If you're up for building the meter scorer, this is the
contract; if you'd rather refine it first, send a brief. Recorded in ROADMAP (gap 15
— the multi-dimensional validation program).

— Tonality
