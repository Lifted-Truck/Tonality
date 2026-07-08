"""Freezability / realtime-fitness check — human-readable runner (efficiency audit).

The invariant this checks was **promoted into ``tests/`` on 2026-07-08**: the CI
gate now lives in ``tests/test_freezability.py`` (a real, blocking test). This
script stays as a convenient report — it reuses the test's scan so the two can't
drift — printing a clean/violation summary with a non-zero exit on a finding.

The invariant: the pure layers must be free of **wall-clock reads** (``time.time``
/ ``perf_counter`` / ``datetime.now`` …) and **unseeded RNG** (``random.random`` /
``choice`` / … — seeded ``random.Random(seed)`` is fine), because the realtime
contract (ROADMAP Decisions 10/11) freezes engine outputs to static artifacts and
that only works if cores are deterministic + reproducible.

    .venv/bin/python3.13 benchmarks/freezability.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# One source of truth — the CI gate owns the scan.
from tests.test_freezability import CORE_DIRS, scan_pure_layers  # noqa: E402


def main() -> int:
    findings = scan_pure_layers()
    scanned = ", ".join(CORE_DIRS)
    if not findings:
        print(f"freezability: CLEAN — no wall-clock / unseeded RNG in mts/{{{scanned}}}")
        print("(enforced as a CI gate: tests/test_freezability.py)")
        return 0
    print(f"freezability: {len(findings)} VIOLATION(S) in the pure layers:")
    for rel, line, kind, snippet in findings:
        print(f"  {rel}:{line}  [{kind}]  {snippet}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
