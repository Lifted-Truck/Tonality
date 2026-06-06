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

## Build sequence

### Phase 0 — Foundation hardening ✅ DONE
- [x] Encapsulate session state in `SessionCatalog`; kill module-level globals.
- [x] Replace `dict[str, object]` analysis returns with typed result dataclasses.
- [x] Project scaffolding: CLAUDE.md, ROADMAP.md, git hygiene, harness.

### Phase 1 — Formalize the identity model
- [ ] Promote the parser's `scope` (abstract/note/absolute) into a first-class
      identity concept: an explicit lattice cell (transpositional × registral).
- [ ] Introduce the **Realization** type (ordered pitches, doublings, bass) as a
      sibling to the identity key; define `realization → key` reduction.
- [ ] Make the **voicing template** (registered + rootless) expressible.
- [ ] Audit analysis functions: tag each with the specification level it requires;
      add the "error, don't guess" guard for register-dependent analysis.

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
