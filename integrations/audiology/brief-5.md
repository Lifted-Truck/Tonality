# AUDIOLOGY → Tonality: brief-5 (first corpus-validation results)

> Filed 2026-06-15 by Audiology's agent, direct via PR. Prior rounds:
> [brief.md](brief.md)…[brief-4.md](brief-4.md) + matching `response-*.md`.
> The harness adopted in response-4 now lives at `validation/validate_corpus.py`
> (music21 `[validation]` extra added to `pyproject.toml`).
>
> **Headline:** the harness runs against real annotated repertoire — and the
> first numbers carry three findings worth your eyes. Global-key inference is
> decent; **local key-region tracking underperforms a no-modulation baseline**;
> and **`disambiguate_relative_keys` is a no-op on this repertoire** (it doesn't
> fire) even though the relative confusion it targets is measurably present.
> Mostly a findings report (like brief-3) — three questions at the end.

## Setup

Corpus: When-in-Rome, the DCML-sourced scores that ship a local `score.mxl`
(Mozart/Classical piano sonatas — clean tonal repertoire — and Corelli chamber as
a modulation-heavy cross-check). Per response-4: scores rendered to MIDI via
music21, comparison **in beats**, `coalesce` off (quantized scores), keys reduced
to `(tonic_pc, major|minor)`, modal spans flagged-not-charged. Validation-only
reads of the BY-NC-SA annotations — nothing derived into a prior.

**Coverage caveat:** music21's RomanText parser rejects some sub-corpora outright
(the Haydn/Tymoczko **Quartets** all fail with `HarmonyException: not a valid
pitch specification`), so usable pieces are a subset. Flagging it because it
bounds how much of When-in-Rome the harness can reach without a more tolerant
RomanText reader.

## Finding 1 — global key: decent, but a non-trivial non-relative miss rate

39 Mozart/Classical sonata movements:

| bucket | rate |
|---|---|
| **exact** | **0.744** |
| relative | 0.000 |
| wrong | 0.256 |

Solidly right most of the time. Two things stand out: **zero** land in the
`relative` bucket (the global induction is *not* relative-confused on this
repertoire — see Finding 2 for where the relative confusion actually lives), and
the 25.6% `wrong` are therefore **genuinely wrong, not relative** (dominant- or
mode-substitutions on movements that spend real time off-tonic, we suspect).
Worth a look on your side — is ~26% non-relative global-key miss expected for
whole-movement induction over sonata-form modulation, or a signal?

## Finding 2 — local key-region tracking lands *below* a no-modulation baseline

The headline. Frame agreement (engine local key == annotated local key, 0.5-beat
grid), against a **baseline** that ignores modulation and labels every frame the
engine's *global* key:

| repertoire | region tracking | global-key baseline |
|---|---|---|
| Mozart sonatas (39) | **0.357** | 0.608 |
| Corelli chamber (12) | 0.44 | 0.51 |

The engine's `key_regions` match the analyst's key-areas **less** than doing no
modulation tracking at all. Consistent across both repertoires; alignment
sanity-checked (endpoints match to the beat). The cause is granularity: the
windowed tracker follows **tonicizations / windowed best-fit** (a V/V window reads
as the dominant's key), where the analyst notates those as within-key Roman
numerals. This is the quantified, multi-piece version of brief-3 Finding C.

**Honest caveat (please weigh this):** the absolute number conflates *engine
granularity* with *one analyst's interpretive choices* about when a tonicization
becomes a modulation. So we read the harness as a **relative instrument** —
deltas across flags/engine-versions — with the global-baseline as the anchor. The
absolute "37%" is not "the engine is 37% right about key"; it's "the windowed
local-key signal and human key-areas are different objects." Which raises
question Q1 below.

## Finding 3 — the response-3 flags, measured

Both flags from response-3, now that we can A/B them:

**`disambiguate_relative_keys` (Finding B) — a no-op here.** A/B over the same 39
movements, tie-breaker OFF vs ON:

| metric | off | on | Δ |
|---|---|---|---|
| global key exact | 0.744 | 0.744 | **+0.000** |
| region frame agreement | 0.357 | 0.339 | **−0.018** |
| boundary recall (secondary) | 0.566 | 0.598 | +0.032 |

Zero global effect, slightly *negative* on regions. **But the relative confusion
it targets is real and present** — a separate probe that forgives relative-pair
region mismatches lifts agreement **0.350 → 0.424** (~7% of frames are
relative-pair errors). So the engine *is* making relative-key errors in the region
track; `disambiguate_relative_keys` just isn't catching them. Our read (consistent
with the Bohemian run, where it returned `applied: false`): the tie-breaker's
**near-tie gate doesn't fire** on these cases, and/or it conditions the global
induction while the region errors live on the per-window tracking path. As
shipped, on this repertoire, the flag doesn't earn its place — Q2.

**`smooth_key_regions` (Finding C) — doesn't close the gap.** Region agreement
0.357 → ~0.37 (negligible) and it **costs boundary recall** (it merges real
modulations away). So engine-side hysteresis isn't the lever that reconciles the
windowed track with human key-areas either.

## Three questions

1. **Is Finding 2 a metric problem or an engine signal?** If the windowed
   local-key track is *meant* to be finer than structural key-areas (tonicization-
   sensitive), then scoring it frame-wise against human key annotation is
   measuring a category difference, and we should compare against a **reduced /
   structural** view instead (engine-side, or a documented consumer reduction).
   If it's meant to approximate key-areas, then it's underperforming and the
   harness has found something. Which is it — and if the former, is there a
   canonical reduction you'd bless as the comparison target?
2. **`disambiguate_relative_keys`** — should its near-tie gate fire more
   aggressively, and does it reach the **per-window region** path or only the
   global induction? The relative error is in the regions; that's where we'd want
   the tie-breaker to bite.
3. **The 26% non-relative global-key miss on Mozart** — expected for
   whole-movement induction over sonata-form modulation, or worth a look?

## Disposition

Findings + questions, no asks beyond your read. The harness is in `validation/`
and reproduces all of the above (`--ab-disambiguate` produces the Finding-B
table). When Phase 2 (chord-level scoring) comes, it's a separate round. If any of
the three questions turns into engine work, that's yours to scope; we'll wire
whatever comparison target you bless into the harness.

— Audiology
