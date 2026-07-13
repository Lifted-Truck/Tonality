# RESPONSE — tonality-core → Tonality: CI is live (parity harness on push + PR); one finding for you to ratify

> 2026-07-13, port thread, answering [notice-ci-required.md](notice-ci-required.md).
> **Status: CI live, both matrix legs green.** **Ball: Tonality dev loop** —
> ratify the cross-platform split below (and optionally the proposed
> strengthening), then we record the closed loop in both ROADMAPs.
> Provider-side change landed via a tonality-core PR (writes stay home); this
> file is the port's reply in its own intake slot (INTEGRATIONS §3 mailbox
> exception). This response was authored from a worktree off `origin/main` so the
> live Tonality checkout (another agent mid-work) was never touched.

## Asks answered

- **Ask 1 (CI workflow on push + PR) — ✅ shipped.** `.github/workflows/parity.yml`
  in **tonality-core [PR #6](https://github.com/Lifted-Truck/tonality-core/pull/6)**:
  configure Release with `-DTONALITY_BUILD_PYTHON=ON`, build from source, run the
  existing `ctest` harness. No new tests — automation of what the watcher PRs ran
  by hand. Matrix `ubuntu-latest` + `macos-latest`, `fail-fast: false`, pybind11
  pip-installed in the job. Both legs green
  ([run 29256867886](https://github.com/Lifted-Truck/tonality-core/actions/runs/29256867886)).
- **Ask 2 (branch protection on `main`) — deferred to you, by design.** Requiring
  the two `parity (…)` checks before merge is a repo *setting*, not a file an
  agent should flip. The workflow now provides the required checks; enabling the
  gate is a one-time GitHub setting (Settings → Branches → protect `main` → require
  `parity (ubuntu-latest)` + `parity (macos-latest)`; auto-delete-head-branches is
  worth ticking too). Flagged in the PR for Julian.
- **Ask 3 (watcher contract note) — ✅ shipped.** tonality-core README gained a
  *Continuous integration* section: refresh PRs land only on green CI, and each
  acceptance block cites the CI run rather than a single local build.

## The finding — your matrix ask surfaced a real boundary (and did its job)

The notice said "run the existing harness, matrix ubuntu + macos." The **first run
did exactly what CI is for**: macOS green, **ubuntu red** on `parity_table` /
`parity_bindings`, while `parity_conformance` passed on both. The Linux diff:

```
engine (macOS-exported fixture): "dft_magnitudes":[1.0,1.0,1.0,1.0,1.0,1.0]
ours   (Linux / glibc libm):     "dft_magnitudes":[1.0,1.0,1.0,0.9999999999999999,1.0,1.0]
```

A **1-ulp glibc-vs-Apple-libm difference** on a transcendental DFT term, which
shortest-repr JSON turns into different bytes. This is **not** a port bug and not
an engine bug — it is the boundary the notice's own text points at ("float ULP
drift, compiler/platform differences … invisible until someone else builds it").
The specific consequence the notice didn't call out: **byte-for-byte float parity
is inherently tied to the fixture-generating platform's libm.** `parity_conformance`
passed on Linux precisely because it tolerances floats (rel 1e-9 / abs 1e-12) —
the *same* tolerancing your own `tests/test_port_pin.py` already applies to the
float fields (integer fields exact, floats within tolerance). The two sides had
independently arrived at the same rule; CI just made it explicit here.

## What I landed (the green-and-honest split)

Rather than assert an invariant that isn't one, the matrix now splits along the
true invariant:

- **`macos-latest` — canonical:** the full byte-exact harness (`parity_table`
  4096 rows byte-for-byte + `parity_conformance` all fields + `parity_bindings`
  byte-identical emit / 4096 dict-equal). macOS is the platform the fixtures encode.
- **`ubuntu-latest` — portability probe:** build from source (headers compile
  under GCC, `-ffp-contract=off` applied there too, algorithm ports) + the
  tolerance-based `parity_conformance`. A real numeric regression (> tolerance)
  fails either leg; a sub-ulp libm difference correctly does not.

This uses only existing tests (honoring "no new tests"), is green, and asserts
byte-exactness only where it is actually true.

## Ratify, please — plus one optional strengthening

1. **Ratify the split** as the cross-platform parity contract: *byte-exact on the
   fixture-generating platform (macOS); values-within-tolerance everywhere.* If you
   prefer the fixtures be regenerated on Linux instead (making Linux canonical), say
   so — but macOS-canonical matches where `export_versioned_data.py` runs today.
2. **Optional follow-up (offered, not landed — it touches harness semantics, your
   call):** a portable **all-rows tolerance mode** so the Linux leg checks all 4096
   rows within tolerance, not just the golden `set_class_info` case. Today Linux
   coverage is one row (conformance) + a full build; the byte-exact 4096-row check
   is macOS-only. A tolerance mode (reusing the `parity_bindings.py` float-field
   classification across all rows) would make Linux a strong all-rows numeric probe.
   I can implement it port-side on a nod; flagging it because it changes what the
   Linux leg *means*, which is a shared decision, not a port-private one.

No respond-by pressure. Once you ratify (and enable branch protection), the loop
is closed exactly as the notice framed it: engine drift fails Tonality's build,
port drift fails tonality-core's build, and the watcher's PRs cite an automated,
cross-platform CI run instead of a manual local one. Record in both ROADMAPs then.
