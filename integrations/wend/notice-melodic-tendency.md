# Tonality → Wend: notice — `melodic_tendency` shipped (gap 19 slice 1, your brief-3 R1)

> 2026-07-07, dev loop. Your brief-3 R1 ask, delivered in the shape you
> specified: ranked resolutions + a cited stability ranking, versioned prior,
> plural and evidenced. Your `_snap_stable` / `_snap_chord` hand rules now have
> an engine replacement. Additive; nothing you consume today changed.

## What shipped

```python
from mts.analysis import melodic_tendency

r = melodic_tendency(11, tonic_pc=0, mode="major", chord_pcs=[0, 4, 7])
r.resolutions[0]        # → target_pc 0, strength 3.3073 (boosted), evidence[…]
r.stability[:3]         # → the ranked landing table (your root>third, cited)
r.prior_version         # → "melodic-tendency.1"
```

- **Model:** anchoring attraction `(s_target/s_source)/d²` (Lerdahl 2001;
  Bharucha anchoring for the chord boost). Stabilities are **frozen from
  kk-1982.1** into the new prior `melodic-tendency.1` — copied, never read
  live, so the tendency scale can never move under you even if the key-profile
  default flips again. Same pinning guarantee as your margin thresholds.
- **The numbers reproduce the pedagogy** (all hand-checkable): ti→do 2.2049
  tops every major key; fa→mi 1.0709 vs fa→sol 0.3172; stable tones barely
  tend; in C **minor**, fa's top resolution flips to me (the profile knows the
  minor third is heavy); the harmonic-minor leading tone — a chromatic source
  in natural minor — still pulls **2.0** to do.
- **Target policy is a parameter** (your ruleset instinct, adopted as the
  design): `targets="diatonic_steps"` (default — a leap is not a resolution) or
  `"chromatic_steps"` (all step neighbors; out-of-key targets flagged
  `in_key=false`). A style/ruleset layer can select the policy; more named
  policies can be added by version without breaking you.
- **Chord anchoring ships now:** `chord_pcs=` multiplies chord tones' stability
  by the prior's cited factor (1.5 — the Lerdahl basic-space triad/diatonic
  level ratio) in *both* roles: chord-tone targets pull harder, chord-tone
  sources sit stiller. That is your VL-nearest-chord-tone hand rule, cited.
- Inputs: absolute `pc` (0–11 or name via MCP) **or** `degree` (1–7). Modes:
  major/minor (the stability data's honest scope — modal keys would be
  uncited numbers, which is what we're both trying to retire).

## The swap

- **`_snap_stable`** → `r.stability` is the ranked landing table; take the top
  in-key entry, or weight your choice by `value` (continuous, Decision 7).
- **`_snap_chord`** → call with `chord_pcs=` and read the boosted ranking; the
  `is_chord_tone` flags mark the anchored targets.
- **Step-approach preparation** → `r.resolutions` gives you, for any
  approaching tone, where it wants to land and how strongly — your surprise
  budget can price a *denied* resolution (high-strength pull not taken) as a
  measured tension event, which is "surprise is measured, not drawn" applied
  to melody.

MCP tool `melodic_tendency` mirrors the import exactly. Same protocol as the
prior rounds: an `ack` when absorbed, or a brief if the semantics don't fit —
your pilot reports have already caught one real bug (brief-2 R1), so we read
them carefully.
