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
| **Key induction** | ranked key candidates with scores + top-two margin from **any non-negative pc-weight 12-vector** (summed durations, exponentially-decaying histograms, velocity-weighted counts — your weighting policy, our ranking) |
| **Local key tracking** | windowed key induction over a sequence → **key regions** (beats + seconds extents, per-region mean score/margin, per-window evidence) — modulation-aware splitting and renderable overlays; window geometry caller-set and cited; no smoothing (gate on `mean_margin`) |
| **Contextual disambiguation** | *the* chosen reading in a key, with ranked alternatives and per-signal evidence; flags aug-6ths, secondary dominants, Neapolitans; honest `is_ambiguous` |
| **Voice-leading distance** | exact minimal motion between two chord identities + the optimal voice mapping; **register-aware form** for voiced chords (actual MIDI notes — octaves cost 12, doublings are voices) via `voice_leading_realized` |
| **Voice identity & pair motion** | `Event.voice` part labels (MIDI seeds one voice per track/channel as `t{n}c{n}`); `voice_motion` classifies every voice-pair transition — parallel / similar / contrary / oblique with mod-12 interval classes as evidence. Counterpoint predicates are one-line filters (parallel fifths = `parallel` + `interval_class 7`) |
| **Melodic atoms** | per-note approach/departure intervals with step/skip/leap classes, Parsons contour, ambitus (`analyze_melody`); **NHT typing** (passing, neighbor, appoggiatura, escape, suspension, anticipation, pedal) against caller-provided harmony spans — no harmony, no claim |
| **Rhythmic atoms** | per-note metric placement (downbeat / beat / offbeat / subdivision) against the felt beat (compound meters beat in threes), a precise **syncopation** predicate (weak onset sounding through the next stronger grid line), durations + inter-onset intervals (`analyze_rhythm`) |
| **Swing feel** | straight / swung / reversed / mixed from two-way beat divisions, with the division-fraction evidence and ratio (2/3 → 2:1 triplet swing, 0.75 → 3:1 shuffle); thresholds are a **versioned prior** (`swing-feel.1`, cited). Only reads swing encoded in the onsets — quantized-straight MIDI carries none (`analyze_swing`) |
| **Rulesets (DSL) + conformance evaluator** | declarative JSON rules over the atom vocabulary (voice motion / melody / rhythm): `where`-filtered `forbid`/`require`, hard or soft-weighted. Strict total validation (`validate_ruleset` returns *every* error — built for LLM-translated rulesets); `evaluate_ruleset` → per-rule violations with locations + atom evidence, conformance frequencies, hard/soft rollups. Rules the material can't ground come back `applicable: false` with the reason — never silently skipped |
| **Voicing analysis / suggestions** | recognition of real voicings (inversion, spread, named type); generative suggestions (closed, drop-2/3, rootless, shell) |
| **MIDI file pipeline** | SMF → events → stable-harmony segments → inferred key → enriched per-segment dataset records (JSON-ready) |
| **MIDI export** | `Sequence` → SMF (single track; tempo/meter, velocity, channel preserved) — the write-back loop for transformers/generators |
| **Catalog** | ~35 scales / ~40 chord qualities with aliases, extensible per session |
| **Catalog containment query** | every catalog scale/quality that **contains** a pc set, at which roots — tightest containers first, exact matches flagged, absolute rooted masks (`find_containers` / `catalog_containment`) |

**Performance:** identity analyses are table-driven over the 4096 possible
pitch-class sets and answer in **microseconds** after first touch. Current
APIs are whole-sequence (batch), not incremental — see "Coming" below.

### Recipes (derived values consumers asked about)

- **Chord evenness** (distance from the nearest perfectly even chord, for
  spectral/timbral mappings): for a chord of cardinality *n*,
  `evenness = set_class.dft_magnitudes[n-1] / n` ∈ [0, 1]. Verified anchors:
  augmented triad / dim7 / whole-tone = 1.0 exactly; major triad ≈ 0.745;
  dominant 7th ≈ 0.661; a 4-note chromatic cluster = 0.25.
- **Voice pairing as evidence**: both VL metrics return not just the distance
  but the optimal `mapping` of voice pairs — `[from_pc, to_pc]` at identity
  level (`voice_leading`), `[from_midi, to_midi]` at register level
  (`voice_leading_realized`) — consume them directly as per-voice motion
  vectors. Same named cardinality policy (`doubling.1`) on both.
- **Key-induction margin as a control signal**: `margin` is the difference
  between the top two candidates' Pearson correlation scores under the cited
  profile version — a continuous confidence value in [0, 2], in practice
  ~0–0.5. **Stability contract:** these semantics hold per profile version;
  a different prior version may shift absolute values, which is exactly why
  results cite the version — pin it if you map margin to a control curve.
- **Near-silence contract**: all-zero or perfectly uniform pc weights raise
  (no tonal information — the engine won't guess). Streaming consumers with
  decaying histograms should gate induction calls on total weight.
- **Mask bit convention**: Tonality masks are *absolute* — bit *n* = pitch
  class *n* (C=0), the same integer convention as Ian Ring's scale numbers.
  If your project keeps *root-relative* masks (bit 0 = your root), convert
  with `rotate_mask(mask, root_pc)`. Set-class identity (prime form, Ring
  number, DFT) is exhaustive over all 4096 sets — catalog *names* exist only
  for cataloged sets, but identity never requires the catalog.
- **Per-segment records, not roll-ups**: `midi_file_analysis` /
  `dataset_from_sequence` return one record per stable-harmony segment, each
  carrying `placement` (onset/duration in beats *and* seconds, bar/beat),
  `interpretations`, and key-conditional `naming` — directly renderable as
  timeline overlays. Shape: `DatasetRecord.to_dict()` with `SCHEMA_VERSION`
  for pinning (`mts/dataset/record.py` is the schema of record).

## Four doors in

1. **Python import** (in-process): `from mts.analysis import analyze_chord,
   infer_key, name_chord, voice_leading, ...` — typed frozen dataclasses, each
   with `to_dict()`. Best for Python-native projects and lowest latency.
2. **MCP endpoint** (cross-language / agent-facing): `pip install 'mts[mcp]'`,
   then `python -m mts.mcp` (stdio). 26 tools mirroring the library surface,
   including `midi_file_analysis` (file → key-aware dataset in one call) and
   catalog discovery (`list_scales`, `list_chord_qualities`). Inputs accept
   note names (`"C"`, `"F#"`, `"Bb"`) or pc ints; MIDI numbers for register.
3. **Dataset artifacts** (offline/pipeline): JSON `DatasetRecord`s with an
   explicit `SCHEMA_VERSION`, a numeric canonical core, provenance, and
   context snapshots — built for reproducible interchange between projects.
4. **Local HTTP bridge** (browser / non-Python consumers): `python -m
   mts.mcp.bridge` (stdlib only — no extra install) serves every MCP tool
   over loopback HTTP, default `http://127.0.0.1:8012`. Discover with
   `GET /tools` (name, doc, params per tool); invoke with
   `POST /call/<tool_name>` and a JSON object of keyword arguments →
   `{"ok": true, "result": ...}`. Bad input is a 400 carrying the engine's
   actionable message; CORS is open (the boundary is loopback, not origin).
   Same signatures and `to_dict()` shapes as the MCP endpoint — the bridge
   is glue, not a second API (ruled 2026-06-11; shipped as ROADMAP gap 9).
   Hosted endpoints remain declined (local-first); a WASM core remains an
   explicit non-commitment.

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
- **Send grid-exact events (for now).** The temporal analyses (segmentation,
  metric placement, voice motion) treat onsets as exact: humanized/performed
  timing fragments segmentation into micro-segments and reads on-the-beat
  notes as off-grid subdivisions. Until the engine-side tolerance layer
  lands (ROADMAP gap 12), quantize or coalesce near-simultaneous onsets
  before sending (Audiology's ~60 ms client-side coalescing is the working
  precedent). Swing/groove material is the exception that *should* keep its
  encoded offsets — see the swing row's caveat.
- **Key candidates span the loaded profile modes** — major and minor under
  `kk-1982.1`. Modal material (a dorian vamp) will rank as its relative
  major/minor rather than its modal tonic; modal profile rows join the
  standing Temperley/Aarden invitation if you need modal centers ranked.
- **Numeric core, spelling at the edge.** Analysis results are pitch-class
  numbers; note *spelling* (F# vs Gb) and label style are rendered separately
  from a display context. Visualizers: consume the numeric core and either
  render your own labels or request spelled views.
- **Errors over guesses.** No realization → register-aware analysis raises.
  No key → naming runs intrinsic-only and flags ambiguity. Silence/uniform
  input → key induction raises. Handle these as signals, not failures.

## Coming (prepare for, don't depend on yet — phases in ROADMAP.md)

- **Cadence detection as evidenced events** (gap 7) — V–I and related
  root-motion patterns as discrete, evidence-carrying events. Consumers:
  TERRANE home-center impulses, A1, A4.
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

**Where answers land:** file them as `integrations/<project>/brief.md` in
this repo (directly via a PR, or relayed through Julian) — see
[integrations/README.md](integrations/README.md) for the channel protocol.
Tonality's agent triages every brief into a per-request verdict
(`integrations/<project>/response.md`), verifies "already shipped" claims in
code, records the project as a target application in
[ROADMAP.md](ROADMAP.md), and documents anything usable today back into this
file. Worked example: [integrations/terrane/](integrations/terrane/).
