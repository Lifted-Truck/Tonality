# Tonality — Roadmap & Architecture Decision Record

> **Single source of truth for project direction.** The build sequence,
> decisions on record, target applications, and deferred/demoted scope all live
> here. Forward-looking statements anywhere else in the repo (README, per-layer
> CLAUDE.md files, docstrings) defer to this file — link the relevant phase
> instead of restating the plan. When a planning decision is made *or rejected*,
> fold it in here in the same PR; a decision that isn't recorded here isn't
> decided.

This is the strategic companion to [CLAUDE.md](CLAUDE.md). CLAUDE.md says *how to
work in the code*; this says *where we are going and why*.

## North star

A **foundation library** with an **MCP endpoint** that lets AI agents analyze music
and turn varied notations — both timeless symbolic identities and time-based
material — into **enriched, contextualized datasets**.

Success looks like: an agent feeds in a notation (a chord expression, a scale, a
MIDI clip), and gets back structured records annotated with functional role,
compatible scales, interval/symmetry properties, voicing data, and temporal
context — reproducibly.

Longer term, the engine should not merely *enumerate* the possible names/analyses of
a chord or passage but **choose the reading its context actually warrants** — and,
when readings genuinely conflict, surface the competing interpretations ranked by
corpus statistics, with evidence. The aspiration: a tool that can reveal *novel*
music-theoretical readings of existing music, not just confirm textbook ones.

## Target applications (what the engine must make possible)

Concrete programs we want to plug the engine into. These are **edge consumers,
not in-repo features** (same relationship MCP and rendering have to core —
library-first stands). Their value here is as *acceptance tests*: each one
decomposes into engine capabilities, and any capability no phase provides is a
gap to record, not a thing to improvise later. Added 2026-06-10; extend this
list as new applications come into view.

- **A1 — Key-aware MIDI analyzer.** Read a MIDI file → infer what key/scale it
  is in, split it at key changes, and emit per-section analysis (scale, chords,
  functional roles) as an enriched dataset.
  *Capabilities:* MIDI ingestion ✅ (Phase 2) · segmentation ✅ (Phase 2, literal;
  harmonic refinement parked) · global key induction ✅ (Phase 3.5b) ·
  key-change splitting = local key tracking ✅ shipped (3.5b extension,
  2026-06-11: `track_keys` key regions; `midi_file_analysis` carries them) ·
  per-section enrichment ✅ (Phase 3 dataset records).
- **A2 — Smart MIDI transformer.** Apply musically-aware transformations to an
  existing MIDI file: re-voice chord progressions; add or alter voices; change
  scale intelligently (preserve contour and degree-function, not literal
  pitches); change the time signature; insert key changes with coherent
  movement (circle-of-fifths paths, or some other stated musical bias).
  *Capabilities:* analysis side ✅/planned as above · re-voicing + added voices →
  **Phase 7** (voice-leading realization) · scale re-mapping, meter re-mapping,
  modulation path planning → **Phase 7 extensions** (recorded there) ·
  **groove apply — gap 10** (its first concrete transformation) · writing
  the result → MIDI export ✅ shipped (Phase 2 addendum).
- **A3 — Complementary part generator.** Given a MIDI file, generate companion
  MIDI for different instrument classes (bass line, pad, lead, counter-melody)
  that is harmonically and rhythmically coherent with the source.
  *Capabilities:* full analysis pipeline (A1) · Phase 7 generation constrained
  by **instrument-class profiles** (register range, polyphony, idiom) — a new
  data vocabulary; ships as versioned priors (Phase 3.5 pattern) · MIDI export.
- **A4 — Live MIDI companion** *(added 2026-06-10)*. A device/plugin that
  listens to what is being played and composes complementary MIDI **in real
  time** — A3's brain under a latency budget. The device frame itself
  (hardware/plugin/app, scheduling, audio I/O) is an edge consumer; the
  engine supplies analysis + generation. This is the most demanding entry on
  the list: it needs essentially everything A1+A3 need, **plus** two
  capabilities no phase currently provides.
  *Capabilities:* offline analysis/generation stack — as A1/A3 ·
  **live MIDI input** — streaming was *explicitly* descoped in Phase 2
  (`events_from_live_midi` is `NotImplementedError`); A4 is its first real
  demand driver (stays descoped until A4 is scheduled — recorded, not
  re-scoped) · **online/incremental analysis APIs** — today every analysis
  is whole-sequence; A4 needs rolling forms (incremental `pc_weights` + key
  tracking, rolling segmentation, per-window naming). Raw compute is *not*
  the gap — the cached mask-space tables answer in microseconds; the gap is
  API shape (update state, don't recompute from zero) · Phase 7 generation
  under a latency budget + instrument-class profiles (A3).

- **A5 — TERRANE** *(added 2026-06-11 from the project's relay brief; intake
  closed by brief 2 — design doc: github.com/Lifted-Truck/Terrane, §11 is the
  TERRANE-side mirror of the exchange)*. An adaptive synthesizer in
  early design: sound is a function of performance history — a particle with
  mass/friction moves through a timbre space whose terrain is reshaped by
  harmonic state, *relational* to a slowly-drifting, confidence-gated "home"
  tonal center. Division of labor mirrors our thesis exactly: TERRANE owns
  dynamics, terrain, and feel; all exact pc analysis is delegated here.
  Queries at chord-event rate (seconds), so **batch APIs suffice for its
  Phase 1** (Python import door, in-process; browser frontend is
  visualization only). Epistemically aligned by design: key-induction margins
  and ambiguity are *rendered* (terrain ruggedness, gated home-pull), not
  worked around — margin semantics are therefore a stability contract
  (documented in INTEGRATION.md).
  *Capabilities:* weighted-distribution key induction ✅ shipped — `infer_key`
  takes any non-negative 12-vector, so decaying pc histograms work today;
  profiles are swappable versioned priors, and **Temperley/Aarden profile
  variants are welcome as additional `key_profiles.json` entries** ·
  identity-level VL distance with the voice pairing as evidence ✅ shipped
  (the `mapping` field) · **realization-level VL transitions — gap 6 below** ·
  chord evenness ✅ derivable from the DFT embedding
  (`dft_magnitudes[n-1] / n`; mapping documented in INTEGRATION.md) ·
  **cadence detection — gap 7 below** (TERRANE stopgaps locally meanwhile) ·
  streaming session API — gap 5; TERRANE joins A4 as a named customer while
  explicitly *not* requiring it for Phase 1.
- **A6 — AUDIOLOGY** *(added 2026-06-11 from its brief —
  `integrations/audiology/`)*. A browser SPA (TypeScript/React, local-first,
  no backend): a Push-3-style scale/chord **explorer** (8×8 grid + keyboard,
  scale-membership coloring), a MIDI-file **player/analyzer** (WebAudio
  transport, canvas piano-roll), and a **live-play** surface (Web MIDI /
  computer keyboard) with a three-mode chord card. Wants to retire its two
  naive-TS theory functions (`analyzeSelection`, `scalesContaining`) in favor
  of engine calls; already lives by the contracts (plural answers, numeric
  core, errors-as-signals, sends richest form incl. bass). Interactive
  (~60–100 ms) pull-based; no hard real-time.
  *Capabilities:* bass-aware chord naming + inversion recognition ✅ shipped
  (`name_pcs` + `voicing_analysis`) · file-level key induction + per-segment
  dataset with placements ✅ shipped (`midi_file_analysis`) · per-segment keys
  ✅ shipped (local key tracking, 2026-06-11 — key regions in beats+seconds,
  renderable as overlays; `key_tracking` tool + `midi_file_analysis`) ·
  catalog of record ✅
  shipped (`list_scales` / `list_chord_qualities`) · pc-set containment
  query ✅ shipped (gap 8 below; `catalog_containment` — retires its naive
  `scalesContaining`) · voicing recognition/suggestions ✅ shipped ·
  browser door ✅ shipped (gap 9 below; `mts.mcp.bridge`, the local HTTP
  bridge — was the blocking question) · named consumer of the **Phase 5
  representation layer** (keyboard + piano-roll descriptors; its three
  surfaces are ready render targets).
- **A7 — SOLVE ET COAGULA** *(added 2026-06-11 from its brief —
  `integrations/solve-coagula/`; repo: github.com/Lifted-Truck/Automata)*.
  A generative instrument: a K=6-state cellular automaton under Glauber
  dynamics whose musical mode (root-fixed, walking the 2,048-vertex mode
  hypercube) *generates the physics*; a pure deterministic TS core emits a
  byte-exact event chronicle, with Tonality strictly in adapters and offline
  enrichment (core purity is absolute). Chronicle fixtures make **versioned
  priors a regression-grade dependency** — the strongest consumer yet of
  that pattern. MCP + dataset doors; chord/epoch-rate pull; no hard
  real-time for us.
  *Capabilities:* voicing naming + disambiguation ✅ shipped · exhaustive
  12-bit mode identity (prime form / Ring number for arbitrary sets, beyond
  the named catalog) ✅ shipped, verified — with the **root-relative →
  absolute mask rotation contract** documented in INTEGRATION.md · DFT
  magnitudes / evenness as CC signals ✅ shipped · velocity-weighted decaying
  key induction ✅ shipped (margin as confidence CC) · VL distance ✅
  identity-level; joins **gap 6** with a **test-corpus offer** (recorded
  there) · MIDI export + dataset enrichment ✅ shipped · prospective **Phase
  4.6 induction consumer** ("derive the idiom from the affinity matrix");
  a sibling instrument is noted as a likely second consumer of the same
  doors.

**Gaps this list surfaces (recorded, not yet scheduled):**
1. **MIDI export** — ✅ shipped (Phase 2 addendum): `sequence_to_midi_file`
   (`Sequence → SMF`, single track, tempo/meter/velocity/channel preserved,
   round-trip tested). This entry predated delivery; corrected 2026-06-12.
2. **Generative transformations** (scale re-mapping, meter re-mapping,
   modulation path planning) — Phase 7 extensions; all generative-side per the
   cardinal rule.
3. **Instrument-class profiles** — versioned data vocabulary for A3.
4. **Live MIDI input** (A4) — streaming `events_from_live_midi`; stays
   explicitly out of scope until A4 is scheduled.
5. **Online/incremental analysis APIs** (A4, A5) — rolling-window key
   tracking, segmentation, and naming that update state instead of
   recomputing; a stateful session object (decaying histograms, last-chord
   memory, event emission) is the natural shape (per the TERRANE brief).
   The *online* sibling of the now-shipped batch local key tracking (the
   stateful form would update windows incrementally instead of re-sliding).
   Not required for TERRANE Phase 1 — per-event batch calls over snapshots
   suffice.
6. **Realization-level voice-leading distance** (A5, A7; also Phase 7) — the
   shipped `voice_leading` is identity-level (mod-12 circular). The
   register-aware sibling measures actual semitone motion between two voiced
   `Realization`s, optimal assignment with the pairing as evidence, doubling/
   omission for unequal voice counts. Consumed by TERRANE as "harmonic
   effort" and by Solve et Coagula as a **validation oracle** for its own
   nearest-octave voicing engine — which has offered a concrete test corpus
   (5 voices, permitted doublings, range clamps root+3..root+40) to seed
   this gap's test suite; Phase 7 wants the same metric for scoring realized
   voice leading. **Delivered (2026-06-11):** `voice_leading_realized`
   (analysis + MCP tool #18) — actual-semitone motion over sorted MIDI
   multisets (octaves cost 12; doublings are voices), optimal pairing exact
   via linear non-crossing (sorted index-wise for equal voices; contiguous
   blocks for unequal), brute-force-verified including 5-voice
   doubled/clamped cases shaped like the offered corpus. Register required —
   raises on `None` per the cardinal rule. The S&C corpus remains welcome to
   *extend* the suite when it arrives.
7. **Cadence detection as evidenced events** (A5, A1, A4) — V–I and related
   root-motion patterns emitted as discrete events with per-signal evidence
   (Decision 7 shape). Kin to the Slice 5 tier-(c) sequential signals —
   build the sequential vocabulary once, serve both.
8. **Catalog containment query** (A6) — "which catalog scales/qualities
   contain this pc-set, at which roots." Ruled **engine-side** (exact
   combinatorics); the first concrete slice of the parked constraint-search
   vision, cheap over the cached tables. Retires Audiology's naive
   `scalesContaining`. **Delivered (2026-06-11):** `find_containers`
   (`analysis/containment.py`) + MCP tool `catalog_containment` (#19; the
   HTTP bridge exposes it automatically). Reverse of compatibility — the
   container transposes, the query stays absolute (`containing_roots`,
   mask-cached in `pcset_math`). Tightest containers first, exact matches
   flagged (modal spellings of one mask are distinct exact answers),
   symmetric containers report every valid root; takes explicit catalog
   mappings so session catalogs are searchable. No ranking policy — pure
   subset combinatorics, deterministic ordering only.
9. **The web door** (A6; the Phase 5 visualizer class) — browsers cannot
   spawn the stdio MCP server. Sanctioned shape, ruled 2026-06-11: a thin
   local HTTP bridge over the existing pure `mts.mcp.tools` functions
   (Decision 5-compliant glue; tools already return JSON-ready dicts).
   Hosted endpoint declined (local-first); WASM noted as an explicit
   non-commitment. **Delivered (2026-06-11):** `mts.mcp.bridge` — stdlib-only
   (`http.server`, zero new dependencies), `python -m mts.mcp.bridge`,
   loopback-bound at `127.0.0.1:8012` by default. `GET /tools` introspects
   every tool (name, doc, params from the live signatures — new tools appear
   automatically); `POST /call/<name>` invokes with JSON kwargs; engine
   `ValueError`s surface as 400s with their actionable messages; CORS open
   because the boundary is loopback, not origin. The tool signatures and
   `to_dict()` shapes remain the only contract — consumers who stood up
   interim bridges swap by changing a URL.
10. **Groove extract / apply** (added 2026-06-12, prompted by Julian —
    Ableton Live's Extract Groove is the reference model). Two halves on
    opposite sides of the cardinal rule:
    *Extract* (analysis) — distill a `GrooveTemplate` from a symbolic loop:
    per grid slot at a chosen base resolution, the signed onset offset (as a
    fraction of the grid unit) and velocity, cycled over the loop length.
    Builds directly on the rhythmic atoms; `analyze_swing` is the
    one-parameter special case (a groove template generalizes the division
    fraction to arbitrary per-slot offsets). Same honesty bound as swing:
    quantized input yields a null groove — the feel must be in the onsets.
    *Apply* (generative) — **A2's first concrete transformation**: new
    `Sequence` with onsets pre-quantized by a quantize %, interpolated
    toward template offsets by a timing %, velocities scaled by a signed
    velocity % (negative reverses, per the Live model); a random component
    requires an explicit seed (same-input-same-output is an engine
    invariant). Parameter vocabulary maps 1:1 onto Live's Groove Pool
    (Base / Quantize / Timing / Random / Velocity / Amount), so grooves
    round-trip conceptually with DAW workflows. Boundary: extraction from
    *audio* stays consumer-side per Decision 9 — consumers send onsets,
    never audio. Template extraction policy knobs (if any emerge) ship as
    versioned priors. Depends on gap 11 only for *trustworthiness*: a wrong
    declared grid poisons offsets, but extraction against a correct
    declared grid works today.
11. **Meter estimation** (added 2026-06-12; promoted from the theory-
    grounding review agenda's "we trust the file's time signature"). The
    time system is declarative: `MeterMap` answers every bar/downbeat
    question exactly, but only from file meta — there is no inference of
    time signature, meter changes, or bar lines from note content, and a
    loop exported with default 4/4 meta poisons every metric judgment
    downstream (rhythmic atoms, syncopation, swing, groove extraction).
    Wanted: batch estimation — ranked candidate signatures with scores and
    margin (Decision 7 shape; profile-correlation over onset/accent
    autocorrelation is the classic method family), change-point detection
    for meter changes, and a declared-vs-estimated disagreement signal
    rather than silent override (the engine never replaces the file's
    claim — it evidences against it). Empirical templates ship as
    versioned priors. The *online* form joins gap 5's session, as with
    key tracking.
12. **Performed-input tolerance** (added 2026-06-12; theory-grounding
    review pass #1's headline finding — A1/A6 feed real MIDI to exactly
    these paths). The temporal analysis layer silently assumes
    **grid-exact onsets**: humanized/performed input is *misread, not
    refused*. Verified: two chords with ~5 ms onset jitter segment into
    **ten** micro-segments including garbage transitional pc sets (each of
    which the A1 pipeline would name as a chord); an on-the-beat melody
    with the same jitter classifies as all-`subdivision` in the rhythmic
    atoms; voice-pair motion fragments across micro-moments. (The melodic
    line extractor at least *refuses* — humanized legato overlaps raise
    "not monophonic".) Wanted: an explicit tolerance layer — an onset
    coalescing window (and optional grid snap) applied at `Sequence`
    construction or as a preprocessing pass, **caller-set and cited in
    results** like window geometry, default off so exactness stays exact.
    Audiology already coalesces at ~60 ms client-side — existing demand
    and a working precedent. Until this ships: consumers must quantize or
    coalesce before sending events (interim guidance in INTEGRATION.md).
13. **Per-region analytical context in the A1 pipeline** (added 2026-06-12;
    review pass #1). `midi_file_analysis` now computes local key regions
    *and* still conditions every segment's naming on the single global
    best key — in a modulating file the foreign-key regions get namings
    under the wrong context (a misread the shipped key tracking already
    knows how to avoid). Wanted: per-segment context selection from the
    key region containing the segment's onset, with the global form kept
    as an option; the region's `mean_margin` rides along as the context's
    confidence evidence.
Local key tracking shipped 2026-06-11 (the 3.5b extension — see that entry):
A1's key-change splitting and A6's renderable key regions are served by the
windowed batch form; A4's *online* requirement remains with gap 5.

## Decisions on record (the "why", so we don't relitigate)

1. **Build on the existing engine, don't greenfield.** The bitmask PC substrate,
   immutable core objects, and the multi-notation parser are correct and tested.
   Greenfield would rebuild them nearly identically. The foundation has the right
   *substance*; we are correcting its *frame* (library/MCP, not standalone app).
2. **Time and timeless identity are layers, not opposites.** The identity layer is
   atemporal; the temporal layer sits above and *references* it. (See CLAUDE.md
   "core data model.")
3. **Identity key + optional realization**, with a two-axis lattice
   (transpositional × registral). Register is a *richer* representation that
   reduces to PC — not "secondary metadata." Voicing-sensitive analysis reads the
   realization; matching/naming reads the key.
4. **Reduce, never invent.** Inventing register = choosing a voicing = a generative
   act. Analysis declares the level it needs and errors when it's missing.
5. **The MCP layer is a thin adapter, not a subsystem.** Intelligence stays in the
   engine. MCP is the first *consumer* and a forcing function for clean APIs.
6. **Keep the tuning system behind a reduction boundary.** "The identity key *is* a
   12-bit bitmask" is a 12-TET-specific choice we accept for now (the substrate is
   correct and tested; a generalized identity type is premature). To keep the
   eventual multi-system generalization (see Phase 6) from being a teardown, the
   **lattice** (transpositional × registral) and the **Realization** API are
   deliberately tuning-agnostic — rooted-ness and register-ness are not 12-TET
   concepts. Only `reduce_to_key()` and `core/bitmask.py` know the substrate is 12.
   New code routes through the reduction rather than open-coding `mask` arithmetic,
   so swapping the substrate later is a localized change, not a rewrite.
7. **Disambiguation is ranked, explicit, and plural — never an opaque guess.** When a
   set or passage admits several names/analyses (the candidates `interpret_chord`
   enumerates), the engine selects the contextually-best reading *and* surfaces the
   competing alternatives with inspectable, data-derived weights and the evidence
   behind them. Statistical scoring stays **reproducible** (same input + same corpus
   → same ranking); it never collapses to a single black-box answer. This preserves
   the division of labor: transparent combinatorics + explicit statistics *here*,
   open-ended semantic leaps in the caller.
8. **Rulesets are declarative, serializable, versioned artifacts over the
   engine's own analytical vocabulary** (added 2026-06-11; see Phase 4.6). A
   compositional ruleset is a set of predicates over facts the typed results
   already expose — scoped (per-event / adjacent-pair / phrase / global), hard
   or soft-weighted, declaring the specification level each rule requires
   (cardinal rule applies: a parallel-fifths rule *errors* on voiceless
   material). Rulesets are versioned priors (the Phase 3.5 pattern; the naming
   weight table is the degenerate first instance). **Rule *proposal* is the
   caller's job; rule *verification and evaluation* are the engine's** — an
   LLM translates a treatise into candidate rules in the DSL, the engine
   validates and evaluates them exactly. Rule *induction* is exact
   version-space mining over a template vocabulary, scored against null
   models — statistics, never an in-engine learned black box. Corollary: the
   engine can only express, check, and induce what its analytical vocabulary
   can say — vocabulary expansion (voice, melody, rhythm) is therefore a
   first-class investment, not a side effect.
9. **Audio stays outside — permanently.** (Decided 2026-06-11 after evaluating
   Magenta DDSP for inclusion.) Audio synthesis and audio-domain DSP — neural
   (DDSP/RAVE-class) or otherwise — are consumer-side, full stop. Reasons on
   record: the division of labor *is* the product (exact combinatorics here;
   a learned controls→audio mapping is the opposite kind of object, and
   Decision 8 just barred in-engine learned components); three consumer
   briefs (A5–A7) signed contracts that depend on the symbolic-only boundary;
   neural synthesis is not byte-reproducible in the versioned-priors sense;
   and the dependency footprint is incompatible with a `mido`-sized engine.
   The engine's audio-facing contribution is **descriptor tracks** (typed
   continuous harmonic control signals — see Phase 5), never sound. Which
   synthesis stack a consumer uses (DDSP, RAVE, analog modeling, …) is a
   per-project choice made in *their* repo.

## Build sequence

### Phase 0 — Foundation hardening ✅ DONE
- [x] Encapsulate session state in `SessionCatalog`; kill module-level globals.
- [x] Replace `dict[str, object]` analysis returns with typed result dataclasses.
- [x] Project scaffolding: CLAUDE.md, ROADMAP.md, git hygiene, harness.

### Phase 1 — Formalize the identity model ✅ DONE
- [x] Promote the parser's `scope` (abstract/note/absolute) into a first-class
      identity concept: an explicit lattice cell (transpositional × registral).
      `core/spec_level.py` defines the two axes and four named corners; `scope`
      is kept as an additive compat alias bridged in `specs.py` (`from_scope` /
      `to_scope`). The bridge proves `scope` is a diagonal — it cannot express
      the registered + rootless corner.
- [x] Introduce the **Realization** type (ordered pitches, doublings, bass) as a
      sibling to the identity key; define `realization → key` reduction.
      `core/realization.py`; `reduce_to_key()` is the sole 12-TET reduction
      boundary (Decision 6). `ChordParseResult.to_realization()` builds one from
      the absolute pitches the parser already captured.
- [x] Make the **voicing template** (registered + rootless) expressible — a
      `Realization` with `root_pc=None`.
- [x] Audit analysis functions: tag each with the specification level it requires;
      add the "error, don't guess" guard for register-dependent analysis.
      `analyze_chord` is now pure-identity (no fabricated voicings); register
      analysis moved to the guarded `analyze_voicing` (raises
      `SpecificationError` via `require_realization`); the synthetic stack
      generator moved to the explicitly-generative `suggest_voicings`.

### Phase 1.5 — Vocabulary completeness (voicings + enharmonic equivalence)
Near-term enrichment that deepens the identity model just built. Goal: the engine
knows *all* the standard names a chord/voicing can go by, and recognizes when two
specifications are the same object. Builds directly on the Phase 1 lattice and
`Realization`. **Preserve the division of labor:** *naming/recognizing* an
existing object is analytical; *producing* a voicing is generative.

Workstream A — **named voicings (generation + recognition).**
- [x] A named-voicing vocabulary (generative, `suggest_voicings`): closed,
      open/spread, drop-2 / drop-3 / drop-2&3 / drop-2&4, rootless (A/B), and shell.
      Built as an extensible registry (`_VOICING_BUILDERS`) over the closed stack;
      each voicing declares applicability and exact duplicates are collapsed.
      *Deferred:* quartal/quintal, cluster, and idiomatic named voicings (e.g.
      "So What") — these are voicing *styles* less well-defined per-chord; add as
      registry entries when needed.
- [x] Express register-bearing-but-rootless voicings as **voicing templates** (the
      `REGISTERED + SHAPE` corner Phase 1 unlocked); concrete voicings are
      `Realization`s. (Delivered in Phase 1: `Realization(root_pc=None)`.)
- [x] Inversions as first-class (root position + inversions; figured-bass labels).
      The `Inversion` result carries `position_index` / `position_name` /
      `figured_bass` (triads: 5/3,6,6/4; sevenths: 7,6/5,4/3,4/2; generic position
      name otherwise).
- [x] **Recognition** (analytical, register-required): `analyze_voicing` now reports
      the actual bass `inversion`/`figured_bass`, an `openness` (closed/open), and a
      recognized `voicing_type` matched against the *shared* `voicing_shapes`
      vocabulary (same registry that generates them). *Limits (honest None):*
      recognition is shape-based, so doubled or non-vocabulary spacings return
      `voicing_type=None`; inversion-invariant matching is a future refinement.

Workstream B — **enharmonic & naming equivalence (structural, beyond PC spelling).**
- [x] Add an `aliases` field to `ChordQuality` (parity with `Scale`); catalog the
      common alternate names. Loader registers aliases as extra catalog keys (so
      `C:major`, `A:m7`, `G:dom7` resolve); `_classify_qualities` de-dupes by
      canonical name so aliases never appear as separate matches.
- [x] Model structural equivalence for symmetric / ambiguous sets and surface *all*
      valid names+roots, not just one: `interpret_chord` (in `equivalence.py`)
      enumerates every `(root, quality)` naming — diminished-7th (4 roots),
      augmented triad (3), ambiguous sets (C6 = Am7), and the augmented-sixth
      family via its enharmonic dominant interpretation. *Deferred:* full
      *functional* augmented-sixth labelling (It/Fr/Ger + spelling) is Phase 3
      territory; B2 exposes the pitch-class equivalence it rests on.
- [ ] Reproducibility: the chosen spelling and any equivalence are explicit in the
      result / dataset record (dovetails with the Phase 3 analytical-vs-display
      context split).

### Phase 2 — Temporal layer ✅ DONE
- [x] Replace the `timeline.py` stub with real `Event` / `Sequence` types — the new
      `mts/temporal/` package: `Event` (onset/duration in quarter-note beats +
      `Pitch`), `Sequence` with `sounding_at` / `realization_at` (a window's
      pitches → a rootless `Realization` → identity key), plus **full tempo + meter**
      (`TempoMap` beats↔seconds, `MeterMap`/`TimeSignature` → bars/beats/downbeats).
      `analysis/timeline.py` is now a deprecated shim; migrating `workspace`/`io`
      off it is a tracked follow-up.
- [x] Implement `io/midi.py` ingestion (MIDI file → events). **Decision: mido**
      (runtime dependency; thin adapter so the engine never imports mido directly).
      `sequence_from_midi_file` / `events_from_midi_file` map ticks→quarter-beats,
      pair note on/off (incl. velocity-0), and read `set_tempo`→`TempoMap` /
      `time_signature`→`MeterMap`. Live/streaming MIDI stays out of scope.
- [x] Segmentation + harmonic rhythm: `mts/temporal/segmentation.py` — `segment()`
      partitions a `Sequence` into maximal stable-pitch-class-set spans (`Segment`
      carries pcs/mask + a representative `Realization`; `.interpret()` names it via
      `interpret_chord`); `harmonic_rhythm()` reports segment count, mean duration
      (beats/seconds), and changes-per-bar. Silences dropped; octave doublings don't
      split a segment. *Future:* harmonic (chord-level) segmentation that filters
      non-harmonic tones by metric salience. *(Reframed 2026-06-10, parked after
      Phase 3.5:)* treat it as **cover-maximization** — choose boundaries and one
      catalog identity per span to maximize metrically-weighted explained notes;
      the residue is classified as non-harmonic tones by approach/departure
      intervals over the event graph (passing, neighbor, suspension, anticipation
      are decidable combinatorially). Wants VL-distance (chord-change cost) and
      key induction (Phase 3.5) as inputs — sequenced after both. This is the
      demo-vs-tool gap for real performed MIDI: literal PC-set stability
      over-segments badly on passing tones and arpeggiation.
- [x] **Addendum (2026-06-10, application-driven): MIDI export** — the write-side
      mirror of ingestion: `Sequence` (+ `TempoMap`/`MeterMap`) → Standard MIDI
      File via the same thin mido adapter. Surfaced by the Target-applications
      list (every A2/A3 transformation must close the loop back to a file).
      Small and well-bounded; no new dependency. Round-trip
      (`read → write → read`) is the natural invariant to test.
      **Delivered (2026-06-11):** `sequence_to_midi_file` /
      `midi_file_from_sequence` — single track, tempo/meter maps preserved,
      per-pitch velocity/channel round-trip, note_off-before-note_on ordering
      so re-struck notes survive. Quantization is honest: beats exact at
      480ths; bpm to within SMF's integer-microsecond resolution. Round-trip
      and the full write→analyze loop (A2's skeleton) are tested.

### Phase 3 — Contextualization & dataset schema ✅ DONE
- [x] Resolve the **two "context" concepts**: *display* context pushed to the edge
      — analysis is numeric/PC-only and spelling/labels render via
      `mts/context/result_format.py` from a `DisplayContext` (Slices 1a/1b); and
      *analytical* context made first-class as `AnalyticalContext` /
      `contextualize_chord` (Slice 2). All four CLI scripts now build a
      `DisplayContext` and render through the formatters (Slice 3) — the parked
      `wip-context-cli-rewiring` work was **re-done on current main** (incl. the
      `run_specific` shadowing-crash fix) rather than merged, then retired.
- [x] Define the **dataset record schema** — the enriched unit emitted per musical
      object/event. Reproducible (capture spelling/context choices explicitly).
      Delivered as the new `mts/dataset/` package (Slice 4): a flat-leaf
      `DatasetRecord` (tiers `identity` → `analysis` → optional `realization` →
      optional temporal `placement`, mirroring `event → realization → identity key`)
      grouped by a `Dataset` container, with a numeric **canonical core** plus a
      shed-able reproducibility layer (`source` provenance, `analytical`/`display`
      context snapshots, and a *derived* `display` block) and a `minimal()`
      projection. `SCHEMA_VERSION` is explicit. Builders (`record_from_chord`,
      `record_from_segment`, `dataset_from_sequence`) *assemble* existing typed
      results — they compute nothing new. Lives **above** analysis/temporal/context
      (it imports all three; none import it) — which is why it is not in
      `analysis/results.py` (that would invert the `temporal → analysis.results`
      dependency).

      **Granularity decision & reflection point.** Slice 4 ships **flat leaf records
      + a `Dataset` container**, not a recursive record — the honest fit for today's
      *flat* literal-PC-set `segment()` and flat harmonic-rhythm. Forward-compat is
      preserved by composition: records carry a `kind` level discriminator and a
      stable `index` handle, and `Dataset` is a *grouping*, **not** asserted as a
      flat, non-overlapping, exhaustive timeline partition. **Revisit the
      flat-vs-recursive distinction when a genuine parent/child *musical* layer
      arrives** — specifically (a) harmonic segmentation that nests non-harmonic
      tones under their parent harmony (the Phase 2 deferred refinement), or (b) a
      form/section layer above progressions. At that trigger, migrate via `Dataset`
      nesting / `DatasetRecord.children` (additive), **not** a leaf-schema teardown.
- [x] **Context-sensitive naming / disambiguation:** consume the candidate
      `(root, quality)` set from `interpret_chord` and pick the contextually-correct
      reading from key, functional role, and voice-leading context — returning the
      chosen name *with ranked alternatives and the evidence for each*, not a bare
      label. (Resolves the deferred functional augmented-sixth labelling from
      Phase 1.5 at detect-and-flag level. Deterministic/rule-based here;
      corpus-statistical ranking is Phase 4.5.) **Delivered (2026-06-10), per
      the design on record below:** `analysis/naming.py` (`name_chord` +
      `name_chord_across_keys`), signal tiers (a)+(b), weight table as
      versioned prior (`data/naming_weights.json`, `naming-rules.1`),
      special-function seam (aug-6 German/French, secondary dominants,
      Neapolitan), `RecordAnalysis.naming` wired in both record builders, and
      `AnalyticalContextSnapshot` moved down to `analysis/results.py`
      (re-exported from `dataset.record`) so readings label their context
      without an upward import. Behavior pins: C6=Am7 ties honestly in
      C major until a bass note or A-minor frame decides it; dim7 stays a
      three-way diatonic tie pending tier (c). *Follow-ups:* tier (c)
      sequential/VL signals; fully-spelled It/Fr/Ger labels.

      **Sequenced after Phase 3.5** (consult, 2026-06-10): this consumes an
      `AnalyticalContext`, and Phase 3.5b is the upstream *producer* of that
      object — the seam itself is correct (analysis must not hardcode
      key-finding). Building the consumer first would mean validating only on
      hand-authored keys, and inventing an evidence vocabulary against toy
      inputs rather than real producer output. **Design requirements:**
      (a) runnable per-candidate over a *ranked set* of `AnalyticalContext`s —
      key induction returns ranked candidates with margins, and relative
      major/minor near-ties are the canonical hard input; (b) the result
      schema labels each reading as conditional on the context that produced
      it (the door to joint key/chord reasoning stays open); (c) may use
      VL-distance (Phase 3.5) as a signal.

      **Design on record (proposed by the prior session, recovered + adapted
      2026-06-10; merging the PR that adds this block = sign-off):**
      - *Entry point & placement:* new `mts/analysis/naming.py` —
        `name_chord(chord, context, *, realization=None) -> ChordNaming`.
        Pure/numeric; consumes `interpret_chord` + `contextualize_chord` +
        `theory/functions.py` (+ `pcset_math.compatibility_roots` as a scoring
        input). Result types in `results.py`; roman-numeral *string* rendering
        at the display edge (`mts/context/result_format.py`). Nests into the
        Slice 4 record: `RecordAnalysis` gains optional
        `naming: ChordNaming | None` — the "chosen reading."
      - *Signal tiers* — ship (a)+(b) now, (c) as an additive follow-up:
        (a) intrinsic: bass-is-root (when a realization is present), quality
        canonicality; (b) key-relative: root-is-diatonic, functional fit via
        `theory/functions.py` + `compatibility_roots`, all-tones-diatonic
        (unless a recognized special function); (c) sequential/voice-leading:
        resolution behavior + VL smoothness/common-tones between neighbors
        (needs progression context; VL-distance now exists for it).
      - *Result shape* (numeric facts in analysis; strings at the edge):
        `NamingEvidence {signal, weight, detail}` ·
        `RankedInterpretation {interpretation, score, rank, functional_role,
        root_degree, function_category, evidence}` ·
        `ChordNaming {chosen, alternatives, is_ambiguous, context}` — where
        `context` is the `AnalyticalContextSnapshot` the reading is
        conditional on (requirement (b)). Signal weights live in an explicit
        **versioned weight table** (the versioned-priors pattern; cite the
        version in results).
      - *No-context behavior:* graceful intrinsic-only ranking with
        `is_ambiguous` set; never fabricate a key (the don't-guess rule —
        documented as distinct from the register rule).
      - *Augmented-sixth scope:* detect-and-flag `function_category`
        (`augmented_sixth_german`, …) via a general special-function seam
        that also covers secondary dominants / Neapolitan; fully-spelled
        It/Fr/Ger labelling deferred to a follow-up.
      - *Ranked-context adaptation* (the one structural change vs. the
        original proposal, which predated key induction): keep `name_chord`
        **single-context and pure**; add a thin wrapper that maps it over
        ranked key candidates (`infer_key` output → `candidate_context`) and
        returns the per-key conditional namings plus a combined view weighted
        by key confidence. Rationale: the core scorer stays testable in
        isolation; the key-confidence marginalization is its own (versioned)
        policy that can evolve without touching the scorer; and the no-context
        path already gives the core a single-arity shape.

### Phase 3.5 — Identity-analysis primitives & key induction ✅ DONE
Inserted 2026-06-10 after an external consult, before the Phase 3 disambiguation
slice. Rationale: disambiguation consumes an `AnalyticalContext` that nothing in
the pipeline yet *produces* — without a producer, the flagship pipeline
(MIDI → enriched dataset) has a caller-shaped hole, and disambiguation could only
ever be validated on hand-authored keys. **Rejected alternative (recorded so we
don't relitigate):** build disambiguation first on its signed-off design, backfill
key induction after. Rejected because the disambiguator's evidence vocabulary
should be designed against real producer output — correlation margins, the
relative-major/minor near-ties Krumhansl-style profiles are notorious for — not
placeholder contexts. Momentum was the only argument for consumer-first.

- [x] **3.5a — set-class & spectral tables.** Normal order and prime form (Rahn),
      set-class identity (prime-form mask — same integer convention as Ian Ring's
      scale numbers, see References), Z-relation partners, and **DFT magnitudes**
      (|f₁..f₆| of the PC-set characteristic function — a transposition- and
      inversion-invariant set-class fingerprint and continuous 6-D similarity
      embedding: |f₅|≈diatonicity, |f₆|≈whole-tone-ness, |f₄|≈octatonicity,
      |f₃|≈hexatonicity). All cached tables over the 4096-mask space (the PR-#17
      pattern). Includes the transformation operators the table build needs as
      internals, exposed as public named functions at near-zero marginal cost:
      `T_n` (existing rotation), inversion `I_n`, complement, M5/M7
      multiplication. Surfaced as identity/analysis-tier fields on the typed
      results (and thence dataset records). *Note:* the DFT **magnitudes**
      deliberately conflate a set with its inversion (right for similarity);
      phases are kept available — they distinguish T_n/T_nI and feed the later
      DFT-based key-finding refinement. *Deferred:* Forte names need a vetted
      reference table (deriving ordinals algorithmically mislabels the known
      Forte/Rahn discrepancy sets); prime form is the unambiguous set-class name
      until then. **Delivered:** `core/setclass.py` + `SetClassData` on both
      analysis results; prime form = min mask over the 24 zero-rooted images
      (provably Rahn — see module docstring); verified exhaustively over the
      4096-mask space (224 set classes, 23 Z-pairs — textbook counts).
- [x] **3.5b — key induction.** `infer_key(sequence) → ranked (key, score,
      margin, evidence)`, producing `AnalyticalContext` candidates — the producer
      for the Phase 3 disambiguation seam. **v1 is global key only:**
      whole-sequence Krumhansl–Schmuckler-style profile correlation over
      duration-weighted PC content (durations already exist in the temporal
      layer), ranked candidates per Decision 7. Profiles are **versioned
      empirical priors** (pattern below). **Delivered:**
      `analysis/key_induction.py` (`infer_key` + `candidate_context` →
      `AnalyticalContext`), `Sequence.pc_weights()` (duration-weighted PC
      content; `infer_key` duck-types a `Sequence`), Krumhansl–Kessler profiles
      as the first versioned prior (`data/key_profiles.json`, `kk-1982.1`);
      every result carries all 24 candidates, the top-two margin, the input
      weights, and the profile version. Degenerate input (silence / uniform)
      errors rather than guesses. *Extension delivered (2026-06-11):*
      **local key tracking** — `temporal/key_tracking.py` `track_keys`
      (windowed `infer_key` over `Sequence.pc_weights(start, end)`, same
      versioned profiles) merges same-best-key windows into `KeyRegion`s
      with beats+seconds extents, per-region mean score/margin, and the
      per-window evidence. Full-size windows only (a truncated tail is a
      different evidence basis); uninformative windows make no claim and
      never split a region (no evidence ≠ a key change); no smoothing in
      v1 — thin-evidence blips are surfaced per Decision 7, `mean_margin`
      is the gate, and any future hysteresis ships as a versioned prior.
      Window geometry is caller-set, cited in the result. MCP: new
      `key_tracking` tool (#20, event triples) + additive `key_regions`
      field on `midi_file_analysis`. The *online* form (A4) remains gap 5.
- [x] **Voice-leading distance** (parallel track; leaf primitive with no
      dependencies). Exact minimal voice-leading distance between two identities:
      min-cost bipartite matching for equal cardinality; the unequal-cardinality
      doubling/omission policy is **named and versioned** (multiple defensible
      conventions exist — the choice is an empirical prior, not a fact).
      Analytical, not generative — it measures, it does not realize. Consumers:
      disambiguation signal (3.5→Phase 3), segmentation cost (harmonic
      segmentation), progression similarity (Phase 4.5 features), Phase 7 input.
      In datasets it lives as **Dataset-level edges** between records — the first
      relational structure in the schema; additive container-level fields, same
      SCHEMA_VERSION policy as additive leaf fields. **Delivered:**
      `analysis/voice_leading.py` — exact via the non-crossing theorem (equal
      cardinality: best of n sorted rotations; unequal: non-crossing surjections
      enumerated as circular block compositions), brute-force-verified in tests;
      policy `doubling.1`; `VoiceLeadingResult` carries the optimal mapping as
      evidence. Dataset-edge integration lands with its first consumer.

**Versioned-priors pattern (Decision 7 infrastructure):** every empirical prior
the engine bakes in — key profiles (3.5b), the disambiguation weight table
(Phase 3), VL cardinality policy (3.5), corpus statistics (Phase 4.5) — ships as
a versioned data asset with one shared mechanism; results cite the prior version
they used. Same input + same prior version → same output.

### Phase 4 — MCP endpoint
- [x] Thin adapter: one tool per analysis entry point; schemas derived from
      `results.py`; stateless by default, session-backed where multi-turn is needed.
      **Delivered (2026-06-10):** `mts/mcp/` — `tools.py` holds 17 pure,
      SDK-free adapter functions (each parses agent-friendly inputs, calls one
      engine entry point, returns its `to_dict()`; Decision 5 honored —
      nothing computed in the layer); `server.py` wires them into FastMCP
      behind a guarded import (`mcp` is an optional extra; `python -m mts.mcp`
      runs stdio). Tool set spans identity (parse / chord / scale / set-class /
      interpretations), context (in-key, naming, key induction,
      naming-across-keys, VL distance), register/generative (voicing analysis
      + suggestions), comparison/brief, catalog discovery, and the end-to-end
      `midi_file_analysis` (the A1 pipeline; local key regions added
      2026-06-11). Stateless-only;
      the session-backed variant is deferred until a multi-turn consumer
      exists.
- [x] Error/validation surface suitable for blind agent use.
      **Delivered:** every tool raises `ValueError` with actionable messages
      that point at the discovery tools (`list_scales` /
      `list_chord_qualities`); inputs accept note names or pc ints; the server
      instructions tell agents that ranked alternatives + `is_ambiguous` are
      part of the answer, not noise.
- [ ] *(parked here 2026-06-10)* **Constraint search / "inverse analysis":**
      `search_identities(constraints)` / `search_voicings(identity, constraints)`
      — exhaustive, exact queries over the 4096-identity universe and the small
      voicing spaces ("all 7-note scales containing this tetrachord with no
      consecutive semitones"; "all voicings of Cmaj9 under 19 semitones of spread
      with no m9 against the bass"). Generalizes `suggest_voicings` into a query
      layer; explicitly generative-side (cardinal rule). Parked because demand is
      MCP-shaped — it's the marquee agent-facing tool, not a library-internal
      need. The Phase 3.5a tables are its index, so parking costs nothing: the
      substrate accrues anyway. *(2026-06-11: Phase 4.6 rulesets generalize
      this — a search constraint and a checkable rule are the same predicate
      pointed in different directions; build the constraint vocabulary once,
      there.)*

### Phase 4.5 — Contextual & statistical interpretation (corpus-driven)
The intelligence payoff: move from *enumerating* interpretations to *weighing* them
with statistics learned from a corpus. Depends on the temporal layer (Phase 2) for
context, the dataset schema (Phase 3) as the unit of record, and a corpus to learn
from. Governed by Decision 7 (ranked, explicit, reproducible — never a black box).

- [ ] Score / rank competing interpretations (chord names, key & functional
      readings, segmentations) by corpus statistics — e.g. progression n-grams,
      voice-leading likelihood — surfacing conflicts with weights + evidence.
- [ ] Build / ingest a corpus and a **reproducible** statistical model (explicit,
      versioned weights; same input + corpus → same ranking).
- [ ] **North-star use case:** reveal *novel* readings of existing pieces — points
      where a statistically- or structurally-supported reinterpretation diverges
      from the conventional analysis. The engine proposes and evidences; the
      human/agent judges (semantic call stays in the caller, per Decision 7).

### Phase 4.6 — Rulesets: a constraint syntax over the analytical vocabulary
Added 2026-06-11 (Decision 8). The articulated vision: **extract, impose, and
compare compositional rulesets** as first-class artifacts. An LLM translates a
theory treatise into the DSL through MCP; the engine validates, evaluates
against material, induces candidate rulesets *from* compositions, and feeds
rulesets into generation as constraints. Lineage: species counterpoint is a
ruleset; constraint programming for music (Ebcioğlu's CHORAL, Anders'
Strasheela) built the imposition half; version-space rule induction builds the
extraction half. What's novel here is the ruleset as a serializable, versioned,
MCP-portable object flowing both directions. Intertwined with Phase 4.5 — soft
rules and corpus statistics are the same object (weighted constraints with
provenance).

- [ ] **Workstream 0 — vocabulary prerequisites** (per the Decision 8
      corollary, these are first-class engine capabilities in their own right,
      wanted independent of rulesets):
      - [x] **Voice identity** — counterpoint rules (parallel fifths, voice
            crossing) need to know *which voice moved*. **Delivered
            (2026-06-11):** `Event.voice` (optional label; `None` = unvoiced —
            the engine never invents an assignment; explicit voice-separation
            of merged material stays a later refinement) · MIDI seeds one
            voice per (track, channel) as `t{n}c{n}` via a per-track parse
            (which also fixed cross-track note_on/note_off mispairing) ·
            `Sequence.voices()` / `filter_voice()` · first consumer:
            `temporal/voice_motion.py` `voice_motion` classifies every
            voice-pair transition (parallel / similar / contrary / oblique,
            mod-12 interval classes as evidence — compound fifths count) over
            adjacent onset moments; held notes yield oblique, double-stops
            make no claim, static pairs emit nothing. The *rules* (e.g. "no
            parallel fifths") stay in the DSL — they are one-line filters
            over these transitions (demonstrated in tests). MCP:
            `voice_pair_motion` (#21).
      - [x] **Melodic atoms** — contour, step/leap classification,
            approach/departure intervals, NHT typing (shared with the parked
            harmonic-segmentation work). **Delivered (2026-06-12):**
            `temporal/melodic.py` `analyze_melody(sequence, voice=, harmony=)`
            — per-note signed approach/departure intervals with the
            species-counterpoint class vocabulary (unison 0 · step 1–2 ·
            skip 3–4 · leap ≥5; definitional, not an empirical knob),
            Parsons-code contour, ambitus. A line is one voice, monophonic —
            multi-voice without `voice=` errors, overlaps error. **NHT typing
            is harmony-relative and never guessed:** runs only when the
            caller provides `(start, end, pcs)` spans (dataset records, a
            chord track, any external analysis); chord tones are not NHTs;
            non-chord tones classify by approach/departure pattern (pedal /
            suspension / anticipation / passing / neighbor / appoggiatura /
            escape / free, documented precedence); notes outside every span
            get no claim. The sequential vocabulary gap 7 (cadences) and
            harmonic segmentation will reuse. MCP: `melodic_analysis` (#22).
      - [x] **Rhythmic atoms** — duration patterns, syncopation, metric
            placement classes. **Delivered (2026-06-12):**
            `temporal/rhythmic.py` `analyze_rhythm(sequence, voice=)` — per
            note: metric placement (downbeat / beat / offbeat / subdivision)
            against the **felt beat** derived from the signature at the
            onset (compound meters — numerator > 3, divisible by 3 — beat in
            threes: 6/8 → dotted quarter; definitional, not a knob);
            a precise syncopation predicate (an offbeat/subdivision onset
            sounding through the next beat line, or a weak-beat onset
            sounding through the next downbeat — downbeats never syncopate);
            durations + inter-onset intervals per note and as line-level
            sequences. Same line discipline as melodic atoms (one voice,
            monophonic; polyphonic rhythm is per-voice). Pattern *mining*
            (which patterns recur) is Phase 4.5/4.6 statistics, not this
            vocabulary layer. MCP: `rhythmic_analysis` (#23, constant meter
            via numerator/denominator; full meter maps via the library
            door). **Workstream 0 is complete — the DSL is unblocked.**
            *Extension — swing feel (2026-06-12, prompted by Julian's
            review):* `analyze_swing` measures where each **two-way beat
            division** places its interior onset (division fraction: 0.5
            straight, 2/3 triplet swing 2:1, 0.75 dotted shuffle 3:1,
            < 0.5 reversed) and classifies straight / swung / reversed /
            mixed under the first rhythm-side **versioned prior**
            (`data/swing_feel.json`, `swing-feel.1`: straight window,
            consistency ceiling, evidence floor — engineering defaults
            pending corpus calibration; results cite the version). Honest
            bounds: three-way divisions are not swing pairs; too few
            divisions raises (no feel from no evidence); and swing that
            lives only in performance timing (quantized-straight MIDI)
            is invisible to symbolic data by nature — documented in the
            tool. MCP: `swing_analysis` (#24). Generalizes to **groove
            templates — gap 10** (per-slot offsets + velocity, the
            Ableton Extract Groove model).
- [ ] **The DSL (v1).** Declarative, JSON-serializable, no code execution.
      Each rule: an *atom* (a path into the typed-results vocabulary), a
      *scope* (per-event / per-segment / adjacent-pair / phrase / global), a
      *predicate* (equals / in-set / threshold / forbidden-pattern), a
      *polarity* (hard, or soft with weight), and the *specification level it
      requires* (error-don't-guess). Rulesets: named, versioned, composable
      (combine / specialize / diff). Schema validation strict enough that a
      blind LLM's translation is mechanically checkable.
- [ ] **The evaluator** (analysis side; build first — deterministic, no new
      theory). `evaluate(ruleset, dataset) → ConformanceReport`: which rules
      hold, violation locations with evidence (Decision 7), per-rule
      conformance frequency. Operates on dataset records — they already carry
      every fact the atoms reference. Ruleset *comparison* falls out: shared
      rules, direct conflicts, implication checks where decidable by
      enumeration over the small spaces, empirical conformance profiles on a
      shared corpus.
- [ ] **Induction** (the rule-space). Version-space mining, not learning:
      enumerate which instantiations of the template vocabulary a corpus
      satisfies (or satisfies at frequency ≥ θ). Output is a *rule-space* —
      plural by construction — narrowed by counterexample pieces, thresholds,
      or projection onto one compositional element (filter by atom family).
      The hard part is **interestingness**: score candidates against null
      models (chance material, permuted corpora; MDL flavor — good rulesets
      *compress*), reusing Phase 4.5's statistical machinery. Honest bound:
      induction can only discover what the vocabulary expresses (Decision 8
      corollary) — interpretable by design, and the reason Workstream 0 leads.
- [ ] **Generation coupling** (lands with Phase 7): rulesets are the
      constraint/cost input to generative search — hard rules prune, soft
      rules score. This *is* Phase 7's "qualitative characteristics"
      parameterization, in principled, composable form.
- *No neural network required* — evaluation, comparison, and induction are
  exact. Learned components (novel template proposal, treatise translation)
  live in the caller per Decision 8: the LLM proposes, the engine verifies.
- *Long-range bridge (recorded 2026-06-11, from the TERRANE brief):* TERRANE's
  serialized **terrain plasticity** and our rulesets are sibling artifacts —
  both persist extracted musical habit as versioned state. When either is
  designed in detail, keep the bridge in view: a terrain state should be able
  to reference the ruleset version active when it was carved.
- *Prospective induction consumer (2026-06-11, from the Solve et Coagula
  brief):* deriving a ruleset from its deterministic event chronicles
  ("derive the idiom from the affinity matrix") and checking the
  instrument's own output against it — a first-class evaluator+induction
  use case, compatible with its core-determinism requirement by
  construction (rulesets are deterministic + versioned).

### Phase 5 — Representation / projection layer (projections as data)
A render-agnostic layer: the engine emits **typed, structured descriptions** of a
musical object in its canonical representations — and *rendering to pixels/files
is a thin edge consumer, not part of core* (same relationship MCP has to analysis).
Decision: **library-first, no in-repo GUI** (the deferred Qt GUI stays demoted).
This is the "visual analysis suite" expressed as data an agent or a renderer can
consume. *(Charter widened 2026-06-11, from "visuals as data" to "projections as
data": rendering targets include sound engines, not just screens — see the
descriptor-track item below and Decision 9.)*

- [ ] Each representation **declares the specification level it requires** and
      errors when under-specified — lattice-governed, "reduce never invent":
  - *register-less (identity key):* pitch-class **clock / bracelet diagram**,
    **interval-vector / IC spectrum**, **Tonnetz** (coordinates already exist),
    **circle of fifths** projection, set-class / normal-form views.
  - *register-required (`Realization`):* **keyboard / piano diagram** of a chosen
    voicing, fretboard.
  - *register + time (depends on Phase 2):* **piano roll**, **staff / sheet-music**
    engraving model.
- [ ] Stable output schemas (coordinates, encodings, an engraving model) with
      parity to `results.py` / the dataset record, so rendering libraries consume
      them at the edge.
- [ ] Reuse existing seeds: `TonnetzAnalysis`, interval vector, reflection
      axes / symmetry (the clock/bracelet math), and re-home `layouts/` out of the
      demoted GUI frame.
- [ ] **Descriptor tracks — control signals as data** *(added 2026-06-11; the
      audio-facing projection family, per Decision 9)*. Given a `Sequence`
      (later: a streaming session, gap 5), emit a typed, time-aligned series
      of the numeric harmonic descriptors the engine already computes — DFT
      embedding, evenness, key-margin, VL effort between adjacent segments —
      per segment or per window, at a declared rate. Entirely symbolic,
      exact, versioned-prior-compatible; the consumer maps tracks onto synth
      parameters / CC streams / lighting. *Demand evidence (ad hoc today):*
      TERRANE's margin→terrain-ruggedness and Solve et Coagula's DFT→CC
      mappings — each privately re-deriving "harmonic state as a control
      signal"; this item is their shared formalization. A DDSP/RAVE-class
      instrument *conditioned on descriptor tracks* is the sanctioned shape
      for "Tonality-aware timbre" (in consumer repos, never here).
- Canonical model for the representation set: **Ian Ring's "A Study of Scales"**
  (see References) — its per-set page enumerates the representations to mirror, and
  it keys every set by our same identity bitmask.

Open question: which rendering targets to support as *reference* edge consumers
(SVG? MusicXML? LilyPond?) — deferred; core commits only to the data layer.

*Named consumer (2026-06-11):* **A6 Audiology** — its 8×8 grid, keyboard, and
canvas piano-roll all map through one pitch axis and are ready render targets
for these descriptors; keyboard + piano-roll view types are confirmed
in-scope. Delivery for the web-visualizer class runs through **gap 9** (the
HTTP door).

### Phase 6 (future) — Beyond 12-TET: generalized identity
- The current substrate is **hard 12-TET** (12-bit bitmask, mod-12 everywhere).
  Other tonal systems — n-TET, just intonation, microtonal, non-octave-repeating —
  will require a more expansive identity system, and "the mask is the key" (Decision
  6, Phase 1) will have to be revisited. This is explicitly **out of scope** until
  the 12-TET foundation, temporal layer, and MCP endpoint are solid.
- Forward-compat contract for earlier phases: don't make choices that would have to
  be *completely* unmade. The lattice and `Realization` stay tuning-agnostic; the
  12-TET assumption stays behind the reduction boundary (Decision 6). When this
  phase lands, generalizing means replacing the reduction + substrate, not the
  identity model layered on top.
- **Known 12-TET footprint collisions (accepted limitations, not bugs).** 12-TET
  cannot faithfully hold every named scale, so distinct cultural/tuning scales can
  share a 12-TET footprint. These are *documented equivalences*, allowlisted so the
  audit doesn't flag them (see `audit/AUDIT.md` §7). Current list:
  - `Pelog Selisir` ≡ `Major Pentatonic` `[0,2,4,7,9]` — pelog is non-12-TET; this
    approximation collapses onto the major pentatonic. Faithful representation
    awaits this phase.
  - The long-term goal of cataloguing *all* named scales will surface many more of
    these; each gets recorded here + in the audit allowlist rather than "fixed."

### Phase 7 (future) — Generative: voice leading & progression realization
*Ordering note: the number groups this with the later work, but it depends only on
shipped layers (voicings, `Realization`, temporal/segmentation) plus optionally
Phase 4.5 corpus statistics — so it can land before the Phase 6 tuning work.*

- **Generative, not analysis** (the cardinal rule): given a chord *progression* — a
  sequence of identities, from segmentation / `interpret_chord` / user input —
  produce **voice-leading realizations**: concrete `Realization`s per chord,
  connected with controlled motion. This *invents* register/voicing, so it lives on
  the generative side (alongside `suggest_voicings`), never in the analysis path.
- **Parameterized depth & variation:** controls for how elaborate the generation is
  (voice count, register range, how many variant realizations to return) and the
  **qualitative characteristics** that shape the search — smoothness / parsimony
  (total semitone motion), common-tone retention, contrary motion, voice
  independence, openness, tessitura, dissonance treatment. Different settings →
  different stylistic outputs at different depths. *(2026-06-11: the principled
  form of these controls is a Phase 4.6 **ruleset** — hard rules prune the
  search, soft rules score it; "a style" is a ruleset handed to the generator.)*
- Builds on the named-voicing vocabulary + `Realization` + the temporal layer;
  qualitative scoring can draw on Phase 4.5 corpus statistics for "what's idiomatic."
- Output is ranked generative *suggestion data* (each variant tagged with its
  qualitative profile), kept out of analysis; spelling/rendering at the edge.

**Extensions (2026-06-10, from the Target-applications list — same generative
frame, recorded here so A2/A3 decompose onto named work):**
- **Scale re-mapping** — transform material from one scale to another preserving
  contour and degree-function rather than literal pitches (degree-correspondence
  mapping; NHTs re-mapped relative to their resolution targets). Analysis names
  the degrees; the re-mapping *invents* pitches → generative.
- **Meter re-mapping** — re-cast a `Sequence` under a new `TimeSignature`
  (re-group beats, preserve or intelligently re-place metric accents). Lives on
  the temporal types; generative because accent placement is a choice.
- **Modulation path planning** — given source and target keys, plan a key-change
  route with a stated bias (shortest circle-of-fifths walk, chromatic-mediant
  color, pivot-chord availability) and realize the connecting material via the
  voice-leading machinery above. Key-distance metrics come cheap from Phase 3.5a
  (|f₅| phase distance ≈ circle-of-fifths position) and Phase 3.5b key profiles.
- **Instrument-class profiles** — the constraint vocabulary A3 needs (register
  range, polyphony, idiomatic spacing per class: bass/pad/lead/counter-melody),
  shipped as versioned priors (Phase 3.5 pattern) so generation under a profile
  stays reproducible.

## Standing review — theory grounding (scheduled 2026-06-12)

A recurring capability review against the **broader principles of music
theory and real-world musical practice**, to surface embedded assumptions
before they undercut the engine's utility outside the cases we built
against. The swing gap is the type specimen: the rhythmic atoms shipped
straight-grid-first, and only a direct question exposed that swung material
read as `subdivision` noise. Each review walks the shipped capability
surface (INTEGRATION.md's table is the checklist) and asks, per capability:

- What idiom/notation/practice does this silently assume (classical/notated,
  straight-grid, quantized, equal-tempered, Western-functional)?
- What common real-world material would it misread rather than refuse?
  (Misreading is worse than erroring — the contracts promise
  error-don't-guess.)
- Is the assumption *documented as definitional*, *priced as a versioned
  prior*, or *invisible* — only the last is a finding.

Findings become recorded gaps or accepted-limitation entries (the Phase 6
12-TET-collision pattern), never silent. **Cadence:** once before the Phase
4.6 DSL v1 ships (the DSL freezes atom semantics — assumptions baked into
the vocabulary get expensive after that), then at each phase boundary.
Candidate first-pass agenda, from known territory: performance timing vs
symbolic data (swing was one case; rubato, humanization, groove templates
are siblings) · literal vs harmonic segmentation (NHT-blind) · key induction
profile bias (KK profiles are classical-corpus priors; jazz/modal/folk
material may rank oddly — Temperley/Aarden variants already invited by A5) ·
modal vs functional harmony assumptions in `theory/functions.py` · the
melodic step/skip/leap mapping's fit for non-Western melody · meter
inference absent (we trust the file's time signature) — *promoted to
gap 11 (2026-06-12), the review's first graduate; groove extract/apply
(gap 10) was recorded the same day from the same conversation.*

**Pass #1 — run 2026-06-12 (before the 4.6 DSL, as scheduled).** Walked
the INTEGRATION.md capability table against the three questions. Findings
and disposals:

1. **Grid-exactness assumption on performed input** — *invisible →
   misreads; the headline.* Segmentation, rhythmic placement, and voice
   motion all treat onsets as exact: verified that ~5 ms humanization
   turns two chords into ten micro-segments (with garbage transitional
   sets the A1 pipeline would name) and an on-the-beat melody into
   all-`subdivision`. → **gap 12** (tolerance layer); interim consumer
   guidance added to INTEGRATION.md contracts.
2. **Global-key naming in a modulating file** — *invisible → misread.*
   `midi_file_analysis` computes key regions yet names every segment
   under the one global key. → **gap 13** (per-region context).
3. **Key-induction candidate space is the profile modes — today
   major/minor only.** Modal centers (a dorian vamp) rank as relative
   major/minor — a misattribution, not an error. Extension is nearly
   data-only: add modal rows to `key_profiles.json` and entries to
   `candidate_context`'s mode→scale map. → *accepted limitation,
   documented in `key_induction.py` + INTEGRATION.md; modal profiles
   join the standing Temperley/Aarden invitation.*
4. **Functional vocabulary exists only for major/minor keys**
   (`TEMPLATES_MAJOR/MINOR`; `load_function_mappings` errors on other
   modes; naming's `functional_fit` silently doesn't fire for modal
   keys). Honest *absence*, not a misread — the engine doesn't claim
   T/PD/D roles it can't ground. → *accepted limitation; modal function
   templates are future vocabulary (the `TAG_MODAL` seeds in
   `theory/functions.py` are the start), demand-driven.*
5. **NHT typing is onset-based** — a held note is judged in the span
   containing its onset only, so the *tied suspension* (the most common
   suspension!) is invisible: the sustained portion reads chord-tone
   even where the harmony has moved under it. → *consequence documented
   in `melodic.py`; tie-aware typing recorded there as the refinement.*
6. Confirmed already-priced: swing/groove (gaps 10/11), KK profile bias
   (versioned + variants invited), step/skip/leap and felt-beat mappings
   (definitional, documented), literal segmentation (documented
   baseline), 12-TET footprint (Phase 6). One verified non-finding:
   uniform articulation cannot bias key induction — Pearson correlation
   is scale-invariant, so staccato vs legato encoding washes out.

Next pass: at the next phase boundary (post-DSL v1).

## Demoted / deferred (built for the old "app" frame)

- `gui/` (Qt) and the audio backend — not on the library/MCP path. Don't delete;
  don't let them shape core architecture.
- `cli/push.py` — keep as an **example consumer**, not a foundation component.

## Parked work (branches)

- ~~**`wip-context-cli-rewiring`**~~ — **RETIRED (Phase 3 Slice 3).** Its intent (the
  four CLI scripts on `DisplayContext`) was **re-done on current `main`** rather
  than merged — the branch was ~30 commits behind, collided with the typed-results
  rewrite, and crashed in `run_specific` (the `context` shadowing bug, now fixed by
  the `session_context` rename). Branch deleted; recoverable from commit `c06270a`
  if ever needed.

## Open questions

- MIDI ingestion dependency: Mido vs. in-house SMF parser?
- ~~Dataset record granularity: per-event, per-segment, or per-progression?~~
  **Resolved (Phase 3 Slice 4):** flat leaf record per object/event/segment, grouped
  by a `Dataset` container; recursion deferred to a future parent/child musical layer
  (see Slice 4 "reflection point").
- Does the temporal layer need tempo/meter awareness in Phase 2, or defer to 2.5?

## References & prior art

- **Ian Ring, "A Study of Scales"** — <https://ianring.com/musictheory/scales/>
  (example entry: <https://ianring.com/musictheory/scales/3055>). An encyclopedic
  catalog of all 4096 twelve-tone pitch-class sets, **each keyed by a number that
  is exactly the 12-bit identity bitmask Tonality uses** (a PC set ↔ an integer
  0–4095). This is the canonical model for two of our workstreams:
  - **Representation suite (Phase 5):** mirror its representations — bracelet /
    necklace diagram (with symmetry axes), Tonnetz, interval vector, prime &
    normal form, Forte class, modes, complement / inverse, rotational & reflective
    symmetry, ridge tones, maximal evenness, Rothenberg propriety, Myhill's
    property, Lewin–Quinn DFT (FC) components, brightness / center of gravity,
    coherence, and the per-set "nearby scales" relational map.
  - **Naming & equivalence (Phase 1.5):** a cross-reference for alternate naming
    traditions (Zeitler, Messiaen modes of limited transposition, dozenal, etc.)
    and for prime-form / inverse equivalence.
  - **Scope caveat:** Ring catalogs *scales / PC-sets* (and the triads embedded in
    each), not chord *voicings* or *realizations* — Tonality's register/voicing
    layer is complementary, not duplicative.
  - **Possible interop:** expose a cross-reference between our `mask` and a Ring
    scale number (mind the bit-order convention) so entries can be linked directly.
