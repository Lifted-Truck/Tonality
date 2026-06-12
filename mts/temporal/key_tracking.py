"""Local key tracking: windowed key induction over a sequence (Phase 3.5b extension).

The global ``infer_key`` answers "what key is this material in"; this module
answers "what key is it in *when*". A fixed-size window slides over the
sequence; each window's duration-weighted pc content is ranked by the same
profile-correlation method (same versioned priors), and consecutive windows
agreeing on the best key merge into :class:`KeyRegion`s — A1's key-change
split points and A6's renderable key regions.

Honesty contract: windows with no tonal information (silence, uniform
chromatic) make **no** key claim — they are recorded as uninformative
evidence and key regions merge across them (absence of evidence is not a
key change). There is no smoothing or hysteresis in v1: per-window argmax,
deterministic merge. A window over thin evidence votes its honest best —
a bare V–I span really does correlate better with the dominant key — so
short blip regions on ambiguous material are surfaced, not suppressed
(Decision 7); per-region ``mean_margin`` is the confidence signal to gate
on. If a smoothing layer ever ships, its thresholds are empirical knobs and
will ship as a versioned prior. Window geometry is the caller's (defaults
below) and is cited in the result for reproducibility.

Windows are full-size only: a truncated trailing window is a different (and
unrepresentative) evidence basis — a 2-beat tail seeing one V–I would vote
for the dominant key. The tail is still covered by the last full window;
only a sequence shorter than one window gets a single truncated window.

Boundaries: the first region starts at the first informative window's start;
the last region ends at the **sequence** end; the boundary *between* two
regions is the midpoint of the adjacent window centers — the windows'
temporal loci. All reported in beats and seconds (the dataset ``placement``
convention). Resolution is inherently the window grid; don't read boundaries
finer than ``hop_beats``.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..analysis.key_induction import infer_key
from .sequence import Sequence

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..io.loaders import KeyProfileSet

_EPS = 1e-9

DEFAULT_WINDOW_BEATS = 8.0
DEFAULT_HOP_BEATS = 2.0


@dataclass(frozen=True)
class KeyWindow:
    """One analysis window: the per-window evidence behind the regions.

    ``tonic_pc``/``mode``/``score``/``margin`` are ``None`` for an
    uninformative window (no tonal information — no claim made).
    """

    start_beats: float
    end_beats: float
    center_beats: float
    tonic_pc: int | None
    mode: str | None
    score: float | None
    margin: float | None

    @property
    def is_informative(self) -> bool:
        return self.tonic_pc is not None


@dataclass(frozen=True)
class KeyRegion:
    """A maximal span over which the per-window best key is constant."""

    start_beats: float
    end_beats: float
    start_seconds: float
    end_seconds: float
    tonic_pc: int
    mode: str
    mean_score: float
    mean_margin: float
    window_count: int

    @property
    def duration_beats(self) -> float:
        return self.end_beats - self.start_beats


@dataclass(frozen=True)
class KeyTrackingResult:
    """Key regions plus the per-window evidence and the cited parameters."""

    regions: list[KeyRegion]
    windows: list[KeyWindow]
    window_beats: float
    hop_beats: float
    profile_version: str

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def track_keys(
    sequence: Sequence,
    *,
    window_beats: float = DEFAULT_WINDOW_BEATS,
    hop_beats: float = DEFAULT_HOP_BEATS,
    profiles: "KeyProfileSet | None" = None,
) -> KeyTrackingResult:
    """Track the local key of *sequence* through time.

    Slides a ``window_beats`` window by ``hop_beats``, ranks each window with
    the global key-induction method (same versioned profiles), and merges
    consecutive same-best-key windows into regions. Raises ``ValueError`` on
    an empty sequence, non-positive window/hop, or when **no** window carries
    tonal information — the engine reports nothing rather than guessing.
    """

    if window_beats <= _EPS:
        raise ValueError("window_beats must be positive.")
    if hop_beats <= _EPS:
        raise ValueError("hop_beats must be positive.")
    if not sequence.events:
        raise ValueError("track_keys needs a sequence with events.")

    if profiles is None:
        from ..io.loaders import load_key_profiles

        profiles = load_key_profiles()

    duration = sequence.duration_beats
    starts = []
    start = 0.0
    while start + window_beats <= duration + _EPS:
        starts.append(start)
        start += hop_beats
    if not starts:  # sequence shorter than one window: a single truncated one
        starts = [0.0]

    windows: list[KeyWindow] = []
    for start in starts:
        end = min(start + window_beats, duration)
        weights = sequence.pc_weights(start, end)
        try:
            ranking = infer_key(weights, profiles=profiles)
        except ValueError:
            windows.append(
                KeyWindow(start, end, (start + end) / 2.0, None, None, None, None)
            )
        else:
            best = ranking.candidates[0]
            windows.append(
                KeyWindow(
                    start_beats=start,
                    end_beats=end,
                    center_beats=(start + end) / 2.0,
                    tonic_pc=best.tonic_pc,
                    mode=best.mode,
                    score=best.score,
                    margin=ranking.margin,
                )
            )

    informative = [w for w in windows if w.is_informative]
    if not informative:
        raise ValueError(
            "No window carries tonal information (all silence or uniform content)."
        )

    # Group consecutive informative windows by best key; uninformative windows
    # between same-key groups do not split them (no evidence != a key change).
    groups: list[list[KeyWindow]] = []
    for window in informative:
        if groups and (groups[-1][0].tonic_pc, groups[-1][0].mode) == (
            window.tonic_pc,
            window.mode,
        ):
            groups[-1].append(window)
        else:
            groups.append([window])

    regions: list[KeyRegion] = []
    for index, group in enumerate(groups):
        if index == 0:
            start_beats = group[0].start_beats
        else:
            start_beats = (groups[index - 1][-1].center_beats + group[0].center_beats) / 2.0
        if index == len(groups) - 1:
            end_beats = duration  # full-size windows leave no claimed tail
        else:
            end_beats = (group[-1].center_beats + groups[index + 1][0].center_beats) / 2.0
        regions.append(
            KeyRegion(
                start_beats=start_beats,
                end_beats=end_beats,
                start_seconds=sequence.seconds_at(start_beats),
                end_seconds=sequence.seconds_at(end_beats),
                tonic_pc=group[0].tonic_pc,
                mode=group[0].mode,
                mean_score=sum(w.score for w in group) / len(group),
                mean_margin=sum(w.margin for w in group) / len(group),
                window_count=len(group),
            )
        )

    return KeyTrackingResult(
        regions=regions,
        windows=windows,
        window_beats=window_beats,
        hop_beats=hop_beats,
        profile_version=profiles.version,
    )


__all__ = [
    "DEFAULT_HOP_BEATS",
    "DEFAULT_WINDOW_BEATS",
    "KeyRegion",
    "KeyTrackingResult",
    "KeyWindow",
    "track_keys",
]
