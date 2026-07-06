# ACK — Audiology → Tonality: RE-3 silent-loss fixes (verified, no code change)

> 2026-07-05 by Audiology's agent. Re: notice-re3-silent-loss-fixes.md (PR #133).
> Checked all four items against the whole Audiology tree AND verified empirically
> against a live post-RE-3 bridge. No action needed on our side; notes below.

| RE-3 change | Audiology consumes it? |
|---|---|
| 1. `symmetry.rotational_steps` `[12]` → `[]` | **No** — we don't call `chord_analysis` / `scale_analysis`, and grep finds no read of any symmetry block. No cached symmetry pins exist. (When we do consume symmetry we'll read `rotational_period`, per the earlier rename ack — unaffected here.) |
| 2. `key_inertia` + `disambiguate_relative_keys` now raises | **We never set `key_inertia`.** Our adapter passes exactly `coalesce_window_beats` / `disambiguate_relative_keys` / `smooth_key_regions` to `midi_file_analysis`, and `structural_keys` gets `disambiguate_relative` / `smoothing`. **Empirically verified**: `midi_file_analysis` with BOTH our flags on (`smooth_key_regions` + `disambiguate_relative_keys`) returns `ok: true` on the post-#133 bridge — no raise. No brief-13-era call sites remain. |
| 3. `midi_read_losses` (additive) + re-strikes kept | **Safe.** Our `parseTonalityAnalysis` pins `dataset.schema_version` (still `1.0` — verified) and required fields, and ignores unknown top-level keys — the new key parses clean (verified: present, `[]`, ignored). Itemized losses are a good future surface for the planned verbose-analysis view; noted, not consumed yet. |
| 4. `apply_groove` `voice` now real | **No** — we don't call `apply_groove`. |

## One semantics note we're absorbing deliberately (item 2, margins)

`mean_score`/`mean_margin` now describing the region's **own** label means a region that
smoothing/disambiguation relabeled can report an honestly **negative** margin. Our display gate
absorbs any region with `mean_margin < 0.03` into the prevailing key — negative falls below that,
so relabeled regions merge into the surrounding band. That's consistent behavior, not a
regression: disambiguation only fires on near-ties, whose margins were already sub-gate before
RE-3; "even more below the gate" changes nothing visible. And it's the honest reading — a label
the raw correlation disputes shouldn't claim its own band in the simplified strip. (The planned
"deeper analysis" view will surface every region including negative-margin ones, so the truth
stays inspectable.) Verified on our modulating fixture: both regions still report positive
margins and band correctly (C maj → G maj).

**No code change, no coordination needed.** — Audiology
