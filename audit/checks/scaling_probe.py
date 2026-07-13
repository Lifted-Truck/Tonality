"""Efficiency / complexity probe harness for the audit loop (charter §6b).

**Deliberately NOT a pytest test** (no ``test_`` prefix → pytest never collects
it, so it never runs in CI and can never flake a gate). Wall-clock belongs in a
hand-run audit cycle, not a blocking check — the audit is the right home for perf
probes *because* it is out of the CI gate: a superlinear result becomes a
triaged issue, not a red build.

Method: time ``run(make_input(n))`` at geometric sizes, take the best of a few
repeats per size (``min`` = the least-contended sample), and fit the median
log-log slope. An O(n) path fits an exponent ≈ 1.0; O(n²) fits ≈ 2.0. **Exponents
are machine-independent** — the *shape* transfers across machines even though the
absolute milliseconds do not, which is exactly why the charter asserts on the
exponent and never on a millisecond threshold.

Constructing a new probe is three lines — a ``make_input(n)`` (deterministic, no
RNG), the callable under test, and one ``report(...)`` call; see ``__main__``.
"""

from __future__ import annotations

import time
from math import log


def estimate_exponent(make_input, run, sizes=(1000, 2000, 4000, 8000), repeats=3):
    """Fit the empirical growth exponent of ``run`` over ``make_input(n)``.

    ``make_input(n)`` builds a size-``n`` input deterministically (no RNG — the
    audit is reproducible); ``run(x)`` executes the code under test. Returns
    ``(exponent, timings)`` where ``timings`` is ``[(n, best_seconds), …]``.
    """
    timings = []
    for n in sizes:
        x = make_input(n)
        best = min(_time_once(run, x) for _ in range(repeats))
        timings.append((n, best))
    # median of the pairwise log-log slopes — robust to a single contended sample.
    slopes = sorted(
        log(t2 / t1) / log(n2 / n1)
        for (n1, t1), (n2, t2) in zip(timings, timings[1:])
        if t1 > 0 and t2 > 0 and n2 > n1
    )
    exponent = slopes[len(slopes) // 2] if slopes else float("nan")
    return exponent, timings


def _time_once(run, x) -> float:
    start = time.perf_counter()
    run(x)
    return time.perf_counter() - start


def report(name, make_input, run, *, expected_max=1.4, **kwargs) -> float:
    """Print a one-line verdict suitable for a cycle-log row or an issue body.

    ``expected_max`` is the exponent ceiling for a path the charter says must be
    ~linear (1.4 leaves generous headroom for constant-factor / cache noise while
    still catching a genuine quadratic at ≈2.0). Returns the fitted exponent.
    """
    exponent, timings = estimate_exponent(make_input, run, **kwargs)
    verdict = "OK" if exponent <= expected_max else "SUPERLINEAR — file an issue"
    trail = "  ".join(f"n={n}:{t * 1000:.1f}ms" for n, t in timings)
    print(f"[{name}] exponent≈{exponent:.2f} (expect ≤{expected_max})  {verdict}\n    {trail}")
    return exponent


if __name__ == "__main__":
    # Template: the temporal entry points the ROADMAP plans to run at corpus
    # scale must stay ~linear. Add the newest scalable surface here each cycle.
    from mts.mcp.tools import _canonical_sequence
    from mts.temporal import part_profiles, part_relations

    def _two_voice(n):
        return _canonical_sequence(
            [[i * 0.25, 0.25, 60 + (i % 12), "a" if i % 2 else "b"] for i in range(n)]
        )

    report("part_profiles", _two_voice, part_profiles)
    report("part_relations", _two_voice, part_relations)
