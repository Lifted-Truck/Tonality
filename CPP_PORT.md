# Tonality C++ Core — Port Plan (draft for review)

> Status: **planning** (no agent spawned yet). This is the build + acceptance plan
> for the Phase 8 / Decision-10 C++ core migration, scoped for a parallel effort.
> Direction of record lives in [ROADMAP.md](ROADMAP.md) Phase 8; this doc is the
> concrete *how*. Julian reviews this before any C++ work starts.

## Why

A native C++ core makes Tonality an **efficient generative tool** — the pitch-class
combinatorics (set-class search, DFT, voice-leading, induction) run orders of
magnitude faster and fit places CPython can't (plugins, embedded/Teensy, WASM).
Decision 10: **port once, bind back** — one C++ core, Python bindings, every
existing consumer keeps working through the bindings.

## The parity contract (this is what makes it safe)

We do **not** re-derive correctness in C++. Two artifacts the Python repo already
ships *are* the spec:

1. **`tests/golden/conformance.json`** — one pinned input→output per MCP tool,
   float-tolerant (rel 1e-9 / abs 1e-12). **A C++ build is correct iff it
   reproduces these files.** Language-neutral by construction.
2. **The versioned-data export** (`scripts/export_versioned_data.py` →
   `set_class_table.json` + `bundle.json`) — the precomputed combinatorics +
   versioned priors a port consumes instead of reimplementing, already validated
   row-vs-engine.

So the acceptance gate for every port slice is mechanical: **load the Python repo's
exported fixtures, reproduce them.** No judgment calls, no drift.

## Scope — port by *stability*, not wholesale

The ROADMAP's sequencing fence ("port after the 12-TET surface is frozen — porting
first means porting twice") is real: the analysis surface is actively growing
(chirality family, meter, representation, all in the last week). We respect it by
porting only the **frozen** subset now.

### Slice 1 — the identity layer the export table already covers (START HERE)

Exactly the fields in `SET_CLASS_TABLE_FIELDS` — the subset we've already declared
stable enough to ship as a frozen *data* contract:

- 12-bit mask ops (membership, subset, rotation, invert, complement)
- normal order, **Rahn prime form** (min-mask over 24 images), prime-form mask
- interval vector, cardinality
- **DFT** components → magnitudes
- Z-relation partner, rotational symmetry order

**Acceptance:** regenerate `set_class_table.json` from the C++ core and diff it
byte-for-byte against the Python export (4096 rows); reproduce the `set_class_info`
conformance case within tolerance. `constexpr` tables over the 4096 universe — this
is the cleanest, most C++-native layer, and it's genuinely frozen (mod-12
combinatorics don't change even if Phase 6 renegotiates the substrate).

### Slice 1b — DFT phase + the chirality family (fast-follow, once it settles)

`dft_phases`, `general_chirality`, `chirality_sign`, `reflection_residual`,
`chirality`. Pure mod-12 DFT math, but **newer** (shipped this week) and A6 may
still iterate (the absolute-weighting / geometric-sign questions are open). Port
after one quiet cycle, and **add these fields to the export table first** so the
same fixture-diff acceptance applies. (The `reflection_residual` minimizer is the
one numerically-sensitive piece — port the grid-bracket + golden-section refine
exactly, or accept it under the float tolerance.)

### Deferred (behind the fence)

Analysis (naming/evidence, induction, VL, containment, succession), temporal
(sequence/segmentation/tracking/atoms), MIDI I/O, the representation descriptors,
the MCP/bridge tool surfaces. These wait until the 12-TET surface freezes (Phase 6).
Sizing on record: core-only ≈ **3–5 weeks**; full parity ≈ 3–5 person-months.

## Mechanics

- **Separate repo** (it's a different language + build system) — e.g.
  `tonality-core`. It consumes this repo's exported fixtures (`conformance.json`,
  `set_class_table.json`, `bundle.json`) checked in as test data, refreshed on a
  pinned engine version.
- **C++17/20, CMake**, header-only where it helps; `constexpr` set-class tables
  generated from the export (a small codegen step, itself diffable).
- **A parity test harness** is the deliverable's backbone: load the fixtures,
  assert reproduction. That harness *is* the port's definition of done, slice by
  slice.
- **pybind11 bindings deferred** — slice 1 ships the C++ core + the parity test
  runner (and optionally a tiny CLI). Bindings come once the core subset is green,
  so "the Python package becomes a shim" is a later, separate step.
- **Engine-side support already done:** the export + conformance harness. The only
  new engine-side work is *adding the chirality/phase fields to the export table*
  for slice 1b (small, additive).

## How you stay looped in (per this session's decisions)

- **Build-then-review with acceptance blocks:** each port slice (and each engine
  feature going forward) ships a PR carrying a short **acceptance block** — what it
  should do, and the exact fixtures/cases that prove it. For the port, the
  acceptance block is literally "reproduces these N fixture rows / M conformance
  cases."
- **Live walkthroughs:** capability review happens interactively — I demo any
  engine behavior live through the tools and we probe it together, rather than you
  reading JSON. The conformance cases are the natural script for those sessions.

## Open questions for you (decisions before we spawn)

1. **Repo:** new `tonality-core` repo, or a `cpp/` subtree in this one? (I lean
   separate repo — clean build, and the fixtures cross over as data.)
2. **Bindings in slice 1?** I propose **no** — core + parity harness first, pybind11
   after. Confirm or pull it forward.
3. **Embedded/WASM:** treat the Teensy/WASM profiles as free side-effects of a clean
   core (default), or an explicit constraint on slice 1 (e.g. no-heap, fixed
   tables)? I lean "free side-effect, don't over-constrain slice 1."
4. **Who builds it:** a background agent in the new repo, graded by the parity
   harness — spawn once you approve this scope.
5. **Chirality timing:** fold slice 1b in now (add the fields to the export first),
   or hold it a cycle until A6's open chirality questions settle? I lean hold.
