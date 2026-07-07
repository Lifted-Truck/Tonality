"""Meter estimation: infer the time signature from note content (gap 11).

The time system is declarative — ``MeterMap`` answers every bar/downbeat
question exactly, but only from file metadata, so a loop tagged with a default
4/4 silently poisons every downstream metric judgment (``analyze_rhythm``
placement, syncopation, swing, groove). This is the inference the engine was
missing: rank candidate time signatures by how well the onset/accent content
fits each meter, and **evidence against the file's declared meter without ever
overriding it**.

The method is ``infer_key`` for meter — a two-stage metric fit per candidate:

- **bar-period autocorrelation** — does the onset-salience signal repeat every
  ``beats_per_bar``? (kills the aliasing where a 3-beat pattern spuriously folds
  onto a non-dividing 4.5-beat bar); and
- **metric-profile correlation** — does the within-bar accent distribution match
  the meter's metric-grid template? (distinguishes 3/4 from 6/8, which share a
  3-beat bar but differ in grouping).

``score = period_score × max(profile_score, 0)``. Templates are versioned
empirical priors (``data/meter_profiles.json``); both sub-scores ride along as
evidence (Decision 7). Honest bound: onset density alone, with no differential
accent, leaves meter genuinely ambiguous — surfaced as a small ``margin``, and
all-flat input raises rather than guesses.

Slice 1 is **global** (whole-sequence), **phase 0** (bar lines from the sequence
start, as ``MeterMap`` assumes). The opt-in ``phase_search`` now also surfaces the
winning bar phase as ``downbeat_offset_beats`` (anacrusis / global-phase estimate).
Deferred: change-point / local meter is delivered (``mts/temporal/meter_tracking``);
still open are agogic (duration) weighting and the online form (gap 5).
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..temporal import Sequence
from .errors import InsufficientInformation
from .results import MeterCandidate, MeterEstimationResult
from ..io.loaders import MeterProfileSet, load_meter_profiles

_EPS = 1e-9
_MIN_ONSETS = 6  # below this there is too little evidence for the autocorrelation


def _pearson(x: list[float], y: list[float]) -> float:
    n = len(x)
    mean_x, mean_y = sum(x) / n, sum(y) / n
    dx = [a - mean_x for a in x]
    dy = [b - mean_y for b in y]
    denom = math.sqrt(sum(a * a for a in dx) * sum(b * b for b in dy))
    return sum(a * b for a, b in zip(dx, dy)) / denom if denom > _EPS else 0.0


def _autocorrelation(signal: list[float], lag: int) -> float:
    """Normalised autocorrelation of the salience signal at an integer grid lag."""

    if lag <= 0 or lag >= len(signal):
        return 0.0
    a, b = signal[:-lag], signal[lag:]
    denom = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b)) / denom if denom > _EPS else 0.0


def infer_meter(
    sequence: "Sequence",
    *,
    profiles: "MeterProfileSet | None" = None,
    phase_search: bool = False,
) -> MeterEstimationResult:
    """Rank candidate time signatures for *sequence* by metric fit.

    Reads onset positions (quarter-note beats) and accents (each event's
    ``pitch.velocity`` if any event carries one, else unit weight) from the
    sequence; compares the top estimate to the declared meter
    (``sequence.meter``) without mutating it. Raises ``ValueError`` on too few
    onsets or content with no metric information (uniform / flat) — the engine
    evidences, it does not guess.

    ``phase_search`` (opt-in, off by default): score each candidate's metric
    profile at its **best bar phase** rather than assuming bar lines start at beat
    0. The period autocorrelation is already phase-invariant; this aligns the
    *profile* fold too, so material whose downbeat is not at beat 0 (an
    anacrusis, or a window that does not begin on a bar line — the local-meter
    tracker's case) is read correctly. The winning bar phase of the top candidate
    is surfaced as ``downbeat_offset_beats`` (the anacrusis / global-phase
    estimate); it is ``None`` when ``phase_search`` is off. Default off keeps the
    phase-0 global contract (and its golden) exactly — only the new field appears,
    defaulting to ``None``.
    """

    if profiles is None:

        profiles = load_meter_profiles()
    grid = profiles.grid_beats

    events = sequence.events
    if len(events) < _MIN_ONSETS:
        raise InsufficientInformation(
            f"meter estimation needs at least {_MIN_ONSETS} onsets, got {len(events)}."
        )
    has_velocity = any(e.pitch.velocity is not None for e in events)
    weighted = [
        (e.onset, float(e.pitch.velocity) if (has_velocity and e.pitch.velocity is not None) else 1.0)
        for e in events
    ]

    total_beats = max(o for o, _ in weighted)
    n_slots = round(total_beats / grid) + 1
    signal = [0.0] * n_slots
    for onset, weight in weighted:
        idx = round(onset / grid)
        if 0 <= idx < n_slots:
            signal[idx] += weight
    if max(signal) - min(signal) <= _EPS:
        raise InsufficientInformation("onset content carries no metric information (uniform signal).")

    # Each entry pairs a candidate with the bar phase (in beats) that best aligned
    # its profile fold — the winning downbeat offset, surfaced for the top candidate.
    scored_candidates: list[tuple[MeterCandidate, float]] = []
    for sig, template in profiles.profiles.items():
        num_s, den_s = sig.split("/")
        numerator, denominator = int(num_s), int(den_s)
        bar_beats = numerator * (4.0 / denominator)
        bar_slots = round(bar_beats / grid)
        if bar_slots != len(template):  # prior self-consistency
            raise ValueError(f"Meter profile {sig!r} length {len(template)} != bar slots {bar_slots}.")

        folded = [0.0] * bar_slots
        for onset, weight in weighted:
            folded[round((onset % bar_beats) / grid) % bar_slots] += weight
        period = _autocorrelation(signal, bar_slots)
        best_phase = 0  # grid-slot rotation; phase-0 unless phase_search picks another
        if phase_search:
            # Best alignment of the fold to the template over all bar phases — a
            # rotation of the folded histogram (the period stays phase-invariant).
            # The winning rotation ``p`` places the template's slot-0 (the
            # downbeat) at the fold's slot ``p`` → the downbeat sits ``p`` grid
            # slots into the bar. Ties resolve to the lowest phase (determinism).
            tmpl = list(template)
            profile, best_phase = max(
                ((_pearson(folded[p:] + folded[:p], tmpl), p) for p in range(bar_slots)),
                key=lambda sp: (sp[0], -sp[1]),
            )
        else:
            profile = _pearson(folded, list(template))
        score = period * max(profile, 0.0)
        scored_candidates.append((
            MeterCandidate(
                numerator=numerator, denominator=denominator,
                score=round(score, 6), period_score=round(period, 6),
                profile_score=round(profile, 6),
            ),
            best_phase * grid,  # winning bar phase in beats (the downbeat offset)
        ))

    scored_candidates.sort(key=lambda cp: (-cp[0].score, cp[0].numerator, cp[0].denominator))
    candidates = [c for c, _ in scored_candidates]
    margin = candidates[0].score - candidates[1].score if len(candidates) > 1 else 0.0
    # Only meaningful when phase_search aligned the fold; phase-0 path reports None
    # so the default contract (and its golden) carries no offset claim.
    downbeat_offset = round(scored_candidates[0][1], 6) if phase_search else None

    declared_sig = sequence.meter.changes[0].signature if sequence.meter.changes else None
    declared_num = declared_sig.numerator if declared_sig else None
    declared_den = declared_sig.denominator if declared_sig else None
    best = candidates[0]
    agrees = declared_sig is not None and (best.numerator, best.denominator) == (declared_num, declared_den)

    return MeterEstimationResult(
        candidates=candidates,
        margin=round(margin, 6),
        declared_numerator=declared_num,
        declared_denominator=declared_den,
        agrees_with_declared=agrees,
        grid_beats=grid,
        profile_version=profiles.version,
        downbeat_offset_beats=downbeat_offset,
    )


__all__ = ["infer_meter"]
