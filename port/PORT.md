# The C++ port thread — contract & scaffolding

> **Read this first if you are the port agent.** This is the handoff contract
> between the Python dev loop (this repo) and the C++ port thread. *What* to
> build and in what order lives in **[CPP_PORT.md](../CPP_PORT.md)**; direction
> of record is **[ROADMAP.md](../ROADMAP.md) Phase 8** (Decision 10, revised:
> dual implementation — C++ is the performance/generative/embedded main, the
> Python engine stays a fully-functional peer). This document is the *how*:
> repo scaffolding, fixture flow, and the protocol that keeps the two threads
> accountable to one another without meetings.

## Adopted defaults (from CPP_PORT.md's open questions, 2026-07-03)

Julian greenlit the port with these defaults — revisit only with him:

1. **Separate sibling repo** — `~/Documents/tonality-core`, GitHub under
   `Lifted-Truck`. Different language, different build system; fixtures cross
   over as data.
2. **No bindings in slice 1** — core + parity harness first; pybind11 later,
   as an optional fast path (never a replacement — Decision 10).
3. **Embedded/WASM are free side-effects**, not slice-1 constraints. Write a
   clean core; don't contort for no-heap yet.
4. **Slice 1b (chirality/DFT-phase) held** until A6's open chirality questions
   settle for a quiet cycle; its fields join the export table first.

## Repo scaffolding (this machine's quirks are real — respect them)

- **Toolchain:** Command Line Tools only — no Xcode, no Ninja. Configure CMake
  with `-G "Unix Makefiles"`. Unix Makefiles is single-config: separate build
  dirs for Debug/Release; all perf claims from Release (`-O3`) only.
- **Always pass absolute build paths** (`cmake --build /abs/path/to/build …`)
  — the agent sandbox resets cwd between shell calls, and a relative build
  silently builds nothing.
- **C++17 or 20, CMake.** Header-only where it helps. Suggested layout:

  ```
  tonality-core/
    CMakeLists.txt
    include/tonality/     bitmask.hpp, set_class.hpp, dft.hpp, …
    src/                  (if anything isn't header-only)
    fixtures/tonality/    vendored fixtures + PIN.json (see below)
    tests/                the parity harness (the definition of done)
    tools/                codegen + fixture refresh scripts
  ```

- **`constexpr` tables over the 4096 mask universe**, generated from the
  vendored export by a small codegen step (itself diffable, committed output).

## Fixture flow (Python repo → port repo)

The Python engine is the spec's source of truth. The port never re-derives
correctness — it reproduces fixtures:

1. Generate from a Tonality checkout (venv lives at the Tonality repo root):

   ```bash
   /Users/machinepriest/Documents/Tonality/.venv/bin/python3.13 \
     /Users/machinepriest/Documents/Tonality/scripts/export_versioned_data.py \
     --out /tmp/export_artifacts/
   ```

   → `set_class_table.json` (4096 rows, list index == mask), `manifest.json`,
   `bundle.json`. Also copy `tests/golden/conformance.json`.

2. Vendor them under `fixtures/tonality/`, and record a **`fixtures/PIN.json`**:
   the Tonality commit sha they were generated from, plus a sha256 per file.
   Every parity run states which engine version it is parity *with*.

3. **Slice-1 definition of done** (from CPP_PORT.md): regenerate
   `set_class_table.json` from the C++ core and diff **byte-for-byte** against
   the vendored export; reproduce the `set_class_info` conformance case within
   the golden tolerances (rel 1e-9 / abs 1e-12).

## The accountability protocol (the "hooks" answer)

Both directions are mechanical — a human never has to remember to tell the
other thread anything.

**Tonality → port (the push side, already live in this repo).**
[`port/pin.json`](pin.json) fingerprints the ported surface (table contents +
field list + export schema version + the ported conformance cases).
[`tests/test_port_pin.py`](../tests/test_port_pin.py) compares the live engine
against it on **every suite run — including the dev loop's Stop hook**, so a PR
that changes the ported surface *cannot pass tests* until the author:

1. reruns `scripts/update_port_pin.py` (regenerates the pin),
2. commits the new `port/pin.json` in the same PR,
3. files a notice in `integrations/tonality-core/` (the standard consumer
   channel — see [integrations/README.md](../integrations/README.md)).

We deliberately ride the *existing* pytest Stop hook rather than adding new
hook plumbing: it binds every agent and CI run on any machine, not one
device's settings file, and it costs nothing extra to maintain.

**Port → Tonality (the pull side, build it into tonality-core early).**
A `tools/refresh_fixtures` script (make it slice-0): regenerate the export
from the Tonality checkout, diff against `fixtures/tonality/`, and

- **no diff** → parity claims stand; nothing to do;
- **diff** → refresh the vendored fixtures, update `fixtures/PIN.json` to the
  new Tonality commit, re-run the parity harness, and commit — one PR, with
  the notice from `integrations/tonality-core/` linked as the cause.

Run it at the start of any port work session and before tagging any release.

**The channel.** `integrations/tonality-core/` in the Tonality repo, standard
protocol: notices/briefs in, responses out, verbatim in / evidenced out.
Engine-side asks from the port thread (e.g. "add chirality fields to the
export" for slice 1b) are **briefs**, answered by the dev loop — the port
agent does not edit `mts/` directly.

## Fences (mirror of the audit thread's)

- The port agent works in **tonality-core**, on branches + PRs there. In the
  Tonality repo it may write **only** under `integrations/tonality-core/`
  (notices/briefs, via PR).
- **Python is the spec.** A disagreement between implementations is a port bug
  until the conformance golden says otherwise; goldens and pins regenerate
  only on the Tonality side.
- **Port by stability.** Slice scope is the contract — nothing beyond
  `SET_CLASS_TABLE_FIELDS` until slice 1 is byte-identical, and nothing past
  the Phase 6 fence regardless.
- **Acceptance blocks on every PR** (both repos): for port slices, literally
  "reproduces these N fixture rows / M conformance cases against engine
  commit `<sha>`".
- Perf claims: Release builds only, and record the numbers in the PR.
