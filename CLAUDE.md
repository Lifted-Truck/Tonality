# Tonality — Agent & Contributor Guide

> Read this first. It is the handoff contract between humans and agents across
> devices. For the strategic plan and build sequence, see **[ROADMAP.md](ROADMAP.md)**.

## What this is (and what it is becoming)

Tonality is a **local-first music-theory engine** for 12-TET pitch material.
Today it recognizes and contextualizes scales, chords, and pitch-class sets.

**The destination is a foundation library with an MCP endpoint** so AI agents can
analyze music and turn varied notations into enriched, contextualized datasets.
It is *not* an end-user app. When a decision trades off "cleaner library API" vs.
"nicer GUI," favor the library. The GUI and audio layers are **out of scope** (the
prototype Qt GUI was removed 2026-06-29 — recoverable from git history; see ROADMAP
"Demoted"). Rendering belongs to consumer projects, not this repo.

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
notation.py  Multi-notation parser (RE-6b; was analysis/specs.py). Below io/ so
             loaders can consume it without a cycle. Re-exported from mts.analysis.
  ↓
session.py   SessionCatalog + manual registration (RE-6b; was analysis/builders.py).
             Sessions are instances; no module-level default. Below io/.
  ↓
io/          Loads catalogs from mts/data/*.json; merges a session's catalogs on request.
  ↓
analysis/    Enrichment engine: *_analysis, comparisons, summaries, results
  ↓
temporal/    Time layer (Phase 2): Event/Sequence + tempo/meter; window → realization → key.
             Segmentation, harmonic rhythm, local key tracking, voice identity/motion,
             melodic + rhythmic atoms.
  ↓
patterns/    Pattern layer (Phase 4.6, gap C): sequential templates as first-class
             objects — a Pattern declares its abstraction (pitch exact/degree/contour
             × time exact/free; the identity lattice at pattern grain) and
             find_pattern matches exactly under that declaration. Patterns say what
             is CHARACTERISTIC; rules say what is forbidden/required. Named library
             in mts/data/patterns/. Slice 1 = melody domain; harmonic schemas,
             rule-projection, and PrefixSpan induction are recorded follow-ons.
  ↓
rules/       Rulesets (Phase 4.6): declarative JSON rules over the atom vocabulary;
             strict total validation + deterministic conformance evaluator +
             composition/comparison (combine/specialize/diff). No code execution;
             rules are data (and round-trip via ruleset_to_payload).
  ↓
search/      Constraint search / inverse analysis (Phase 4): exact, exhaustive
             queries over the 4096-identity universe and bounded register spaces.
             GENERATIVE-side (cardinal rule). Reuses the rules `Condition`
             predicate over identity/voicing field vocabularies — same predicate,
             pointed the other way. search_identities + search_voicings shipped
             (register window required — never defaulted; templates via root=None).
  ↓
representation/ Projections as data (Phase 5): render-agnostic descriptors
             (keyboard, piano-roll, bracelet, Tonnetz). Library emits descriptions;
             pixel/file rendering is an edge consumer, NOT core (no in-repo GUI).
             Each view declares its required spec level; numeric only.
  ↓
mcp/         Thin adapter (Phase 4): one tool per analysis entry point. tools.py is
             pure + SDK-free (fully testable); server.py needs the optional `mcp`
             extra (`python -m mts.mcp`). Intelligence stays below this line.
```

`io/` loads catalogs from `mts/data/*.json` (inside the package, so installed
copies work) and sits **above** `notation.py`/`session.py` so it can consume both
without an import cycle (RE-6b untangled the old `io ↔ analysis` cycle by moving
those two modules below it). `theory/functions.py` generates functional harmony.
`workspace.py` is a stateful session facade (one `SessionCatalog` each — keep it
lean; it is *a* entry point, not *the* API).

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
not inside the worktree. Keep the full `tests/` suite green on every commit
(one test needs the optional `mcp` extra and skips without it).

## Gotchas

- **Ignore `build/`** — it is a stale generated copy of `mts/` (now gitignored).
  Never edit it; never trust search hits inside it.
- `.tonality_session.json` is user session state, not source. Gitignored.
- `io/midi.py` parses Standard MIDI Files via **mido** (a runtime dependency);
  only `events_from_live_midi` is still `NotImplementedError` (streaming is out of
  scope). `mido` is required — `pip install` it into the venv.

## Cross-project integration channel

External consumer projects (Julian's synths/generators/visualizers) exchange
briefs and responses with this repo through **`integrations/`** — see
[integrations/README.md](integrations/README.md) for the protocol. If you find
an un-triaged `brief.md` there (or one arrives by relay), triage it: verify
"already shipped" claims in code, write the per-request `response.md`, and
fold durable outcomes into ROADMAP.md (target application + gaps) in the same
PR. Decisions never live in `integrations/` — it records exchanges; ROADMAP.md
records what was decided.

## Parallel audit thread

A separate **audit loop** periodically checks capabilities and surfaces bugs. Its
contract is **[audit/AUDIT.md](audit/AUDIT.md)** — read it if you touch audit
scaffolding. Key fences for the dev loop: the audit runs in its **own git
worktree** (not this checkout), files findings as **GitHub issues**, and keeps its
checks in **`audit/checks/`** — which is *excluded* from the dev suite via
`testpaths = ["tests"]`, so `pytest tests/` (the Stop hook) never runs them. **Do
not put audit checks in `tests/`**; promote a proven invariant into `tests/` only
via a reviewed PR.

## Parallel port thread (C++)

A separate **port thread** builds the C++ core (Decision 10: dual implementation)
in a sibling repo, `tonality-core`. Its contract is **[port/PORT.md](port/PORT.md)**.
What the dev loop must know: **`port/pin.json`** fingerprints the ported surface
(the set-class export table + the ported conformance cases), and
`tests/test_port_pin.py` fails whenever the engine drifts from it. If your change
trips that test intentionally, rerun `scripts/update_port_pin.py`, commit the new
pin in the same PR, and file a notice in `integrations/tonality-core/` so the port
refreshes its vendored fixtures. The port agent never edits `mts/`; its engine
asks arrive as briefs on the integrations channel.

## Git workflow

- Work on a branch; `main` has branch protection (push succeeds via bypass, but
  prefer PRs for substantive work).
- End commit messages with the co-author trailer for the model that wrote them.
- SSH auth is configured (`~/.ssh/id_ed25519_github`).
- **Acceptance block on substantive PRs** (the build-then-review contract): every
  PR that adds or changes a capability states, near the top, *what it should do*
  and *the exact cases/fixtures that prove it* — so review is coherent against
  intent, not just a diff. For port slices, the acceptance block is literally
  "reproduces these conformance cases / fixture rows." Trivial fixes are exempt.

<!-- KNOWLEDGE-LOOP:START -->
## Self-Improving Knowledge Loop

Each session: read accumulated knowledge before acting, write distilled knowledge
after. This meta-layer sits on top of my primary role and never overrides it.

### Every session
1. **ORIENT** — Read INDEX.md in full (kept small on purpose). Pull ONLY the matching
   entries from LIBRARY.md into context. Never load all of LIBRARY by default.
2. **ACT** — Do the work, applying retrieved lessons. If a lesson proves wrong,
   correcting it outranks adding a new one.
3. **REFLECT** — Ask: "What did I learn that a future session needs and could not
   cheaply re-derive?" A lesson qualifies only if durable, evidenced (tied to a
   concrete trigger), and non-obvious. If nothing qualifies, write nothing.
4. **WRITE (atomic)** — Append the lesson to LIBRARY.md and a one-line pointer to
   INDEX.md in the same change. New lessons enter as `tier: candidate`; promote to
   `canonical` only on a second independent occurrence or human review.

### Write gate (anti-poisoning)
This loop feeds its own output back as input, so a wrong lesson, written once, is
retrieved and reinforced forever. Therefore: prefer not writing over writing
unverified; every lesson states what would falsify it; if a retrieved lesson
contradicts present evidence, trust the evidence and demote the lesson.

### Consolidation (periodic)
When LIBRARY exceeds ~30 entries, merge duplicates, delete superseded entries,
promote recurring candidates, tighten tags. Refactor it like code; don't grow it
like a log.

### LIBRARY entry template
`[Lxxxx] <title> | tier | added: YYYY-MM-DD | tags: … | lesson: … | evidence: … | falsifier: … | supersedes: …`

### Scope boundary (Tonality-specific — read before writing a lesson)
This loop is one of **four** knowledge systems here; keeping them disjoint is what
prevents drift. A lesson belongs in LIBRARY **only if none of these own it**:
- **ROADMAP.md** owns *decisions and plans* (Decisions on record, phase gates). A
  new decision or a "what to build next" is a ROADMAP edit, NOT a LIBRARY lesson.
- **Per-layer CLAUDE.md / the code** own *code-structure facts* (module homes,
  layer rules). Where a function lives is not a lesson.
- **`~/.claude/…/memory/`** auto-memory owns *this user's private, machine-local*
  cross-session state. LIBRARY is instead **repo-shared** (committed, travels via
  git to the audit / port / consumer agents).

LIBRARY therefore holds only **repo-shared agent-process lessons** — the hard-won,
evidenced "how to work in this repo without re-tripping a wire" that any thread's
agent benefits from and that is not a decision, a plan, or a code fact.

Retrieval tags (domain-tuned): `workflow` (harness/CI gotchas) · `architecture`
(layer/import invariants) · `contracts` (what must not silently change) ·
`coordination` (dev/audit/port/consumer thread interlock) · `theory-traps`
(music-math correctness subtleties).
<!-- KNOWLEDGE-LOOP:END -->
