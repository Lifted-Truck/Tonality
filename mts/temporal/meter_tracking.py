"""Local meter tracking: windowed meter estimation over a sequence (gap 11 follow-on).

The global :func:`mts.analysis.meter_estimation.infer_meter` answers "what meter is
this material in"; this module answers "what meter is it in *when*". A fixed-size
window slides over the sequence; each window's onset/accent content is ranked by the
same metric-fit method (the same versioned ``meter-grid`` priors), and consecutive
windows agreeing on the best time signature merge into :class:`MeterRegion`s — the
change-point / local-meter form deferred from the global slice, exactly as local key
tracking (:func:`mts.temporal.track_keys`) was the windowed form of ``infer_key``.

Honesty contract (the same one ``track_keys`` keeps): a window with too few onsets or
no differential accent makes **no** meter claim — it is recorded as uninformative
evidence and regions merge across it (absence of evidence is not a meter change).
Raw per-window argmax, deterministic merge; **no smoothing/hysteresis in v1** (meter
is already a slow-changing signal — if a smoothing layer is ever needed its
thresholds ship as a versioned prior, as on the key side). Per-region ``mean_margin``
is the confidence signal to gate on.

Windows are **phase 0** (bar lines from each window's start, as the global estimator
assumes — anacrusis/phase estimation stays deferred) and **full-size** (a truncated
trailing window is an unrepresentative metric basis; the tail is covered by the last
full window — only a sequence shorter than one window gets a single truncated one).
Because meter detection needs several bars of period evidence, the default window is
larger than key tracking's. Window geometry is the caller's (defaults below) and is
cited in the result; don't read boundaries finer than ``hop_beats``.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..analysis.meter_estimation import infer_meter
from .sequence import Event, Sequence

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..io.loaders import MeterProfileSet

_EPS = 1e-9

# Meter changes slowly and its period needs several bars of evidence, so the window
# defaults run larger/coarser than key tracking's.
DEFAULT_WINDOW_BEATS = 16.0
DEFAULT_HOP_BEATS = 4.0


@dataclass(frozen=True)
class MeterWindow:
    """One analysis window: the per-window evidence behind the regions.

    ``numerator``/``denominator``/``score``/``margin`` are ``None`` for an
    uninformative window (too few onsets or no differential accent — no claim).
    """

    start_beats: float
    end_beats: float
    center_beats: float
    numerator: int | None
    denominator: int | None
    score: float | None
    margin: float | None

    @property
    def is_informative(self) -> bool:
        return self.numerator is not None


@dataclass(frozen=True)
class MeterRegion:
    """A maximal span over which the per-window best time signature is constant."""

    start_beats: float
    end_beats: float
    start_seconds: float
    end_seconds: float
    numerator: int
    denominator: int
    mean_score: float
    mean_margin: float
    window_count: int

    @property
    def duration_beats(self) -> float:
        return self.end_beats - self.start_beats


@dataclass(frozen=True)
class MeterTrackingResult:
    """Meter regions plus the per-window evidence and the cited parameters."""

    regions: list[MeterRegion]
    windows: list[MeterWindow]
    window_beats: float
    hop_beats: float
    profile_version: str

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def _window_subsequence(sequence: Sequence, start: float, end: float) -> Sequence:
    """The events in ``[start, end)`` re-based to window phase 0.

    Onsets shift by ``-start`` (so the window starts on a notional downbeat, the
    phase-0 assumption the global estimator makes); pitch/velocity/duration are
    preserved so the accent weighting is intact. Tempo/meter default — only the
    inferred candidate is read from this sub-sequence; region seconds come from the
    original sequence's tempo map.
    """

    windowed = [
        dataclasses.replace(e, onset=e.onset - start)
        for e in sequence.events
        if start - _EPS <= e.onset < end - _EPS
    ]
    return Sequence.from_events(windowed)


def track_meter(
    sequence: Sequence,
    *,
    window_beats: float = DEFAULT_WINDOW_BEATS,
    hop_beats: float = DEFAULT_HOP_BEATS,
    profiles: "MeterProfileSet | None" = None,
) -> MeterTrackingResult:
    """Track the local time signature of *sequence* through time.

    Slides a ``window_beats`` window by ``hop_beats``, ranks each window with the
    global meter-estimation method (the same versioned profiles), and merges
    consecutive same-best-meter windows into regions. Raises ``ValueError`` on an
    empty sequence, non-positive window/hop, or when **no** window carries metric
    information (too sparse / uniform throughout) — the engine reports nothing
    rather than guessing. A window that individually lacks evidence is simply
    uninformative; regions merge across it.
    """

    if window_beats <= _EPS:
        raise ValueError("window_beats must be positive.")
    if hop_beats <= _EPS:
        raise ValueError("hop_beats must be positive.")
    if not sequence.events:
        raise ValueError("track_meter needs a sequence with events.")

    if profiles is None:
        from ..io.loaders import load_meter_profiles

        profiles = load_meter_profiles()

    duration = sequence.duration_beats
    starts: list[float] = []
    start = 0.0
    while start + window_beats <= duration + _EPS:
        starts.append(start)
        start += hop_beats
    if not starts:  # shorter than one window: a single truncated one
        starts = [0.0]

    windows: list[MeterWindow] = []
    for start in starts:
        end = min(start + window_beats, duration)
        try:
            ranking = infer_meter(
                _window_subsequence(sequence, start, end), profiles=profiles, phase_search=True
            )
        except ValueError:
            windows.append(MeterWindow(start, end, (start + end) / 2.0, None, None, None, None))
        else:
            best = ranking.candidates[0]
            windows.append(
                MeterWindow(
                    start_beats=start,
                    end_beats=end,
                    center_beats=(start + end) / 2.0,
                    numerator=best.numerator,
                    denominator=best.denominator,
                    score=best.score,
                    margin=ranking.margin,
                )
            )

    informative = [w for w in windows if w.is_informative]
    if not informative:
        raise ValueError(
            "No window carries metric information (too sparse or uniform throughout)."
        )

    # Group consecutive informative windows by best (numerator, denominator);
    # uninformative windows between same-meter groups do not split them.
    labels = [(w.numerator, w.denominator) for w in informative]
    groups: list[tuple[tuple[int, int], list[MeterWindow]]] = []
    for window, label in zip(informative, labels):
        if groups and groups[-1][0] == label:
            groups[-1][1].append(window)
        else:
            groups.append((label, [window]))

    regions: list[MeterRegion] = []
    for index, (label, group) in enumerate(groups):
        if index == 0:
            start_beats = group[0].start_beats
        else:
            start_beats = (groups[index - 1][1][-1].center_beats + group[0].center_beats) / 2.0
        if index == len(groups) - 1:
            end_beats = duration  # full-size windows leave no claimed tail
        else:
            end_beats = (group[-1].center_beats + groups[index + 1][1][0].center_beats) / 2.0
        scores = [w.score for w in group]
        margins = [w.margin for w in group]
        regions.append(
            MeterRegion(
                start_beats=start_beats,
                end_beats=end_beats,
                start_seconds=sequence.seconds_at(start_beats),
                end_seconds=sequence.seconds_at(end_beats),
                numerator=label[0],
                denominator=label[1],
                mean_score=round(sum(scores) / len(scores), 6),
                mean_margin=round(sum(margins) / len(margins), 6),
                window_count=len(group),
            )
        )

    return MeterTrackingResult(
        regions=regions,
        windows=windows,
        window_beats=window_beats,
        hop_beats=hop_beats,
        profile_version=profiles.version,
    )


__all__ = [
    "MeterWindow",
    "MeterRegion",
    "MeterTrackingResult",
    "track_meter",
    "DEFAULT_WINDOW_BEATS",
    "DEFAULT_HOP_BEATS",
]
