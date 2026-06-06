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
   eventual multi-system generalization (see Phase 5) from being a teardown, the
   **lattice** (transpositional × registral) and the **Realization** API are
   deliberately tuning-agnostic — rooted-ness and register-ness are not 12-TET
   concepts. Only `reduce_to_key()` and `core/bitmask.py` know the substrate is 12.
   New code routes through the reduction rather than open-coding `mask` arithmetic,
   so swapping the substrate later is a localized change, not a rewrite.

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

### Phase 2 — Temporal layer
- [ ] Replace the `timeline.py` stub with real `Event` / `Sequence` types
      (onset, duration, realization reference, simultaneity/overlap).
- [ ] Implement `io/midi.py` ingestion (MIDI file → events). Mido or in-house.
- [ ] Segmentation + harmonic rhythm: derive chord/identity stream from events.

### Phase 3 — Contextualization & dataset schema
- [ ] Resolve the **two "context" concepts**: promote *analytical* context
      (scope, functional role, compatibility) into the core; push *display*
      context (spelling prefs, layout) to the edge/out of core.
      **Finish & integrate the `wip-context-cli-rewiring` branch here** (see
      Parked work below) — wire all CLI scripts onto `DisplayContext` on top of
      the typed-results base, as one coherent, tested unit.
- [ ] Define the **dataset record schema** — the enriched unit emitted per musical
      object/event. Reproducible (capture spelling/context choices explicitly).

### Phase 4 — MCP endpoint
- [ ] Thin adapter: one tool per analysis entry point; schemas derived from
      `results.py`; stateless by default, session-backed where multi-turn is needed.
- [ ] Error/validation surface suitable for blind agent use.

### Phase 5 (future) — Beyond 12-TET: generalized identity
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
