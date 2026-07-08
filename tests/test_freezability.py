"""Freezability invariant — promoted from ``benchmarks/`` to a CI gate (2026-07-08).

The realtime contract (ROADMAP Decisions 10/11) rests on the **pure layers being
deterministic and freezable**: a consumer freezes an engine output to a static
artifact and reads it later, so a core that reads the wall clock or rolls
unseeded dice would make that frozen artifact stale / non-reproducible. This
started as a ``benchmarks/`` measurement (Layer-E); it is promoted here so CI
**blocks** any regression.

**Scope is the pure layers only.** ``io/`` and ``mcp/`` are adapters / edges where
a clock read is architecturally allowed (a ``saved_at`` timestamp in session
persistence is legitimate). The doctrine is "no wall-clock in **cores**", not
"nowhere" — so this test gates the cores and leaves the edges free. (Empirically
the whole tree is clean today, but enforcing it on the adapters would forbid a
future legitimate timestamp.)
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# The pure layers whose outputs must be freezable/reproducible.
CORE_DIRS = (
    "core", "analysis", "rules", "temporal", "search",
    "representation", "theory", "context",
)

WALLCLOCK = re.compile(
    r"\b(?:time\.(?:time|perf_counter|monotonic|process_time)"
    r"|datetime\.(?:now|utcnow)|date\.today)\s*\("
)
# random.<x> that is NOT random.Random( — the module-global *unseeded* RNG.
# Seeded random.Random(seed) is reproducible and therefore freezable — allowed.
UNSEEDED_RANDOM = re.compile(
    r"\brandom\.(?!Random\b)"
    r"(?:random|choice|choices|randint|shuffle|uniform|sample|getrandbits|randrange|gauss)\b"
)


def _strip_comment(line: str) -> str:
    """Drop a trailing ``#`` comment so a mention in prose isn't a false positive."""
    hashpos = line.find("#")
    return line if hashpos == -1 else line[:hashpos]


def scan_pure_layers() -> list[tuple[str, int, str, str]]:
    """Every wall-clock / unseeded-RNG hit in the pure layers: (file, line, kind, src)."""
    findings: list[tuple[str, int, str, str]] = []
    for sub in CORE_DIRS:
        base = REPO_ROOT / "mts" / sub
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            for i, raw in enumerate(path.read_text().splitlines(), 1):
                line = _strip_comment(raw)
                rel = str(path.relative_to(REPO_ROOT))
                if WALLCLOCK.search(line):
                    findings.append((rel, i, "wall-clock read", raw.strip()))
                if UNSEEDED_RANDOM.search(line):
                    findings.append((rel, i, "unseeded RNG", raw.strip()))
    return findings


def test_pure_layers_are_freezable():
    findings = scan_pure_layers()
    assert not findings, (
        "freezability violation(s) in the pure layers — a core must not read the "
        "wall clock or use unseeded RNG (it would break frozen-artifact "
        "reproducibility; see Decisions 10/11):\n"
        + "\n".join(f"  {rel}:{ln}  [{kind}]  {src}" for rel, ln, kind, src in findings)
    )


def test_scanner_actually_catches_hazards():
    """Positive control — the patterns must have teeth, or the gate is vacuous."""
    assert WALLCLOCK.search("stamp = time.time()")
    assert WALLCLOCK.search("now = datetime.now()")
    assert WALLCLOCK.search("t = time.perf_counter()")
    assert UNSEEDED_RANDOM.search("x = random.random()")
    assert UNSEEDED_RANDOM.search("pick = random.choice(items)")


def test_seeded_rng_is_not_a_violation():
    """The nuance: seeded RNG is reproducible → freezable → allowed."""
    assert not UNSEEDED_RANDOM.search("rng = random.Random(seed)")
    assert not UNSEEDED_RANDOM.search("return random.Random(seed).random()")
    # transition.py samples with exactly that pattern — it must not trip the gate.
    assert not any("transition.py" in rel for rel, _, _, _ in scan_pure_layers())
