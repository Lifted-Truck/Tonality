"""Key induction: rank candidate keys for a body of pitch material (Phase 3.5b).

v1 is **global key only**: one ranking for the whole input (windowed/local key
tracking is a recorded extension, not this module). The method is
Krumhansl–Schmuckler-style profile correlation: the input is a 12-vector of
duration-weighted pitch-class content; each candidate ``(tonic, mode)`` scores
the Pearson correlation between that vector and the mode's profile rotated to
the tonic. Profiles are **versioned empirical priors** loaded from
``data/key_profiles.json`` — results cite the version they used, so the same
input + the same prior version always yields the same ranking (Decision 7).

This is the upstream *producer* for the ``AnalyticalContext`` seam: analysis
functions consume a context; this module is what fills one from raw material.
Per Decision 7 the result is plural — every candidate with its score, plus the
top-two margin. Relative major/minor near-ties are normal and are surfaced,
not collapsed.

Layering: this module is pure over a weights vector and imports nothing from
``temporal``. ``infer_key`` also accepts any object with a ``pc_weights()``
method (e.g. ``mts.temporal.Sequence``) by duck typing, so callers can write
``infer_key(sequence)`` without an upward import here.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence as SequenceABC
from typing import TYPE_CHECKING, Any

from ..core.scale import Scale

if TYPE_CHECKING:  # lazy at runtime: io.loaders imports analysis.builders
    from ..io.loaders import KeyProfileSet
from .analytical_context import AnalyticalContext
from .results import KeyCandidate, KeyInductionResult

# Catalog scale realizing each profile mode (the same mapping the functional
# harmony generator uses for "major"/"minor").
_MODE_SCALE_NAMES = {"major": "Ionian", "minor": "Natural Minor"}


def _pearson(x: list[float], y: list[float]) -> float:
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    dx = [a - mean_x for a in x]
    dy = [b - mean_y for b in y]
    numerator = sum(a * b for a, b in zip(dx, dy))
    denominator = math.sqrt(sum(a * a for a in dx) * sum(b * b for b in dy))
    return numerator / denominator


def infer_key(
    material: Any,
    *,
    profiles: "KeyProfileSet | None" = None,
) -> KeyInductionResult:
    """Rank all candidate keys for *material*.

    ``material`` is either a 12-vector of non-negative pitch-class weights
    (index = pc, value = salience — typically summed duration), or any object
    exposing ``pc_weights()`` returning one (e.g. a temporal ``Sequence``).

    Raises ``ValueError`` on input that carries no tonal information (empty,
    all-zero, or uniform weights) — per the cardinal rule, the engine errors
    rather than guessing.
    """

    if hasattr(material, "pc_weights"):
        weights_in = material.pc_weights()
    else:
        weights_in = material
    if isinstance(weights_in, Mapping) or not isinstance(weights_in, SequenceABC):
        raise ValueError("infer_key expects a 12-element weight sequence or an object with pc_weights().")
    weights = [float(w) for w in weights_in]
    if len(weights) != 12:
        raise ValueError(f"pc weights must have exactly 12 entries, got {len(weights)}.")
    if any(w < 0 for w in weights):
        raise ValueError("pc weights must be non-negative.")
    if max(weights) == min(weights):
        # All-zero (silence) or perfectly uniform (e.g. full chromatic, equal
        # durations): correlation is undefined and no key is better than another.
        raise ValueError("pc weights carry no tonal information (empty or uniform).")

    if profiles is None:
        from ..io.loaders import load_key_profiles

        profiles = load_key_profiles()

    candidates: list[KeyCandidate] = []
    for mode, profile in profiles.profiles.items():
        for tonic in range(12):
            rotated = [profile[(pc - tonic) % 12] for pc in range(12)]
            candidates.append(
                KeyCandidate(tonic_pc=tonic, mode=mode, score=_pearson(weights, rotated))
            )
    candidates.sort(key=lambda c: (-c.score, c.tonic_pc, c.mode))
    margin = candidates[0].score - candidates[1].score if len(candidates) > 1 else 0.0
    return KeyInductionResult(
        candidates=candidates,
        margin=margin,
        pc_weights=weights,
        profile_version=profiles.version,
    )


def candidate_context(
    candidate: KeyCandidate,
    *,
    scales: Mapping[str, Scale] | None = None,
) -> AnalyticalContext:
    """Realize a key candidate as an :class:`AnalyticalContext`.

    Maps the candidate's mode to its catalog scale (major → Ionian,
    minor → Natural Minor) so downstream key-relative analysis
    (``contextualize_chord``, disambiguation) can consume the reading.
    Run per-candidate over a ranked result to keep the plurality —
    don't collapse to ``result.best`` unless the margin warrants it.
    """

    scale_name = _MODE_SCALE_NAMES.get(candidate.mode)
    if scale_name is None:
        known = ", ".join(sorted(_MODE_SCALE_NAMES))
        raise ValueError(
            f"No catalog scale mapping for mode {candidate.mode!r} (known: {known})."
        )
    if scales is None:
        from ..io.loaders import load_scales

        scales = load_scales()
    if scale_name not in scales:
        raise ValueError(f"Scale {scale_name!r} not present in the catalog.")
    return AnalyticalContext(tonic_pc=candidate.tonic_pc, key=scales[scale_name])


__all__ = ["infer_key", "candidate_context"]
