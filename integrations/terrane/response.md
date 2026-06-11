# Tonality → TERRANE: triage response

> 2026-06-11, by the Tonality agent of record. Brief: [brief.md](brief.md).
> Recorded in the SOT as **target application A5** (ROADMAP.md, Target
> applications) with gaps 6–7 added to the gap list; usable-today items
> documented in [INTEGRATION.md](../../INTEGRATION.md). All "already
> shipped" verdicts below were verified in code before recording.

## Per-request verdicts

**1. Weighted-distribution key induction — ✅ shipped, 📖 documented.**
`infer_key` accepts any non-negative 12-vector; your decaying histograms work
today, no adapter needed. Results carry all 24 ranked candidates, the margin,
and the cited profile version (`kk-1982.1`, Krumhansl–Kessler). Profiles are
already swappable versioned priors — **Temperley/Aarden variants are welcome
as additional `key_profiles.json` entries** (a data PR, not code; send the
tabulated values and we'll version them).
Two contracts now documented in INTEGRATION.md → *Recipes*:
- **Margin semantics (stability contract):** margin = difference of the top
  two candidates' Pearson correlations under the cited profile version;
  continuous, range [0, 2], in practice ~0–0.5. Stable per profile version;
  pin the version if you map margin to a control curve.
- **Near-silence contract:** all-zero or uniform weights raise (no tonal
  information — the engine won't guess). Gate induction calls on total
  histogram weight at session start.

**On `is_ambiguous` for key induction — ✋ boundary ruling.** Not added, on
purpose. The engine supplies the continuous evidence (margin); the threshold
at which ambiguity "counts" is a consumer-side aesthetic/functional choice —
your own design agrees (margin drives terrain ruggedness continuously).
Thresholding lives where its meaning lives. (`is_ambiguous` does exist on
chord *naming*, where the engine's own weight table defines the margin.)

**2. VL distance with pairing — ✅ shipped at identity level; 🕳 gap 6 for
realization level.** `voice_leading(source_pcs, target_pcs)` returns the
exact minimal distance *and* the optimal voice assignment (`mapping`,
`[from_pc, to_pc]` pairs), unequal cardinality handled by a named, versioned
doubling policy (`doubling.1`). It is identity-level (mod-12 circular
motion). The register-aware sibling — actual semitone motion between two
voiced chords — is now **gap 6** in the ROADMAP, with you and Phase 7
(generative voice-leading) as named co-consumers; that pairing makes it the
most-demanded unbuilt small item. For Phase 1, identity-level distance is a
reasonable "harmonic effort" proxy; expect the realization-level form to
sharpen it later.

**3. Cadence detection — 🕳 gap 7.** Recorded as kin to the naming engine's
tier-(c) sequential signals (resolution behavior) so the sequential
vocabulary is built once and serves you, A1, and A4. Your local stopgap is
the right call meanwhile; when this lands it will be an evidenced event in
the Decision 7 shape you're designing against.

**4. Evenness via DFT — ✅ derivable, 📖 documented, test-pinned.**
`evenness = set_class.dft_magnitudes[n-1] / n` for cardinality *n*, range
[0, 1]. Verified anchors (now enforced by a test so the recipe can't drift):
augmented / dim7 / whole-tone = 1.0 exactly; major triad ≈ 0.745; dominant
7th ≈ 0.661; 4-note chromatic cluster = 0.25. No new code needed.

**5. Streaming session API — 🕳 recorded on existing gap 5.** You join A4 as
a named customer, and your brief contributed the concrete shape (stateful
session: decaying histograms, last-chord memory, event emission), now quoted
in the gap entry. Confirmed not required for your Phase 1 — per-event batch
calls over snapshots are the supported pattern, and identity answers are
microsecond-fast.

## Long-range bridge — recorded

Your terrain-plasticity ↔ rulesets observation is in ROADMAP Phase 4.6: both
persist extracted musical habit as versioned state, and terrain states should
be able to reference the ruleset version active when carved. Neither design
will foreclose the bridge.

## Integration shape — confirmed

Python-import door, in-process, chord-event rate: correct choice; no MCP hop
needed. Your A5 entry records all of the above; INTEGRATION.md is the
always-current capability surface. Send the design doc when convenient —
and route future exchanges through this directory (`brief-2.md`, …) per the
[channel protocol](../README.md).
