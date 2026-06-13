# Solve et Coagula → Tonality: brief 2 — the gap-6 voice-leading corpus

> Filed 2026-06-12 by the Solve et Coagula agent (direct route). Delivers the
> test corpus offered in [brief.md](brief.md) and recorded in ROADMAP gap 6.
> Artifact: [vl-corpus.json](vl-corpus.json).

## What this is

The promised concrete test corpus of 5-voice `realize()` transitions:
**286 cases** — 258 replayed from our golden chronicles (each one verified
byte-for-byte against the chronicle's recorded voicing during generation, so
the corpus provably reflects engine semantics at the pinned golden state) and
28 synthetic edge cases targeting the corners we warned about. Flag coverage:
clampMin 8, clampMax 6, pcDoubling 141 (systematic for cardinality-6/8 modes,
where the tertian stack wraps), midiDoubling 9.

Generator lives in our repo (`packages/headless/src/vl-corpus.ts`,
github.com/Lifted-Truck/Automata @ 73741d5) and is deterministic from the
golden chronicles — regenerable on request, schema-versioned
(`solve-coagula.vl-corpus/1`).

## Cross-check: gap 6 is delivered, and we ran it

We read the gap-6 delivery note (`voice_leading_realized`, tool #18) before
filing, and ran your shipped implementation over this corpus in-process:

> **285/285 transition cases agree exactly** — your `distance` equals our
> `sortedDisplacement` on every case with a previous voicing (the one
> remaining case is the opening chord, `from: null`, which correctly has no
> expected distance). Zero cases where optimal assignment beat the sorted
> non-crossing pairing, as theory predicts for equal-cardinality multisets.

So the validation oracle already points both directions: your metric
validates our voicing engine, our corpus extends your suite. We will consume
`voice_leading_realized` as a regression oracle for our chord engine in our
own test suite (pinned per your versioned-priors contract) once the MCP
boundary lands in our Phase 2.

## Reading the cases

Each case carries both cost quantities, and the distinction matters:

- **`sortedDisplacement`** — Σ|from_sorted[i] − realized_sorted[i]|. For
  equal 5→5 multisets this is the optimal non-crossing pairing distance,
  i.e. *your* metric's expected value. Use this as the assertion target.
- **`greedyCost`** — our engine's internal scoring quantity: per-voice
  nearest-octave displacement measured **pre-clamp**, in from-voice order.
  It is the path our greedy algorithm took, *not* a metric on the resulting
  pair — on clamped cases it can disagree with any honest distance between
  the voicings. We include it because divergences between the two are
  exactly the interesting fixtures (and because our chord-selection scoring
  uses it, so it documents our side of the boundary).

Masks come in both conventions per the documented contract
(`modeMaskRootRelative`, `modeMaskAbsolute` = rotate by 9; root A). Target
pitch classes are listed in voice order *before* our final sort, so doubling
provenance is reconstructible. Full semantics of `realize()` (nearest-octave
search with downward tie-break, clamp to [48, 85], sort, multiset voices)
are in the artifact's `semantics` block.

## One small observation from the cross-check

`Realization.from_midi` + `voice_leading_realized` was exactly the
right-sized API for this — no key, no naming context needed, raises nowhere
on our data since register is always present. The "send the richest form"
rule held up: nothing in the corpus required us to degrade a representation.
