# NOTICE — Tonality → tonality-core: stand up CI (the parity harness must run on every PR)

> 2026-07-09, Tonality dev loop, prompted by Julian ("I want to make sure there is
> a rigorous and reliable testing regime in place to keep the projects from
> straying — the whole point of the port watcher routine"). **Ball: port thread.**
> This is an ask, not a patch — writes stay home (INTEGRATIONS §3 rule zero), so
> the port's residents own the workflow file; this notice specifies what and why.

## The finding

The port's *discipline* is good — every watcher PR carries an acceptance block and
reports the three parity ctests green. But **verification is entirely manual and
single-machine**:

- `tonality-core` has **no `.github/workflows/`** — zero CI runs on any push or PR;
- `main` has **no branch protection** — a PR can merge with nothing checked;
- `PORT.md` line ~92 *already promises* the fixtures/PIN mechanism "binds every
  agent and **CI run** on any machine" — the contract assumes CI that was never
  stood up. (A docs↔reality drift of exactly the kind Tonality's new
  semantic-coherence audit checks for.)

Why it matters, concretely: **the pin-determinism incident is the proof.** The
engine's pin was green on the machine that generated it and red everywhere else —
caught only because Tonality's CI ran a matrix. A single-machine parity claim has
the same exposure: float ULP drift, compiler/platform differences, and stale-run
mistakes are invisible until someone else builds it.

## The ask (port-side, one workflow file + one setting)

1. **CI workflow** on push + PR:
   - configure + build (`cmake -B build -DTONALITY_BUILD_PYTHON=ON`, Release);
   - run the existing harness — `ctest` (`parity_table`, `parity_conformance`,
     `parity_bindings`) — no new tests needed, just automation of what the PRs
     already run by hand;
   - **matrix: `ubuntu-latest` + `macos-latest`** — the ULP lesson: cross-platform
     is the point, one OS re-creates the single-machine trap;
   - pybind11/Python needed by `parity_bindings` installed in the job.
2. **Branch protection on `main`**: require the CI checks green before merge (and
   consider auto-delete-head-branches, which also fixes stacked-PR retargeting).
3. **Watcher contract note in the port's README/PORT docs**: the watcher's
   refresh PRs merge only on green CI — the acceptance block *cites* the CI run
   instead of a local build.

## What Tonality already guards (so the seam is covered from both ends)

- `tests/test_port_pin.py` runs in **Tonality's CI** (3.10 + 3.13) — the engine
  cannot drift from the pinned surface without a red build here.
- The conformance golden + versioned-data export are regenerated only through
  reviewed PRs, and notices announce every pinned-surface change on this channel.

The gap is only the port's half: nothing *there* verifies a refresh PR
automatically. With its CI up, the loop is closed — engine drift fails Tonality's
build, port drift fails tonality-core's build, and the watcher becomes an
automated, evidenced loop rather than a manual ritual.

No respond-by pressure — but the next watcher refresh PR is the natural moment to
land the workflow (verify it catches its own build first). Reply on-channel when
CI is live and we'll record the closed loop in ROADMAP.
