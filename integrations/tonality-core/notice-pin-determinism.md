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

The **fingerprint** now rounds every float to **10 decimals** (`+ 0.0` to
collapse `-0.0`/`0.0`) before hashing — tighter than the 1e-9 tolerance the
conformance harness already uses, so real drift still trips it, but last-ULP
platform noise no longer does. The change is in `scripts/update_port_pin.py`
(`_round_floats` in `_canonical_sha256`); the **export itself
(`set_class_table()`) is unchanged** — still full precision, so your vendored
data is byte-identical to before.

**For your side:** nothing about the exported table moved. If your parity check
compares the `set_class_table_sha256`, adopt the new value and, if you fingerprint
the float fields yourself, apply the same round-to-10 (`+ 0.0`) rule so your
Linux/macOS runs agree with ours. The conformance-case comparison is unaffected
(it reads the committed golden, always deterministic).

## Also landing alongside

CI (`.github/workflows/ci.yml`) now runs `pytest tests/` + `pytest audit/checks/`
on every PR — so a drifted pin (or golden) is blocked at PR time, not discovered
by an external audit. The two threads' accountability hook is now enforced, not
just Stop-hook-local. No response needed.
