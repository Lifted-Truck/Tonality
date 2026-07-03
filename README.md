# Tonality

**A music-theory engine that *derives* its harmonic knowledge rather than storing it — and, where the theory admits more than one reading, returns them ranked and evidenced.**

Tonality is a local-first theory core for twelve-tone equal temperament. It exists
less to *describe* a passage than to be **queried** by the things that make and
transform music — synthesizers, generative sequencers, visualizers, and agents.
Where most theory libraries hand back a single confident label, Tonality takes the
opposite posture: surface every candidate the theory admits, rank them by fit, and
show the evidence behind each. It is a **foundation library**, not an end-user app —
Python, no external services, no network; the catalogs are data you can read and
edit, the analysis is code you can audit.

## The doctrine

Three rules organize everything in the engine.

**Reduce, never invent.** Harmonic knowledge is *derived* from primitives and
explicit rules, not stored as answers the engine can't show its work for. Functional
harmony, chord–scale relationships, and borrowing are computed from interval
structure and scale definitions — the legacy static lookup tables were removed — so
behind every result there is a derivation, not a table someone typed once. The
corollary (the division of labor): precise combinatorics live in the engine, fuzzy
and creative judgment in the caller, and the engine **never fabricates** what you
didn't give it — no register without real notes, no key without evidence. Analyses
that need missing information **error; they don't guess.**

**Plural, ranked, evidenced.** Where the theory admits more than one reading, the
engine returns more than one — ordered by fit, each carrying the evidence
(interval-class fingerprints, pitch-class membership, functional role) that justifies
its rank. A confident wrong answer is treated as worse than a surfaced uncertainty.
(Deterministic facts — a set-class fingerprint, a voice-leading distance — are
reported as the single values they are; it is *interpretation* that comes plural.)

**Built to be consumed, not just read.** Every result is a typed structure for a
downstream caller. The terminal tools are a window onto the engine, not the point of it.

---

## What it can do

Everything below is shipped, tested, and reachable from Python, the MCP endpoint,
or as a JSON dataset. (Full capability schematic: **[INTEGRATION.md](INTEGRATION.md)**.)

### Functional harmony, *derived*
Functional roles, chord–scale compatibility, and modal **borrowing** are computed
from interval structure and scale definitions — not stored tables (the static ones
were removed). Multiple chord options per scale degree, each with its interval stack,
fall out of the derivation; a non-diatonic chord names its candidate borrow-source
and the exact pitch classes it adds or removes; and a validation pass
(`scripts/validate_function_mappings.py`) cross-checks the derived mappings against
scale masks — the engine checking its own work.

### Set-class & harmonic-color analysis
Normal order, **Rahn prime form**, Z-relations, interval vectors, and the
**6-D DFT "harmonic color"** embedding (|f₅| ≈ diatonicity, |f₆| ≈ whole-tone-ness)
— plus DFT **phase** and a complete **chirality family**: scalars that capture a
chord's *handedness*, cleanly separating major from minor and dom7 from m7♭5 where
the interval vector alone cannot. (The complete signed chirality is a small research
result derived in collaboration with a consumer project — see ROADMAP.)

### Naming & contextual disambiguation
Every structurally valid `(root, quality)` reading of a pitch-class set (C6 = Am7;
dim7 names at four roots), then **the** chosen reading inside a key with ranked
alternatives and per-signal evidence — flagging augmented sixths, secondary
dominants, and Neapolitans instead of penalizing their chromaticism.

### Key induction & tracking
Ranked key candidates with scores and a top-two margin from any pc-weight vector;
**windowed local key tracking** into modulation-aware regions; a tonicization-vs-
modulation **structural key-area** reduction; opt-in **continuity priors** and a
relative-major/minor tie-breaker. Empirical knobs ship as **versioned priors**,
cited in every result.

### Meter, rhythm & time
Infer the time signature from note content (never overriding the file's), track it
through **meter changes**, and recover the **downbeat phase** of an anacrusis.
MIDI ingestion, segmentation, harmonic rhythm, voice-motion, melodic and rhythmic
atoms, plus swing/groove feel.

### Voice-leading & succession
Exact minimal voice-leading distance between pc-sets (and over real voicings);
**next-chord recommendations** tagged with functional, voice-leading, and color
evidence; cadence detection (authentic / plagal / half / deceptive).

### Representation — projections as *data*
Render-agnostic numeric descriptions a visualizer can draw however it likes:
**keyboard**, **piano-roll**, **clock/bracelet**, **Tonnetz**, **chord-network**
(a "Cube Dance" voice-leading graph), **colour-content** wheels, and a
voicing-continuous **tonal-orientation** angle. The library emits descriptions;
pixels are an edge consumer's job.

### Built for reproducibility
Typed result objects (never ad-hoc dicts), a **golden conformance harness** that
pins every tool's output, and a **versioned-data export** so a native port (no
Python) can compute the same answers from the same data.

---

## Three ways in

| Door | For | Entry point |
|---|---|---|
| **Python library** | scripting, embedding | `import mts` — pure functions over frozen dataclasses |
| **MCP endpoint** | AI agents | **46 tools**, one per analysis; `python -m mts.mcp` (needs the `mcp` extra) |
| **Dataset / JSON** | offline pipelines | versioned catalogs in `mts/data/`, dataset records from MIDI |

The core data model is two structures: an **identity key** (a pitch-class set as a
12-bit bitmask — what you match and name on) and an optional **realization** (the
actual pitches — what voicing, inversion, and register analysis read). You can
always *reduce* a realization to a key; you can never *invent* register from a key
without choosing a voicing — and choosing is a generative act, not an analytical one.

---

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .            # MIDI parsing (mido) is included; add ".[mcp]" for the MCP server
python examples/quickstart_engine_demo.py
```

You'll get a short report covering interval, chord, scale, and layout objects
sourced from the bundled JSON catalogs. To analyze a chord from the terminal:

```bash
python scripts/analyze_chord.py C maj7 --tonic C --json
```

The `scripts/` folder bundles terminal tools over the analysis layer —
`analyze_scale.py`, `analyze_chord.py`, `check_chord_scale_compat.py`,
`build_scale_or_chord.py`, and `export_versioned_data.py`. Each self-documents via
`-h/--help`.

---

## Data & customization

Reference material is versioned JSON under `mts/data/` — scales (modal/ethnic sets with
alias support), chord qualities (triads through altered 13ths), functional-harmony
tables, key/meter/scoring priors. Empirical values are versioned and cited; theory
sets are never corpus-fit. Adjust the JSON, reload via `mts.io.loaders`, and the
engine picks up the change. `mts/theory/functions.py` derives functional mappings
procedurally from template rules.

---

## Terminal Push grid (legacy)

`mts/cli/push.py` renders a text-based Ableton Push lattice in the terminal
(`python -m mts.cli.push --key Eb --scale Dorian --chord "Bb:maj9" --preset fourths`),
with in-scale validation, layout presets, and enharmonic bias. It was Tonality's
first visualization surface and remains a handy CLI, but **live Push visualization
of chords and theory is now handled by consumer projects** (e.g. Audiology) that
consume this engine through the integration channel — Tonality supplies the
analysis; the consumer owns the surface. See `examples/push_grid_demo.py`.

---

## Where to go next

- **[ROADMAP.md](ROADMAP.md)** — the single source of truth for direction: build
  sequence, architecture decisions, target applications, what's deferred. Any
  forward-looking statement (including this README) defers to it.
- **[INTEGRATION.md](INTEGRATION.md)** — the capability schematic for outside
  consumers: every shipped capability, the three integration doors, the contracts
  to design around.
- **[CLAUDE.md](CLAUDE.md)** — contributor and agent workflow, the architecture
  layers, and the conventions.
- **`integrations/`** — the cross-project exchange channel where consumer projects
  (synths, generators, visualizers) trade briefs and responses with the engine.
