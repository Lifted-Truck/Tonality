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

The candidate space is the loaded profile set's modes — **major and minor
only under ``kk-1982.1``** (theory-grounding review pass #1, accepted
limitation): modal material ranks as its relative major/minor, not its modal
tonic. The extension is nearly data-only — add modal rows to
``key_profiles.json`` and entries to ``_MODE_SCALE_NAMES`` below.

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
from .results import (
    KeyCandidate,
    KeyInductionResult,
    RelativeKeyDisambiguation,
    RelativeKeyEvidence,
)

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


def _find(candidates: list[KeyCandidate], tonic_pc: int, mode: str) -> KeyCandidate:
    for candidate in candidates:
        if candidate.tonic_pc == tonic_pc and candidate.mode == mode:
            return candidate
    raise ValueError(f"No candidate for ({tonic_pc}, {mode}) — corrupt induction.")


def disambiguate_relative_key(
    material: Any,
    *,
    profiles: "KeyProfileSet | None" = None,
    weights: Any = None,
) -> RelativeKeyDisambiguation:
    """Break a relative-major/minor near-tie with tonal-hierarchy signals (3.5a).

    Relative pairs (e.g. C major / A minor) share a diatonic collection, so the
    KK-profile correlation in :func:`infer_key` separates them weakly — the very
    confusion Audiology's brief-3 surfaced. This is the **additive** refinement:
    :func:`infer_key` is left untouched (its scores/margin are a pinned stability
    contract for A5/A7) and carried here as ``induction``; the tie-break runs on
    top, evidenced and reproducible.

    ``material`` is the usual :func:`infer_key` input (a 12-vector or an object
    with ``pc_weights()``) **or** an already-computed :class:`KeyInductionResult`.
    When the top candidate and its relative partner are not within the prior's
    ``near_tie_margin`` the result is a passthrough (``applied=False``).
    """

    if isinstance(material, KeyInductionResult):
        induction = material
    else:
        induction = infer_key(material, profiles=profiles)

    if weights is None:
        from ..io.loaders import load_relative_key_weights

        weights = load_relative_key_weights()

    w = induction.pc_weights
    top = induction.best

    # The relative partner: major M ↔ minor M+9 (i.e. minor m ↔ major m+3).
    if top.mode == "major":
        major = top
        minor = _find(induction.candidates, (top.tonic_pc + 9) % 12, "minor")
    else:
        minor = top
        major = _find(induction.candidates, (top.tonic_pc + 3) % 12, "major")
    partner = minor if top is major else major

    if top.score - partner.score > weights.near_tie_margin:
        return RelativeKeyDisambiguation(
            applied=False,
            chosen=None,
            relative=None,
            is_ambiguous=False,
            tiebreak_score=0.0,
            evidence=[],
            induction=induction,
            weights_version=weights.version,
        )

    M, m = major.tonic_pc, minor.tonic_pc
    total = sum(w) or 1.0

    def _triad(root: int, third: int) -> float:
        return w[root] + w[(root + third) % 12] + w[(root + 7) % 12]

    signals = {
        "tonic_salience": (w[m] - w[M]) / total,
        "tonic_triad_salience": (_triad(m, 3) - _triad(M, 4)) / total,
        "leading_tone": w[(m + 11) % 12] / total,
    }
    details = {
        "tonic_salience": "minor-tonic vs major-tonic weight",
        "tonic_triad_salience": "minor-triad vs major-triad weight",
        "leading_tone": "raised 7th of the minor (outside the shared collection)",
    }
    evidence = [
        RelativeKeyEvidence(
            signal=name,
            value=round(value, 6),
            weight=weights.weights.get(name, 0.0),
            detail=details[name],
        )
        for name, value in signals.items()
    ]
    score = sum(weights.weights.get(name, 0.0) * value for name, value in signals.items())

    if score > weights.decision_margin:
        chosen, relative, ambiguous = minor, major, False
    elif score < -weights.decision_margin:
        chosen, relative, ambiguous = major, minor, False
    else:
        # Tie-break inconclusive: keep the correlation winner, flag it honestly.
        chosen, relative, ambiguous = top, partner, True

    return RelativeKeyDisambiguation(
        applied=True,
        chosen=chosen,
        relative=relative,
        is_ambiguous=ambiguous,
        tiebreak_score=round(score, 6),
        evidence=evidence,
        induction=induction,
        weights_version=weights.version,
    )


__all__ = ["infer_key", "candidate_context", "disambiguate_relative_key"]
