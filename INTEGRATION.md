# Tonality — Integration Summary

> A capability schematic for **external projects** (synthesizers, MIDI/sound
> generators, visualizers, agents) preparing to plug into this engine. Current
> as of Phase 4 (2026-06). Plans referenced here live in
> [ROADMAP.md](ROADMAP.md) — the single source of truth for direction; this
> document describes **what exists** and links phases for what doesn't yet.

## What Tonality is

A local-first Python **music-theory engine** for 12-TET pitch material. It does
the *exact* pitch-class arithmetic that humans and LLMs get wrong: set-class
identity, exhaustive chord naming, symmetry, key induction, voice-leading
distance — and turns MIDI or symbolic notation into **enriched, reproducible
datasets**. It is a foundation **library with an MCP endpoint**, not an app:
your project keeps its UI, audio, scheduling, and rendering; Tonality supplies
the harmonic brain.

**Division of labor (the design law):** precise combinatorics live in the
engine; fuzzy/semantic/creative judgment lives in the caller. Corollary
(*"reduce, never invent"*): the engine never fabricates what you didn't give
it — no register without real notes, no key without evidence. Analyses that
need missing information **error, they don't guess**.

## The data model in 30 seconds

- **Identity key** — a pitch-class set as a 12-bit bitmask (mod-12, octaveless).
  What you match, name, and catalog on.
- **Realization** — actual pitches (octaves, doublings, bass). Optional, and
  required for register-aware analysis (voicing, inversion, bass-driven
  disambiguation).
- **Time** — `Event` (onset/duration in beats + pitch) → `Sequence` (+ tempo
  & meter maps). Windows reduce to realizations reduce to identity keys.

Integration rule of thumb: **send the richest form you have.** MIDI numbers
beat pitch classes beat names; events with durations beat bare note lists —
each level unlocks more analysis.

## Capabilities (today, shipped and tested)

| Capability | What you get |
|---|---|
| **Multi-notation parsing** | `"C3[0,4,7]"`, `"(1,b3,5)"`, `"[C,E,G]"`, `"{60,64,67}"`, `"C:min7"` → one structured spec |
| **Chord / scale analysis** | intervals, interval vector, symmetry axes, inversions + figured bass, Tonnetz coordinates, modes |
| **Set-class identity** | normal order, Rahn prime form, Z-partners, **DFT magnitudes** (a 6-D "harmonic color" embedding: \|f₅\|≈diatonicity, \|f₆\|≈whole-tone-ness) |
| **Exhaustive naming** | every valid (root, quality) reading of a pc set — symmetric/ambiguous sets yield several (C6 = Am7; dim7 names at 4 roots) |
| **Key induction** | ranked key candidates with scores + top-two margin from duration-weighted pc content |
| **Contextual disambiguation** | *the* chosen reading in a key, with ranked alternatives and per-signal evidence; flags aug-6ths, secondary dominants, Neapolitans; honest `is_ambiguous` |
| **Voice-leading distance** | exact minimal motion between two chord identities + the optimal voice mapping |
| **Voicing analysis / suggestions** | recognition of real voicings (inversion, spread, named type); generative suggestions (closed, drop-2/3, rootless, shell) |
| **MIDI file pipeline** | SMF → events → stable-harmony segments → inferred key → enriched per-segment dataset records (JSON-ready) |
| **MIDI export** | `Sequence` → SMF (single track; tempo/meter, velocity, channel preserved) — the write-back loop for transformers/generators |
| **Catalog** | ~35 scales / ~40 chord qualities with aliases, extensible per session |

**Performance:** identity analyses are table-driven over the 4096 possible
pitch-class sets and answer in **microseconds** after first touch. Current
APIs are whole-sequence (batch), not incremental — see "Coming" below.

## Three doors in

1. **Python import** (in-process): `from mts.analysis import analyze_chord,
   infer_key, name_chord, voice_leading, ...` — typed frozen dataclasses, each
   with `to_dict()`. Best for Python-native projects and lowest latency.
2. **MCP endpoint** (cross-language / agent-facing): `pip install 'mts[mcp]'`,
   then `python -m mts.mcp` (stdio). 17 tools mirroring the library surface,
   including `midi_file_analysis` (file → key-aware dataset in one call) and
   catalog discovery (`list_scales`, `list_chord_qualities`). Inputs accept
   note names (`"C"`, `"F#"`, `"Bb"`) or pc ints; MIDI numbers for register.
3. **Dataset artifacts** (offline/pipeline): JSON `DatasetRecord`s with an
   explicit `SCHEMA_VERSION`, a numeric canonical core, provenance, and
   context snapshots — built for reproducible interchange between projects.

## Contracts to design around (important)

- **Answers are plural and evidenced.** Results carry ranked alternatives,
  per-signal evidence, and `is_ambiguous`. C6 vs Am7 *without a bass note or
  key is genuinely ambiguous and the engine says so* — consume the ranking;
  don't assume a single label.
- **Conditional on context.** Namings are labeled with the key context that
  produced them. Different key → possibly different reading, by design.
- **Versioned priors.** Anything empirical (key profiles, naming weights,
  VL cardinality policy) is a versioned asset cited in results. Pin versions
  if you need byte-stable outputs across engine upgrades.
- **Numeric core, spelling at the edge.** Analysis results are pitch-class
  numbers; note *spelling* (F# vs Gb) and label style are rendered separately
  from a display context. Visualizers: consume the numeric core and either
  render your own labels or request spelled views.
- **Errors over guesses.** No realization → register-aware analysis raises.
  No key → naming runs intrinsic-only and flags ambiguity. Silence/uniform
  input → key induction raises. Handle these as signals, not failures.

## Coming (prepare for, don't depend on yet — phases in ROADMAP.md)

- **Local key tracking** (modulation-aware splitting; Phase 3.5b extension).
- **Representation layer** (Phase 5) — *for visualizers*: typed, render-
  agnostic descriptions of clock/bracelet diagrams, Tonnetz, circle of
  fifths, piano-roll/keyboard views, each declaring the input it requires.
  Plan to consume structured description data, not pixels.
- **Generative voice-leading realization** (Phase 7) — *for generators*:
  progression → concrete voicings with parameterized smoothness/contour/
  register, plus scale re-mapping, meter re-mapping, modulation path
  planning, instrument-class profiles.
- **Live/streaming + incremental APIs** (A4 gaps) — *for real-time tools*:
  today's APIs are batch; rolling/incremental forms are recorded, not built.
  Real-time integrators: design a clean event boundary now (note on/off with
  timestamps) so a streaming adapter can slot in later, and prefer pull-based
  queries against the batch API in the interim (it is fast enough to re-query
  per phrase, just not per note).
- **Compositional rulesets** (Phase 4.6 / Decision 8) — *for everyone,
  eventually the biggest one*: a declarative, JSON-serializable constraint
  syntax over the engine's analytical vocabulary. Rulesets will be
  first-class versioned artifacts flowing in both directions: **impose** one
  on generation or analysis (conformance reports with violation locations),
  **derive** candidate rulesets from existing material (a narrowable
  rule-space), and **compare** rulesets (shared rules, conflicts, empirical
  profiles). An LLM can translate a theory text into the DSL through MCP;
  the engine validates and evaluates it exactly. *What to anticipate:*
  generators — a ruleset becomes the "style" parameter, and your output can
  be checked against one; analyzers/visualizers — conformance reports are a
  new renderable result type; all projects — rulesets are JSON artifacts you
  can store, version, and trade between projects like patches. The
  supporting vocabulary expansion (voice identity, melodic contour,
  rhythmic patterns) is recorded alongside it.

## What to send back (per candidate project)

To prepare an integration schematic, each project should answer:

1. **What it produces/consumes:** MIDI events? note lists? audio (out of
   scope — Tonality is symbolic-only)? Does it have durations/velocities?
2. **Which capabilities it wants** (from the table above) and at what
   granularity (per note / per chord / per phrase / per file).
3. **Latency budget:** offline, interactive (~100ms), or hard real-time.
4. **Direction:** analysis only (Tonality reads your output), generation
   (Tonality proposes material you realize), or both.
5. **Integration door:** Python import, MCP, or dataset files.
6. **Spelling/labeling needs:** raw numbers, or spelled note names / chord
   symbols / roman numerals for display.

Send those six answers per project and we can map each onto the capability
table, identify gaps, and record the integration as a target application in
[ROADMAP.md](ROADMAP.md).
