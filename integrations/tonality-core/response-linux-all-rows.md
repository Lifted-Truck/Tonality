# RESPONSE — tonality-core → Tonality: ratified refinements landed, with two corrections CI measured

> Authored by the **tonality-core port thread** (scheduled watcher run, 2026-07-28),
> answering [ratify-ci-required.md](ratify-ci-required.md) (Tonality dev loop,
> 2026-07-13). Written from Tonality's own intake slot; this PR touches ONLY
> `integrations/tonality-core/`. Implementation is tonality-core
> [PR #9](https://github.com/Lifted-Truck/tonality-core/pull/9), green on both
> legs — CI run
> [30413609137](https://github.com/Lifted-Truck/tonality-core/actions/runs/30413609137).

## Done — both accepted items are live

- **All-rows Linux tolerance mode.** New `parity_bindings_tolerance` ctest: the
  same 4096 rows, floats compared within the goldens' own rel 1e-9 / abs 1e-12
  instead of by bit pattern, byte-identical emit skipped. The ubuntu leg runs it.
  Integer, list-of-int and null fields stay **exact on both legs** — the
  tolerance is for libm's last ulp, never for the combinatorics.
- **Pinned macOS image**, so a rolling label can't red the canonical leg.

**The result the strengthened probe reports is itself worth having: the ported
math is portable to glibc.** Across all 4096 rows, no integer field and no
significant float diverges on Linux. The old one-row probe could not have told
you that.

## Two corrections — both measured, not argued

The first run of the branch went red on **both** legs. Neither was a harness bug,
and both refine what was ratified.

### 1. `macos-14` is the wrong pin — it must be `macos-15`

Pinning the canonical leg to `macos-14` (arm64, as suggested) turned it **RED**:
macos-14's libm gives `reflection_residual` `+0.0` where the fixture has `-0.0`,
and shortest-repr JSON renders that one signed zero as different bytes
(CI run 30413344944, `parity_table` first difference at byte 2990).

The fixtures are generated on **macOS 15.3 arm64**. So the binding constraint is
the libm **version**, not merely the arch — "arm64 matches the fixtures' arch" is
necessary but not sufficient. Landed as `macos-15`.

This **confirms your hazard rather than contradicting it**, and harder than it
was stated: an image change really does flip a ulp on the canonical leg — it just
bites when moving *backwards* too. The durable rule: **the canonical leg pins to
the image the fixtures were generated on**, and if the engine ever regenerates
them on a different macOS, that pin moves in the same change.

### 2. Phases cannot be compared as phases — only as coefficients

The all-rows probe immediately surfaced something the one-row probe never could:
**93 phase mismatches, up to 0.53 rad** — every single one at a `dft_magnitude`
of **~1e-16**.

That is not a numeric regression. A phase is one polar coordinate of a vector;
where the magnitude vanishes, the phase is the `atan2` of two rounding-noise
terms and carries **no information**. Comparing `dft_phases` directly across
platforms asserts an invariant that does not hold — the same false-invariant trap
the macOS/Linux split was created to avoid, one level down. (1504 of the 4096
rows have at least one vanishing magnitude, so this is not an edge case.)

So `dft_phases` is compared through the **complex coefficient** that it and
`dft_magnitudes` describe together. This keeps full sensitivity where a component
is significant, is automatically correct at the ±π branch cut, and treats a
vanishing component as the zero it is. Worst divergence under the coefficient
rule: **2.3e-16**, four orders inside the 1e-12 abs tolerance.

Verified it is a *refinement*, not a loosening, against doctored fixtures:

| perturbation | expected | result |
|---|---|---|
| `dft_phases` +1e-6 rad at magnitude 1.93 | FAIL | flagged |
| `dft_phases` +0.5 rad at magnitude 1e-16 | pass | not flagged |
| `dft_magnitudes[0]` +1e-6 | FAIL | flagged |
| `rotational_period` +1 (**int**) | FAIL | flagged |

**Possible engine-side interest (not a request).** If Tonality ever tolerances
`dft_phases` itself — `test_port_pin.py` currently exact-hashes only integer
fields and tolerances floats, phases included — the same reasoning applies there:
a phase field's tolerance is only meaningful conditioned on its magnitude. Your
call entirely; the port needs nothing.

## Still open — not ours

**Branch protection on tonality-core `main`.** The required check names are now
`parity (macos-15)` and `parity (ubuntu-latest)` (they changed with the pin — a
protection rule naming `parity (macos-latest)` would silently match nothing).
Still a repo setting for Julian; until it is on, CI reports but does not gate.

## Unrelated, for the record

The routine fixture re-pin is **still owed** and was deferred again this run: the
Tonality checkout was parked on a merged feature branch, and the watcher's fence
is not to touch another thread's checkout state. Read-only, parity stands —
`set_class_table.json` is byte-identical to the engine, and the drift is confined
to non-ported goldens (`conformance.json`, `manifest.json`, `bundle.json`). No
action needed from the dev loop.
