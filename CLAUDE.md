# Tonality — Agent & Contributor Guide

> Read this first. It is the handoff contract between humans and agents across
> devices. For the strategic plan and build sequence, see **[ROADMAP.md](ROADMAP.md)**.

## What this is (and what it is becoming)

Tonality is a **local-first music-theory engine** for 12-TET pitch material.
Today it recognizes and contextualizes scales, chords, and pitch-class sets.

**The destination is a foundation library with an MCP endpoint** so AI agents can
analyze music and turn varied notations into enriched, contextualized datasets.
It is *not* an end-user app. When a decision trades off "cleaner library API" vs.
"nicer GUI," favor the library. The Qt GUI and audio layers are **deferred**, not
active (see ROADMAP "Demoted").

The engine's reason to exist: it does the exact pitch-class arithmetic that LLMs
are bad at (interval vectors, exhaustive subset search, symmetry). Keep that
division of labor — precise combinatorics live here; fuzzy/semantic reasoning
lives in the caller.

## The core data model (read before touching `core/` or `analysis/`)

Two structures, not a hierarchy of importance:

- **Identity key** — a pitch-class set as a 12-bit bitmask. Always present.
  Cheap, hashable. This is what you **match, name, and catalog** on.
- **Realization** — an ordered list of actual pitches (octave, doublings,
  spacing, bass). **Optional.** This is what **voicing, voice-leading,
  inversion, and perceptual** analysis read.

A *timeless identity* is a key with no realization. A *MIDI chord* is a key with
a realization. Time-based events carry a realization that **reduces to** a key:
`event → realization → identity key`.

Two **independent** reductions define a lattice of identity types (do not collapse
them into one linear "scope"):

- **Transpositional** — fixed root, or transposition-invariant *shape*?
- **Registral** — fixed octaves/spacing, or octave-invariant?

The four corners: registered+rooted (a real voicing) · PC-set+root (a named
chord) · PC-set rootless (an interval shape) · **registered+rootless (a voicing
template** — currently underexpressed; first-class target for generative work).

**The cardinal rule:** you can always *reduce* (realization → key); you can never
*invent* register (key → realization) without choosing a voicing — and choosing a
voicing is a **generative** act, not an analytical one. Analysis functions must
declare the specification level they require and **error, not guess**, when handed
a register-less identity for register-dependent analysis.

## Architecture layers (bottom → top)

```
core/        Identity layer: bitmask, pitch, scale, chord, quality, enharmonics, symmetry
  ↓
analysis/    Enrichment engine: specs (parser), *_analysis, comparisons, summaries, results
  ↓
temporal/    Time layer (Phase 2): Event/Sequence + tempo/meter; window → realization → key.
             Segmentation + harmonic rhythm PLANNED. (analysis/timeline.py is a DEPRECATED stub.)
  ↓
[mcp]         PLANNED: thin adapter — one tool per analysis function, schemas from results.py
[representation] PLANNED: render-agnostic representation DATA (clock/Tonnetz/piano-roll/staff/
              circle-of-fifths). Library emits descriptions; pixel/file rendering is an edge
              consumer, NOT core (no in-repo GUI). Each view declares its required spec level.
```

`io/` loads catalogs from `data/*.json`. `theory/functions.py` generates functional
harmony. `workspace.py` is a stateful session facade (one `SessionCatalog` each —
keep it lean; it is *a* entry point, not *the* API).

## Conventions

- **Immutability:** core objects are `@dataclass(frozen=True)`. Keep them hashable.
- **Typed results:** analysis returns dataclasses from `analysis/results.py`, never
  `dict[str, object]`. Each top-level result has `to_dict()` for JSON/MCP output.
- **Sessions are isolated:** never reintroduce module-level mutable registries.
  User-defined scales/chords live in a `SessionCatalog` instance.
- **Mod-12 everywhere** in the identity layer. Register lives only in realizations.
- Prefer pure functions in `analysis/`; side effects and state stay in `workspace`/sessions.
- **Plans live in [ROADMAP.md](ROADMAP.md) — the single source of truth for
  direction.** Don't write forward-looking roadmaps, "next steps", or TODO
  sections in the README, per-layer CLAUDE.md files, or module docstrings; link
  the ROADMAP phase instead. When you make (or reject) a planning decision in
  conversation or a PR, fold it into ROADMAP.md in the same PR — an unrecorded
  decision isn't decided. This keeps every agent and device aligned on one plan.

## Running things (IMPORTANT — environment quirks)

There is **no bare `python`** on this machine. Use the project venv explicitly:

```bash
# Tests (config lives in pyproject.toml)
/Users/machinepriest/Documents/Tonality/.venv/bin/pytest tests/ -v

# Run a script / one-off
/Users/machinepriest/Documents/Tonality/.venv/bin/python3.13 scripts/analyze_chord.py C maj7 --json
```

The venv is at the **main repo root** (`/Users/machinepriest/Documents/Tonality/.venv`),
not inside the worktree. There are **109 tests**; keep them green on every commit.

## Gotchas

- **Ignore `build/`** — it is a stale generated copy of `mts/` (now gitignored).
  Never edit it; never trust search hits inside it.
- `.tonality_session.json` is user session state, not source. Gitignored.
- `analysis/timeline.py` is a DEPRECATED stub (superseded by `mts/temporal/`).
  `io/midi.py` parses Standard MIDI Files via **mido** (a runtime dependency);
  only `events_from_live_midi` is still `NotImplementedError` (streaming is out of
  scope). `mido` is required — `pip install` it into the venv.

## Parallel audit thread

A separate **audit loop** periodically checks capabilities and surfaces bugs. Its
contract is **[audit/AUDIT.md](audit/AUDIT.md)** — read it if you touch audit
scaffolding. Key fences for the dev loop: the audit runs in its **own git
worktree** (not this checkout), files findings as **GitHub issues**, and keeps its
checks in **`audit/checks/`** — which is *excluded* from the dev suite via
`testpaths = ["tests"]`, so `pytest tests/` (the Stop hook) never runs them. **Do
not put audit checks in `tests/`**; promote a proven invariant into `tests/` only
via a reviewed PR.

## Git workflow

- Work on a branch; `main` has branch protection (push succeeds via bypass, but
  prefer PRs for substantive work).
- End commit messages with the co-author trailer for the model that wrote them.
- SSH auth is configured (`~/.ssh/id_ed25519_github`).
