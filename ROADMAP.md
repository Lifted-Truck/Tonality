# Tonality — Roadmap & Architecture Decision Record

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

### Phase 2 — Temporal layer
- [x] Replace the `timeline.py` stub with real `Event` / `Sequence` types — the new
      `mts/temporal/` package: `Event` (onset/duration in quarter-note beats +
      `Pitch`), `Sequence` with `sounding_at` / `realization_at` (a window's
      pitches → a rootless `Realization` → identity key), plus **full tempo + meter**
      (`TempoMap` beats↔seconds, `MeterMap`/`TimeSignature` → bars/beats/downbeats).
      `analysis/timeline.py` is now a deprecated shim; migrating `workspace`/`io`
      off it is a tracked follow-up.
- [ ] Implement `io/midi.py` ingestion (MIDI file → events). Mido or in-house —
      **parser decision deferred to this slice (Slice 3).**
- [ ] Segmentation + harmonic rhythm: derive chord/identity stream from events
      (Slice 2 — each segment's `Realization` feeds `interpret_chord`).

### Phase 3 — Contextualization & dataset schema
- [ ] Resolve the **two "context" concepts**: promote *analytical* context
      (scope, functional role, compatibility) into the core; push *display*
      context (spelling prefs, layout) to the edge/out of core.
      **Finish & integrate the `wip-context-cli-rewiring` branch here** (see
      Parked work below) — wire all CLI scripts onto `DisplayContext` on top of
      the typed-results base, as one coherent, tested unit.
- [ ] Define the **dataset record schema** — the enriched unit emitted per musical
      object/event. Reproducible (capture spelling/context choices explicitly).
- [ ] **Context-sensitive naming / disambiguation:** consume the candidate
      `(root, quality)` set from `interpret_chord` and pick the contextually-correct
      reading from key, functional role, and voice-leading context — returning the
      chosen name *with ranked alternatives and the evidence for each*, not a bare
      label. (Resolves the deferred functional augmented-sixth labelling from
      Phase 1.5. Deterministic/rule-based here; corpus-statistical ranking is
      Phase 4.5.)

### Phase 4 — MCP endpoint
- [ ] Thin adapter: one tool per analysis entry point; schemas derived from
      `results.py`; stateless by default, session-backed where multi-turn is needed.
- [ ] Error/validation surface suitable for blind agent use.

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

## Demoted / deferred (built for the old "app" frame)

- `gui/` (Qt) and the audio backend — not on the library/MCP path. Don't delete;
  don't let them shape core architecture.
- `cli/push.py` — keep as an **example consumer**, not a foundation component.

## Parked work (branches)

- **`wip-context-cli-rewiring`** (`c06270a`, on `origin`) — an *unfinished* migration
  of the four analysis CLI scripts (`analyze_chord`, `analyze_scale`,
  `check_chord_scale_compat`, `compare_chords`) from `spelling`/`key_signature`
  args to `DisplayContext`. **Do not merge as-is:** `check_chord_scale_compat.py`
  crashes (`context` not threaded through `run_specific`), and two files collide
  with the Phase 0 typed-results rewrite. Integrate during **Phase 3** as one
  finished, tested unit. Nothing here is on `main`.

## Open questions

- MIDI ingestion dependency: Mido vs. in-house SMF parser?
- Dataset record granularity: per-event, per-segment, or per-progression?
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
