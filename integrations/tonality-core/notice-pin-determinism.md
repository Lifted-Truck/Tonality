# NOTICE — Tonality → tonality-core: port pin regenerated (fingerprint made platform-deterministic)

> 2026-07-07, dev loop. `port/pin.json`'s `set_class_table_sha256` changed
> (`91576bc…` → `16917db5…`) and `pinned_at_commit` moved to `86ee10d`. **Not a
> surface change — a determinism fix.** Refresh your vendored fixtures against
> the new pin; your parity harness's *values* are unchanged (within tolerance).

## What happened

An external maturity audit caught the one failing test on a fresh clone: the pin
was green on the machine that generated it but red elsewhere. Root cause — the
fingerprint hashed the set-class table's **float** fields (`dft_magnitudes`,
`dft_phases`, and the chirality family) at full precision via exact `sha256`.
Those agree across IEEE-754 platforms only to the last few ULPs (~1e-15 at these
magnitudes), so macOS and Linux computed different hashes for identical logic.
The pin was effectively machine-specific.

## The fix (relevant to your parity harness)

The **fingerprint now hashes only the exactly-reproducible integer/combinatorial
fields** of the set-class table — `mask, cardinality, normal_order, prime_form,
prime_form_mask, interval_vector, z_partner_prime_form, complement_prime_form,
rotational_period` (recorded in the pin as `set_class_table_sha256_fields`).
Those are pure bit/integer arithmetic, bit-identical on every conforming
platform. The transcendental/iterative **float** fields (DFT magnitudes/phases,
the chirality family, reflection_residual) are *dropped from the exact hash* —
exact-hashing them is inherently machine-specific (we first tried rounding to
1e-10; CI proved it still drifted macOS↔Linux). The **export itself
(`set_class_table()`) is unchanged** — still full precision, all 16 fields
(`set_class_table_fields` still lists them) — so your vendored data is
byte-identical to before.

**For your side:** the exported table is unchanged; only what the pin
*exact-hashes* narrowed to the integer surface. Compare the float fields the way
this engine does — **with tolerance** (the conformance harness uses 1e-9; your
parity harness already does the same per PORT.md), never by exact hash. The
conformance-case comparison (`ported_conformance_cases_sha256`) is unaffected —
it reads the committed golden, always deterministic.

## Also landing alongside

CI (`.github/workflows/ci.yml`) now runs `pytest tests/` + `pytest audit/checks/`
on every PR — so a drifted pin (or golden) is blocked at PR time, not discovered
by an external audit. The two threads' accountability hook is now enforced, not
just Stop-hook-local. No response needed.
