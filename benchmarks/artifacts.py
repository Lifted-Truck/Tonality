"""Contract-artifact freeze/load cost (efficiency audit, Layer-E).

Decision 11: a real-time consumer reads a *frozen* JSON contract artifact, so the
artifacts must be **small** and **fast to load**. This measures, for a few
representative outputs, the serialized JSON byte size and the round-trip cost
(``to_dict`` → ``json.dumps`` → ``json.loads`` → ``from_dict`` where available).
Machine-specific; a relative/regression signal, not a gate.

    .venv/bin/python3.13 benchmarks/artifacts.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from mts.rules import (  # noqa: E402
    TransitionMatrix,
    build_transition_matrix,
    induce_ruleset,
)
from mts.mcp import tools  # noqa: E402

_CMAJ = (0, "major")
_CORPUS = [
    ([(0, "maj"), (5, "maj"), (7, "maj"), (0, "maj")], _CMAJ),
    ([(0, "maj"), (2, "min"), (7, "maj"), (0, "maj")], _CMAJ),
    ([(0, "maj"), (9, "min"), (7, "maj"), (0, "maj")], _CMAJ),
]


def _time(fn, runs=200):
    best = float("inf")
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        best = min(best, (time.perf_counter() - t0) * 1000.0)
    return best


def main() -> int:
    rows = []

    # A transition matrix — the gap-14 contract artifact.
    tm = build_transition_matrix(_CORPUS, state="degree", source="bench")
    tm_json = json.dumps(tm.to_dict())
    rows.append((
        "transition_matrix (degree)",
        len(tm_json.encode()),
        _time(lambda: TransitionMatrix.from_dict(json.loads(tm_json))),
    ))

    # An induced ruleset — the constraint artifact.
    rs = induce_ruleset(family="harmony", chord_corpus=_CORPUS).to_dict()
    rs_json = json.dumps(rs)
    rows.append(("induced ruleset (harmony)", len(rs_json.encode()), _time(lambda: json.loads(rs_json))))

    # set_class_info — a small identity artifact.
    sc_json = json.dumps(tools.set_class_info(pcs=[0, 4, 7]))
    rows.append(("set_class_info [0,4,7]", len(sc_json.encode()), _time(lambda: json.loads(sc_json))))

    print("contract-artifact freeze/load — size + load round-trip\n")
    print(f"  {'artifact':<30}{'size (bytes)':>14}{'load (ms)':>12}")
    print(f"  {'-' * 28:<30}{'-' * 12:>14}{'-' * 10:>12}")
    for name, size, load in rows:
        print(f"  {name:<30}{size:>14,}{load:>12.4f}")
    print("\n  (target: contract artifacts small ~KB + sub-ms load; machine-specific)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
