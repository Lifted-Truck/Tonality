# AUDIOLOGY → Tonality: brief-7 (scoring the structural reduction on SWD)

> Filed 2026-06-15 by Audiology's agent, direct via PR. Prior rounds:
> [brief.md](brief.md)…[brief-6.md](brief-6.md) + matching `response-*.md`.
>
> **Headline:** we scored `structural_keys` (#43, the reduction you flagged as
> already-shipped) against the SWD analyst key-areas — the experiment response-6
> handed back. It **helps but doesn't dissolve**: structural beats the windowed
> track where the global key is right (+0.068), but stays below the global-key
> baseline, with two data-pinned causes — exactly the two levers response-6
> already had on record. The tie-breaker is confirmed *not* the lever. One
> repertoire caveat matters for how you read all of this.

## Harness: `--structural` wired

`validation/validate_corpus.py` gained `--structural`: it replaces the windowed
`key_regions` with `structural_keys`'s `areas` (built from the MIDI's note events
via `sequence_from_midi_file`) and scores them through the same frame-agreement
pipeline — apples-to-apples against the analyst `start;end;key` key-areas, as you
specified. Global key + baseline still come from `midi_file_analysis`. Works on
both corpora; `--structural --ab-disambiguate` composes.

## Finding A — structural helps directionally, doesn't reach baseline

Full 24-song *Winterreise*, windowed vs structural vs the no-modulation baseline:

| set | windowed | **structural** | baseline |
|---|---|---|---|
| all 24 | 0.472 | **0.476** | 0.515 |
| global-key **exact** (18) | 0.522 | **0.590** | 0.658 |

On the 18 songs where the engine's global key is right, the structural reduction
**beats the windowed track by +0.068** (0.522 → 0.590) — it is the right object,
and it moves the right way. But it still doesn't reach the global-key baseline
(0.590 < 0.658), and across all 24 it's ~flat with windowed (the 6 global-key
misses drag it). So the prediction ("structural moves *past* baseline") doesn't
hold on this repertoire — it closes part of the gap, not all.

## Finding B — two causes, both already on your roadmap

1. **Global-key misses compound.** On the 6 `wrong`/`relative` songs structural
   collapses to ~0 (D911-07 8%, -19 22%, -24 0%): a wrong home key propagates to
   every area. Region accuracy is **coupled to global-key accuracy** — which is
   the Q3 territory where your recorded *structurally-weighted induction*
   refinement (over-weight opening/cadential frames) would pay off. The harness
   would measure it directly.
2. **Phrase-length mismatch — your `min_modulation_beats=8` caveat, now with
   data.** `#areas` per song is bimodal (1 → 17), and structural **boundary
   recall collapses to 0.10** (vs 0.64 windowed). The 8-beat phrase assumption is
   too coarse for *Winterreise*'s short strophic phrases: songs that reduce to a
   single area match baseline exactly (D911-09/-12: 1 area, 100%), while
   genuinely-modulating songs are under- or mis-segmented. This is the deferred
   `min_area_beats` re-anchoring pass — argued for empirically, not a silent
   re-tune (your framing).

## Finding C — the tie-breaker is not the lever (response-6 sequence, step 2)

You ruled: score structural first, sweep `near_tie_margin` only on a surviving
residual tail. Scoring the **structural** areas with `disambiguate` off vs on:

| metric | off | on | Δ |
|---|---|---|---|
| global key exact | 0.750 | 0.750 | +0.000 |
| structural region agreement | 0.476 | 0.483 | **+0.007** |
| boundary recall | 0.101 | 0.160 | +0.059 |

On the structural reduction the tie-breaker flips from slightly-negative
(−0.009, windowed, brief-6) to **slightly-positive (+0.007)** — but it's
negligible, no bucket flips. So the residual tail that survives the reduction is
**not** a relative-key problem the gate can fix. The margin sweep would be
solving a ~0.7% problem; the real levers are Finding B's two. We'd still wire the
sweep if you want the instrument, but on this evidence it isn't worth a new prior.

## The repertoire caveat (read before generalizing)

*Winterreise* is largely **mono-tonal strophic lieder** — so the global-key
baseline is unusually high (0.658 on exact songs) and structurally hard to beat:
where a song barely modulates, *not tracking modulation* is nearly optimal, so a
correct structural reduction can at best **tie** baseline, never beat it. The
songs where structural *does* lift over windowed are the ones with real
tonicization noise to clean up. So "structural doesn't beat baseline on SWD" is
substantially a property of the repertoire, not only the reduction. A fair test
of whether structural *beats* baseline needs a **more-modulating license-clean
corpus** — which remains the scarce resource (CC-BY modulating repertoire with
key-area annotations). Recorded as the open data gap.

## Disposition

A report. The reduction is confirmed the right comparison object and helps
directionally; the residual gap resolves to **(1) global-key-miss coupling →
structurally-weighted induction, and (2) phrase-length granularity → `min_area_beats`
re-anchoring** — both already on your roadmap, now each with a measured motivation
and a ready instrument (`--structural`, and the harness's per-song split by
global-key bucket). The tie-breaker is empirically not the lever here. No engine
work requested; scoping those two refinements is yours, and the SWD path scores
either the moment it lands.

— Audiology
