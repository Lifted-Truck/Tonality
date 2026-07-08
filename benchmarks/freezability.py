"""Freezability / realtime-fitness static check (efficiency audit, Layer-E).

The realtime contract (ROADMAP Decisions 10/11): a real-time consumer never calls
the engine live — it reads a *frozen* contract artifact or embeds the C++ core.
That only works if engine outputs are **reproducible and freezable**, which
requires the pure layers to be free of:

  - **wall-clock reads** (``time.time`` / ``perf_counter`` / ``datetime.now`` …) —
    a core that reads the clock cannot be frozen to a deterministic artifact;
  - **unseeded RNG** (``random.random`` / ``choice`` / … without an explicit
    seed) — non-reproducible. Seeded ``random.Random(seed)`` is fine.

This scans the pure layers (not the mcp/ adapters, not benchmarks/tests) and
reports any violation. Deterministic — a candidate to promote into ``tests/`` as
a guaranteed invariant once it has proven its worth (per the audit-charter
promotion path). Exit code is non-zero on a finding.

    .venv/bin/python3.13 benchmarks/freezability.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# The pure layers whose outputs must be freezable. mcp/ (adapters) and io/midi
# streaming are intentionally excluded — IO edges may read the clock.
CORE_DIRS = (
    "core", "analysis", "rules", "temporal", "search",
    "representation", "theory", "context",
)

_WALLCLOCK = re.compile(
    r"\b(?:time\.(?:time|perf_counter|monotonic|process_time)"
    r"|datetime\.(?:now|utcnow)|date\.today)\s*\("
)
# random.<x> that is NOT random.Random( — i.e. the module-global unseeded RNG.
_UNSEEDED_RANDOM = re.compile(
    r"\brandom\.(?!Random\b)"
    r"(?:random|choice|choices|randint|shuffle|uniform|sample|getrandbits|randrange|gauss)\b"
)


def _strip_comment(line: str) -> str:
    """Drop an inline ``#`` comment so a mention in prose isn't a false positive.

    Naive (doesn't parse strings) but adequate: the patterns we hunt are calls,
    which don't appear inside a trailing comment we'd want to keep.
    """
    hashpos = line.find("#")
    return line if hashpos == -1 else line[:hashpos]


def scan() -> list[tuple[str, int, str, str]]:
    findings: list[tuple[str, int, str, str]] = []
    for sub in CORE_DIRS:
        base = REPO / "mts" / sub
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            for i, raw in enumerate(path.read_text().splitlines(), 1):
                line = _strip_comment(raw)
                rel = str(path.relative_to(REPO))
                if _WALLCLOCK.search(line):
                    findings.append((rel, i, "wall-clock read", raw.strip()))
                if _UNSEEDED_RANDOM.search(line):
                    findings.append((rel, i, "unseeded RNG", raw.strip()))
    return findings


def main() -> int:
    findings = scan()
    scanned = ", ".join(CORE_DIRS)
    if not findings:
        print(f"freezability: CLEAN — no wall-clock / unseeded RNG in mts/{{{scanned}}}")
        return 0
    print(f"freezability: {len(findings)} VIOLATION(S) in the pure layers:")
    for rel, line, kind, snippet in findings:
        print(f"  {rel}:{line}  [{kind}]  {snippet}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
