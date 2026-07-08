"""Per-tool latency baseline (efficiency audit, Layer-E — measured, non-blocking).

Times every MCP tool over its conformance case(s) — the same representative,
deterministic inputs the golden pins — so the workload is maintained for free and
matches what consumers actually call. Reports **min** (the least-noisy estimate of
the hot path) and **median** per call, sorted slowest-first, after a warm-up call
that pays one-time catalog/cache loads (RE-5).

Timing is machine-specific and inherently noisy — this is a **relative** tool
(which tools dominate, and regression tracking across runs), never an absolute
gate. Nothing here blocks CI; it is Layer-E measurement, not a Layer-0 oracle.

    .venv/bin/python3.13 benchmarks/latency.py [runs]
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Reuse the conformance workload: representative, deterministic, already maintained.
from tests.test_conformance import CASES, _run_case  # noqa: E402


def measure(runs: int = 9) -> list[tuple[str, float, float]]:
    rows: list[tuple[str, float, float]] = []
    for name, kwargs in CASES:
        _run_case(name, kwargs)  # warm-up: one-time catalog/cache loads
        samples = []
        for _ in range(runs):
            t0 = time.perf_counter()
            _run_case(name, kwargs)
            samples.append((time.perf_counter() - t0) * 1000.0)  # ms
        rows.append((name, min(samples), statistics.median(samples)))
    return rows


def main() -> int:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    rows = measure(runs)
    # Collapse multiple cases of one tool to that tool's worst (min-time) case.
    worst: dict[str, tuple[float, float]] = {}
    for name, mn, med in rows:
        if name not in worst or mn > worst[name][0]:
            worst[name] = (mn, med)
    ordered = sorted(worst.items(), key=lambda kv: -kv[1][0])

    print(f"per-tool latency (min of {runs} runs, warm cache) — slowest first\n")
    print(f"  {'tool':<26}{'min (ms)':>12}{'median (ms)':>14}")
    print(f"  {'-' * 24:<26}{'-' * 10:>12}{'-' * 12:>14}")
    for name, (mn, med) in ordered:
        print(f"  {name:<26}{mn:>12.3f}{med:>14.3f}")
    total_min = sum(mn for _, (mn, _) in worst.items())
    print(f"\n  {len(worst)} tools · Σ worst-case min = {total_min:.1f} ms")
    print("  (machine-specific; a relative/regression signal, not an absolute gate)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
