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
  harmonic refinement parked) · global key induction → **Phase 3.5b** ·
  **key-change splitting = local key tracking** — currently a parked 3.5b
  extension; A1 is its concrete demand driver (still sequenced after the global
  v1) · per-section enrichment ✅ (Phase 3 dataset records).
- **A2 — Smart MIDI transformer.** Apply musically-aware transformations to an
  existing MIDI file: re-voice chord progressions; add or alter voices; change
  scale intelligently (preserve contour and degree-function, not literal
  pitches); change the time signature; insert key changes with coherent
  movement (circle-of-fifths paths, or some other stated musical bias).
  *Capabilities:* analysis side ✅/planned as above · re-voicing + added voices →
  **Phase 7** (voice-leading realization) · scale re-mapping, meter re-mapping,
  modulation path planning → **Phase 7 extensions** (recorded there) · writing
  the result → **MIDI export, a gap** (recorded as Phase 2 addendum).
- **A3 — Complementary part generator.** Given a MIDI file, generate companion
  MIDI for different instrument classes (bass line, pad, lead, counter-melody)
  that is harmonically and rhythmically coherent with the source.
  *Capabilities:* full analysis pipeline (A1) · Phase 7 generation constrained
  by **instrument-class profiles** (register range, polyphony, idiom) — a new
  data vocabulary; ships as versioned priors (Phase 3.5 pattern) · MIDI export.

**Gaps this list surfaces (recorded, not yet scheduled):**
1. **MIDI export** — `io/midi.py` is read-only; every transformation app needs
   `Sequence → SMF`. Small and well-bounded (mido already a dependency); Phase 2
   addendum.
2. **Generative transformations** (scale re-mapping, meter re-mapping,
   modulation path planning) — Phase 7 extensions; all generative-side per the
   cardinal rule.
3. **Instrument-class profiles** — versioned data vocabulary for A3.
Local key tracking was already parked (Phase 3.5b extension); A1 names its
customer.

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
- [ ] **Addendum (2026-06-10, application-driven): MIDI export** — the write-side
      mirror of ingestion: `Sequence` (+ `TempoMap`/`MeterMap`) → Standard MIDI
      File via the same thin mido adapter. Surfaced by the Target-applications
      list (every A2/A3 transformation must close the loop back to a file).
      Small and well-bounded; no new dependency. Round-trip
      (`read → write → read`) is the natural invariant to test.

### Phase 3 — Contextualization & dataset schema
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
- [ ] **Context-sensitive naming / disambiguation:** consume the candidate
      `(root, quality)` set from `interpret_chord` and pick the contextually-correct
      reading from key, functional role, and voice-leading context — returning the
      chosen name *with ranked alternatives and the evidence for each*, not a bare
      label. (Resolves the deferred functional augmented-sixth labelling from
      Phase 1.5. Deterministic/rule-based here; corpus-statistical ranking is
      Phase 4.5.)

      **Sequenced after Phase 3.5** (consult, 2026-06-10): this consumes an
      `AnalyticalContext`, and Phase 3.5b is the upstream *producer* of that
      object — the seam itself is correct (analysis must not hardcode
      key-finding). Building the consumer first would mean validating only on
      hand-authored keys, and inventing an evidence vocabulary against toy
      inputs rather than real producer output. **Design requirements
      (preserved from the prior design discussion — re-derive the rest when
      this slice starts):** (a) runnable per-candidate over a *ranked set* of
      `AnalyticalContext`s — key induction returns ranked candidates with
      margins, and relative-major/minor near-ties are the canonical hard
      input; (b) the result schema labels each reading as conditional on the
      context that produced it (the door to joint key/chord reasoning stays
      open); (c) may use VL-distance (Phase 3.5) as a signal.

### Phase 3.5 — Identity-analysis primitives & key induction
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
      errors rather than guesses. *Parked extension (not this phase):*
      windowed/local key tracking and modulation detection.
- [ ] **Voice-leading distance** (parallel track; leaf primitive with no
      dependencies). Exact minimal voice-leading distance between two identities:
      min-cost bipartite matching for equal cardinality; the unequal-cardinality
      doubling/omission policy is **named and versioned** (multiple defensible
      conventions exist — the choice is an empirical prior, not a fact).
      Analytical, not generative — it measures, it does not realize. Consumers:
      disambiguation signal (3.5→Phase 3), segmentation cost (harmonic
      segmentation), progression similarity (Phase 4.5 features), Phase 7 input.
      In datasets it lives as **Dataset-level edges** between records — the first
      relational structure in the schema; additive container-level fields, same
      SCHEMA_VERSION policy as additive leaf fields.

**Versioned-priors pattern (Decision 7 infrastructure):** every empirical prior
the engine bakes in — key profiles (3.5b), the disambiguation weight table
(Phase 3), VL cardinality policy (3.5), corpus statistics (Phase 4.5) — ships as
a versioned data asset with one shared mechanism; results cite the prior version
they used. Same input + same prior version → same output.

### Phase 4 — MCP endpoint
- [ ] Thin adapter: one tool per analysis entry point; schemas derived from
      `results.py`; stateless by default, session-backed where multi-turn is needed.
- [ ] Error/validation surface suitable for blind agent use.
- [ ] *(parked here 2026-06-10)* **Constraint search / "inverse analysis":**
      `search_identities(constraints)` / `search_voicings(identity, constraints)`
      — exhaustive, exact queries over the 4096-identity universe and the small
      voicing spaces ("all 7-note scales containing this tetrachord with no
      consecutive semitones"; "all voicings of Cmaj9 under 19 semitones of spread
      with no m9 against the bass"). Generalizes `suggest_voicings` into a query
      layer; explicitly generative-side (cardinal rule). Parked because demand is
      MCP-shaped — it's the marquee agent-facing tool, not a library-internal
      need. The Phase 3.5a tables are its index, so parking costs nothing: the
      substrate accrues anyway.

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

### Phase 5 — Representation / projection layer (visuals as data)
A render-agnostic layer: the engine emits **typed, structured descriptions** of a
musical object in its canonical representations — and *rendering to pixels/files
is a thin edge consumer, not part of core* (same relationship MCP has to analysis).
Decision: **library-first, no in-repo GUI** (the deferred Qt GUI stays demoted).
This is the "visual analysis suite" expressed as data an agent or a renderer can
consume.

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
- Canonical model for the representation set: **Ian Ring's "A Study of Scales"**
  (see References) — its per-set page enumerates the representations to mirror, and
  it keys every set by our same identity bitmask.

Open question: which rendering targets to support as *reference* edge consumers
(SVG? MusicXML? LilyPond?) — deferred; core commits only to the data layer.

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
  different stylistic outputs at different depths.
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
