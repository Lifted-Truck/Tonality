"""Stated resource bounds for caller-sized work (security slice, 2026-10-08).

Several analyses build a grid whose size the CALLER controls — windows over a
span, bars × subdivisions, groove slots — and some callers are untrusted: a
prompt-injected model chooses MCP tool arguments, and the HTTP bridge serves any
local process. Before these bounds, one small argument (a duration of ``1e9``,
``1e999`` which valid JSON parses to infinity, or ``subdivisions=10**7``) made
the engine allocate over 1.2 GB per second until the OS killed it, through the
stdio MCP server, the bridge, and direct import alike (measured; see
``docs/security/BOUNDARIES.md``).

Two bounds, both deliberately far above any real piece and far below harm:

- ``MAX_SPAN_BEATS`` — the longest sequence the engine accepts. The longest
  fixture in the repo (a full Schubert song) spans 273 beats; a four-hour piece
  at 240 bpm is 57,600. Measured cost at 100,000 beats: ~44 MB, ~0.2 s.
- ``MAX_GRID_CELLS`` — the most cells any single grid may have. The span bound
  alone is not enough: a tiny ``hop_beats`` or a huge ``subdivisions`` grows the
  grid without moving the span. 100,000 covers a four-hour piece at four chords
  per bar with headroom.

These are POLICY values, like the inertia λ of Decision 14: stated, cited in the
error, and changed by review — never discovered, never silently clamped. An
over-budget request raises ``ValueError`` naming the knob, so a caller that hits
one learns exactly which argument to change. Deliberately free of imports so
every layer, including ``analysis/`` below ``temporal/``, can use it.
"""

from __future__ import annotations

import math

MAX_SPAN_BEATS = 100_000
MAX_GRID_CELLS = 100_000


def require_finite(value: float, what: str) -> None:
    """Reject NaN and ±infinity. Ordinary comparisons do NOT catch NaN — every
    comparison with it is False, so ``nan < 0`` and ``nan <= 0`` both pass a
    range check — which is how NaN onsets reached the engine before this."""

    if not math.isfinite(value):
        raise ValueError(f"{what} must be a finite number, got {value!r}.")


def require_grid(cells: float, what: str, knob: str) -> None:
    """Refuse to build a grid larger than ``MAX_GRID_CELLS``. Call it BEFORE
    allocating — the point is that the expensive thing never starts."""

    if not math.isfinite(cells) or cells > MAX_GRID_CELLS:
        raise ValueError(
            f"{what} would need {cells:,.0f} cells, over the engine's limit of "
            f"{MAX_GRID_CELLS:,} (mts.limits.MAX_GRID_CELLS). Reduce {knob}."
        )


__all__ = ["MAX_GRID_CELLS", "MAX_SPAN_BEATS", "require_finite", "require_grid"]
