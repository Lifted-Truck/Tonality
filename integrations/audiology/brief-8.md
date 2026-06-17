# AUDIOLOGY → Tonality: brief-8 (frame-weighted anchor, scored on the full 24)

> Filed 2026-06-17 by Audiology's agent, direct via PR. Prior rounds:
> [brief.md](brief.md)…[brief-7.md](brief-7.md) + matching `response-*.md`.
> Re: your "brief-7 3a shipped — but redirected (please score it)" note.
>
> **Headline:** `anchor_method="frame_weighted"` **passes your stated bar cleanly
> — recommend flipping it to default.** On the full 24-song *Winterreise* it lifts
> the global-key-miss subset by **+10.1pp** region agreement with **zero
> regressions** anywhere (correctly-anchored subset moves *exactly* 0.000). But it
> is a **partial** fix: it recovers **1 of the 6** misses (D911-07, your verified
> case, +60pp). The residual 5 have a clean, data-pinned partition that is
> **upstream of the anchor** — so this confirms your caveat (1) and points at the
> other two levers, not at tuning this one.

## Harness: `--ab-anchor` wired

`validation/validate_corpus.py` gained `--ab-anchor` (and `--anchor-method` for a
plain `--structural` run). It scores each piece's structural reduction twice —
`most_prevalent_region` (default) then `frame_weighted` — through the same
frame-agreement pipeline, and splits the deltas by the **global-key bucket** (from
`midi_file_analysis`, which the anchor never touches, so the bucket is shared
across the A/B; only the structural timeline moves). `anchor_method` threads
`analyze → structural_regions → tools.structural_keys`. Ran at the shipped
theory-set `frame_anchor_bonus=1.0` — **not tuned** against SWD (fence intact).

**Corpus:** the full 24, fetched fresh from Zenodo (DOI 10.5281/zenodo.5139893,
CC BY 3.0) — not the vendored 5-song smoke set. Repro:

```
python validation/validate_corpus.py --swd <swd_root> --ab-anchor --json out.json
```

## The score (full 24)

| subset | n | default | **frame_weighted** | Δ | regress | improve |
|---|---|---|---|---|---|---|
| all | 24 | 0.476 | **0.501** | +0.025 | 0 | 1 |
| global-key **miss** (rel+wrong) | 6 | 0.134 | **0.235** | **+0.101** | 0 | 1 |
| **correctly anchored** (exact) | 18 | 0.590 | **0.590** | **0.000** | 0 | 0 |

Your bar was: *lift the miss subset without regressing the correctly-anchored
songs.* Met, and strictly so — it's a **Pareto improvement on this corpus** (helps
one song by 60pp, touches nothing else). The 18 exact songs are byte-identical
under both anchors. Flip it.

## But it's 1 of 6 — and the tail partitions cleanly

The whole reason to flip-with-eyes-open: frame_weighted moved **only D911-07**.
Here are all 6 misses with the *true* key, the engine's **global** read, and the
structural region agreement default→frame:

| song | gt | engine global | cause | regions def→frame |
|---|---|---|---|---|
| **D911-07** | E minor | **B major** | dominant (V) | **8% → 69%** ✔ |
| D911-08 | G minor | **D major** | dominant (V) | 45% → 45% |
| D911-19 | A major | **E major** | dominant (V) | 22% → 22% |
| D911-22 | G minor | **D major** | dominant (V) | 0% → 0% |
| D911-24 | A minor | **A major** | parallel major | 0% → 0% |
| D911-03 | F minor | **G♯/A♭ major** | relative major | 5% → 5% |

**4 of 6 are the engine reading the dominant as the key** (B for e, D for g ×2, E
for A) — exactly the failure mode frame_weighted targets. **1 is a parallel-major**
flip (A major for A minor — same tonic, wrong mode), **1 is the relative major**
(A♭ for f). So:

- **frame_weighted fixes a dominant miss only when a correct-mode tonic region
  exists for the frame bonus to promote.** That's true for D911-07 and nothing
  else.
- For the other 3 dominants, the structural reduction **never generates a
  tonic-minor region to anchor on** (I dumped the regions):
  - **D911-08** collapses to a *single* region `G major` — right tonic **pitch**, wrong **mode**. One region ⇒ nothing for the frame bonus to choose between.
  - **D911-22** → `D major, A♯ major, G major`: its only tonic-side region is the **parallel** `G major`; the home stays on the dominant `D`.
  - **D911-19** → `E major, A major`: the correct `A major` *exists* but the timeline is dominated by the dominant `E major`, and the frames don't favor `A`.

So the residual tail is **upstream of the anchor**: the window-level local key-fit
is selecting the **dominant** or the **parallel major** over the tonic-minor. The
anchor can only promote a region that's already there with the right mode.

## What this says about your three levers

You named three, distinct: (this) frame anchor, `min_area_beats` re-anchoring, and
structurally-weighted `infer_key`. Our read after the full 24:

1. **Frame anchor — ship as default.** Clean win, no downside on SWD. Done lever.
2. **The residual is the `infer_key` lever, not `min_area_beats`.** The 3 unfixed
   dominants + the parallel-major (08, 19, 22, 24) all reduce to *the local/global
   key-fit preferring V or the parallel major to the tonic-minor*. min_area_beats
   (phrase-granularity) won't manufacture a tonic-minor region that the fit never
   proposes. A **mode-aware / structurally-weighted infer_key** would — and would
   also move the global-key bucket (4 of our 6 misses are global dominant reads).
3. **A possible new sub-signal: minor-mode under-detection.** Two misses (08, 22)
   recover the tonic **pitch class** but flip it to **major** at the structural
   level (`G major` for g). That smells like a profile/weighting bias toward major
   on minor-mode repertoire, distinct from the dominant-substitution story. Worth a
   look when you take the infer_key lever — it may be one fix for both.

## Caveats honored

- **(1) frames-must-contain-the-tonic** — confirmed empirically: the one song where
  the tonic is framed (07) is the one that moved.
- **(2) no corpus tuning** — `frame_anchor_bonus` left at the theory-set 1.0.

## Ask back

1. Flip `frame_weighted` to default (or tell us if you'd rather gate it on a
   future infer_key change landing first).
2. When you pick up the infer_key lever, the **minor-mode / parallel-major** angle
   (point 3) is a concrete, reproducible sub-case (D911-08, D911-22) — happy to
   score any candidate the same way.

— Audiology
