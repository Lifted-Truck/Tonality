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

from ..analysis.key_induction import disambiguate_relative_key, infer_key
from .sequence import Sequence

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..io.loaders import KeyProfileSet, KeySmoothingPriors

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
    disambiguate_relative: bool = False
    smoothing_version: str | None = None
    inertia_version: str | None = None

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def _smooth_labels(
    informative: list[KeyWindow],
    labels: list[tuple[int, str]],
    priors: "KeySmoothingPriors",
) -> list[tuple[int, str]]:
    """Absorb short, low-confidence key-region blips into their stronger neighbour.

    Iteratively: build runs of consecutive equal labels; a run shorter than
    ``min_region_windows`` whose mean per-window margin is below
    ``min_region_margin`` is a blip. Relabel the weakest blip (shortest, then
    leftmost) to its longer adjacent neighbour's label (ties → preceding), then
    re-coalesce; repeat until none remain. Each step strictly reduces the run
    count, so it terminates. The margin override keeps confident brief
    modulations.
    """

    labels = list(labels)
    while True:
        runs: list[list] = []  # [label, start_idx, end_idx, count]
        for i, label in enumerate(labels):
            if runs and runs[-1][0] == label:
                runs[-1][2] = i
                runs[-1][3] += 1
            else:
                runs.append([label, i, i, 1])
        if len(runs) <= 1:
            break

        blips = []
        for ri, (label, start, end, count) in enumerate(runs):
            mean_margin = sum(informative[k].margin for k in range(start, end + 1)) / count
            if count < priors.min_region_windows and mean_margin < priors.min_region_margin:
                blips.append((count, start, ri))
        if not blips:
            break

        blips.sort()  # shortest, then leftmost — deterministic
        _, _, ri = blips[0]
        label, start, end, count = runs[ri]
        left = runs[ri - 1] if ri > 0 else None
        right = runs[ri + 1] if ri + 1 < len(runs) else None
        if left and right:
            target = left[0] if left[3] >= right[3] else right[0]
        else:
            target = (left or right)[0]
        for k in range(start, end + 1):
            labels[k] = target
    return labels


def _key_inertia_path(
    score_vectors: list[dict[tuple[int, str], float]], switch_penalty: float
) -> list[tuple[int, str]]:
    """Deterministic key-inertia Viterbi (A6 brief-13): the max-score
    ``(tonic, mode)`` path over per-window correlation emissions with a flat
    one-time ``switch_penalty`` on any state change. Rewards fit, penalizes
    switching, lets a sustained well-fit key win (the penalty is paid once; a real
    modulation accrues emission advantage over many windows). Ties break to the
    lexicographically-lowest state so the path is reproducible.
    """

    states = sorted(score_vectors[0])  # all (tonic, mode), deterministic order
    dp: dict[tuple[int, str], float] = dict(score_vectors[0])
    back: list[dict[tuple[int, str], tuple[int, str]]] = [{}]
    for emis in score_vectors[1:]:
        prev = dp
        cur: dict[tuple[int, str], float] = {}
        bk: dict[tuple[int, str], tuple[int, str]] = {}
        for s in states:
            best_sp = states[0]
            best_val: float | None = None
            for sp in states:  # sorted → strict-> keeps the lowest state on ties
                v = prev[sp] + (0.0 if sp == s else -switch_penalty)
                if best_val is None or v > best_val:
                    best_val, best_sp = v, sp
            cur[s] = emis[s] + best_val
            bk[s] = best_sp
        dp = cur
        back.append(bk)
    last = max(states, key=lambda s: dp[s])  # first maximal (lowest) on ties
    path = [last]
    for bk in reversed(back[1:]):
        path.append(bk[path[-1]])
    return list(reversed(path))


def track_keys(
    sequence: Sequence,
    *,
    window_beats: float = DEFAULT_WINDOW_BEATS,
    hop_beats: float = DEFAULT_HOP_BEATS,
    profiles: "KeyProfileSet | None" = None,
    disambiguate_relative: bool = False,
    smoothing: bool = False,
    key_inertia: bool = False,
) -> KeyTrackingResult:
    """Track the local key of *sequence* through time.

    Slides a ``window_beats`` window by ``hop_beats``, ranks each window with
    the global key-induction method (same versioned profiles), and merges
    consecutive same-best-key windows into regions. Raises ``ValueError`` on
    an empty sequence, non-positive window/hop, or when **no** window carries
    tonal information — the engine reports nothing rather than guessing.

    ``disambiguate_relative`` (opt-in, off by default — the
    :func:`~mts.analysis.key_induction.disambiguate_relative_key` refinement
    applied per window): on a relative-major/minor near-tie the window adopts the
    tonal-hierarchy reading instead of the bare correlation argmax (only when the
    tie-break is decisive — passthrough/ambiguous windows are untouched). Better
    relative-key sections in the rendered timeline; cited on the result.

    ``smoothing`` (opt-in, off by default — versioned hysteresis): a key region
    shorter than the prior's ``min_region_windows`` whose ``mean_margin`` is
    below ``min_region_margin`` is a low-confidence **blip** and is absorbed into
    its stronger neighbour (a short region with a strong margin — a confident
    brief modulation — is kept). Unlike ``disambiguate_relative`` this is a
    *region-level* decision: the per-window ``windows`` keep their raw argmax as
    evidence; only the region grouping is smoothed. Cited via
    ``smoothing_version`` on the result. Removes the residual micro-band noise on
    real performances (Audiology brief-3, Finding C).

    ``key_inertia`` (opt-in, off by default — a continuity prior; A6 brief-13): a
    deterministic Viterbi over the per-window candidate scores with a flat
    ``switch_penalty`` (versioned prior ``key-inertia.1``, cited via
    ``inertia_version``) re-decodes the per-window ``(tonic, mode)`` path —
    rewarding fit, penalizing switching, letting a sustained well-fit key win. Holds
    near-tie mode flips on sparse content to their context (the maintainer's
    parsimony-plus-continuity principle), substantially reducing over-segmentation.
    Composes with ``smoothing`` (inertia first, then region hysteresis) and largely
    subsumes it. Operates on the windowed track only — ``infer_key`` is untouched.

    ``key_inertia`` does **not** compose with ``disambiguate_relative`` (RE-3c):
    the inertia path re-decodes from the raw per-window score vectors, so the
    per-window tie-break could never reach it — the combination used to be
    accepted and the tie-break silently discarded. It now raises: continuity is
    itself a tie-breaking policy for relative-key near-ties; choose one.
    """

    if window_beats <= _EPS:
        raise ValueError("window_beats must be positive.")
    if hop_beats <= _EPS:
        raise ValueError("hop_beats must be positive.")
    if not sequence.events:
        raise ValueError("track_keys needs a sequence with events.")
    if key_inertia and disambiguate_relative:
        raise ValueError(
            "key_inertia does not compose with disambiguate_relative: the "
            "inertia path re-decodes from raw score vectors, so the per-window "
            "relative-key tie-break cannot reach it (it used to be silently "
            "discarded). Continuity is itself a tie-breaking policy — choose one."
        )

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
    # Per-window full candidate scores (the emission vectors the key-inertia path
    # consumes); None for an uninformative window. Kept parallel to `windows`.
    score_vectors: list[dict[tuple[int, str], float] | None] = []
    for start in starts:
        end = min(start + window_beats, duration)
        weights = sequence.pc_weights(start, end)
        try:
            ranking = infer_key(weights, profiles=profiles)
        except ValueError:
            windows.append(
                KeyWindow(start, end, (start + end) / 2.0, None, None, None, None)
            )
            score_vectors.append(None)
        else:
            best = ranking.candidates[0]
            if disambiguate_relative:
                tiebreak = disambiguate_relative_key(ranking, profiles=profiles)
                if tiebreak.applied and not tiebreak.is_ambiguous:
                    best = tiebreak.chosen  # the tonal-hierarchy reading
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
            score_vectors.append({(c.tonic_pc, c.mode): c.score for c in ranking.candidates})

    informative = [w for w in windows if w.is_informative]
    info_scores = [sv for sv in score_vectors if sv is not None]
    if not informative:
        raise ValueError(
            "No window carries tonal information (all silence or uniform content)."
        )

    # Per-window labels — raw argmax by default. Two opt-in refinements compose
    # (the windows keep their raw labels as evidence; only the grouping changes):
    # `key_inertia` re-decodes the per-window path with a continuity prior (a
    # transition penalty over the full score vectors — A6 brief-13), then
    # `smoothing` applies region-level hysteresis on top.
    labels = [(w.tonic_pc, w.mode) for w in informative]
    inertia_version: str | None = None
    if key_inertia:
        from ..io.loaders import load_key_inertia

        inertia = load_key_inertia()
        labels = _key_inertia_path(info_scores, inertia.switch_penalty)
        inertia_version = inertia.version
    smoothing_version: str | None = None
    if smoothing:
        from ..io.loaders import load_key_smoothing

        priors = load_key_smoothing()
        labels = _smooth_labels(informative, labels, priors)
        smoothing_version = priors.version

    # Group consecutive informative windows by (possibly smoothed) label;
    # uninformative windows between same-key groups do not split them.
    groups: list[tuple[tuple[int, str], list[KeyWindow], list[dict]]] = []
    for window, scores, label in zip(informative, info_scores, labels):
        if groups and groups[-1][0] == label:
            groups[-1][1].append(window)
            groups[-1][2].append(scores)
        else:
            groups.append((label, [window], [scores]))

    regions: list[KeyRegion] = []
    for index, (label, group, group_scores) in enumerate(groups):
        if index == 0:
            start_beats = group[0].start_beats
        else:
            start_beats = (groups[index - 1][1][-1].center_beats + group[0].center_beats) / 2.0
        if index == len(groups) - 1:
            end_beats = duration  # full-size windows leave no claimed tail
        else:
            end_beats = (group[-1].center_beats + groups[index + 1][1][0].center_beats) / 2.0
        # Region stats are measured against the region's OWN label (RE-3c):
        # each window contributes its score *for that key* and its margin of
        # that key over the best other candidate. For a raw-argmax region this
        # is exactly the old top-score / top-two-margin; for a window that
        # inertia/smoothing relabeled, the margin goes negative — the
        # advertised gating signal now describes the key the region claims,
        # not the raw argmax the relabeling overrode.
        label_scores = [scores[label] for scores in group_scores]
        label_margins = [
            scores[label] - max(v for state, v in scores.items() if state != label)
            for scores in group_scores
        ]
        regions.append(
            KeyRegion(
                start_beats=start_beats,
                end_beats=end_beats,
                start_seconds=sequence.seconds_at(start_beats),
                end_seconds=sequence.seconds_at(end_beats),
                tonic_pc=label[0],
                mode=label[1],
                mean_score=sum(label_scores) / len(group),
                mean_margin=sum(label_margins) / len(group),
                window_count=len(group),
            )
        )

    return KeyTrackingResult(
        regions=regions,
        windows=windows,
        window_beats=window_beats,
        hop_beats=hop_beats,
        profile_version=profiles.version,
        smoothing_version=smoothing_version,
        inertia_version=inertia_version,
        disambiguate_relative=disambiguate_relative,
    )


__all__ = [
    "DEFAULT_HOP_BEATS",
    "DEFAULT_WINDOW_BEATS",
    "KeyRegion",
    "KeyTrackingResult",
    "KeyWindow",
    "track_keys",
]
