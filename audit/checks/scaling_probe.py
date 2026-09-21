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
    from mts.temporal import (
        classify_chromatic_events,
        confirm_key_areas,
        find_scale_runs,
        part_profiles,
        part_relations,
    )
    from mts.generate.modal import modal_transform

    MAJOR_DEGREES = [0, 2, 4, 5, 7, 9, 11]

    def _two_voice(n):
        return _canonical_sequence(
            [[i * 0.25, 0.25, 60 + (i % 12), "a" if i % 2 else "b"] for i in range(n)]
        )

    def _diatonic_melody(n):
        # One voice, walking the C-major degrees — feeds confirm_key_areas /
        # classify_chromatic_events / modal_transform without raising (they
        # need a non-empty sequence, not a specific harmonic shape).
        return _canonical_sequence(
            [[i * 0.5, 0.5, 60 + MAJOR_DEGREES[i % 7], "melody"] for i in range(n)]
        )

    def _scale_walk(n):
        # find_scale_runs requires a monophonic line; walk up/down the degrees
        # so every window is a maximal scale run.
        pcs, idx, up = [], 0, True
        for _ in range(n):
            pcs.append(60 + MAJOR_DEGREES[idx % 7] + 12 * (idx // 7))
            idx = idx + 1 if up else idx - 1
            if idx >= 21 or idx <= 0:
                up = not up
        return _canonical_sequence([[i * 0.5, 0.5, pcs[i], "melody"] for i in range(n)])

    report("part_profiles", _two_voice, part_profiles)
    report("part_relations", _two_voice, part_relations)
    report("confirm_key_areas", _diatonic_melody, confirm_key_areas,
           sizes=(200, 400, 800, 1600))
    report("classify_chromatic_events", _diatonic_melody, classify_chromatic_events,
           sizes=(200, 400, 800, 1600))
    report("find_scale_runs", _scale_walk, find_scale_runs,
           sizes=(200, 400, 800, 1600))
    report("modal_transform", _diatonic_melody,
           lambda seq: modal_transform(seq, MAJOR_DEGREES, target_root=2),
           sizes=(200, 400, 800, 1600))
