"""Structural key-area reduction: tonicization vs modulation (gap — A6 brief-5).

``track_keys`` is a **windowed local-fit** signal: each window reports the key
its content best correlates with, so a brief **tonicization** (a V/V span) reads
as the *dominant's key*. Human analysts notate those as Roman numerals *within
the parent key*. So the windowed track is a different object than **structural
key-areas**. This reduces the local track to that structural timeline —
distinguishing a **tonicization** (brief, diatonically-related excursion —
absorbed into the parent) from a **modulation** (a sustained/structural key
change — kept).

The lever ``smooth_key_regions`` lacked is **functional context**: a tonicization
can be a *confident* window, so confidence-gating can't remove it — but "is the
excursion's tonic a diatonic degree of the parent?" can. The discriminator
(revised with A6 brief-11) is **brief OR (related AND returns)**: only a
*sustained* region (>= ``min_modulation_beats``, the phrase-length floor) can
establish a new structural key; a brief excursion is a tonicization — diatonic,
or (when unrelated) a brief *chromatic* one. Duration is what separates
"tonicization of V" from "modulation to the dominant".

A derived reduction — it **never overrides**; the raw local ``KeyTrackingResult``
rides along as evidence, and the global ``infer_key`` reading is recorded so
anchor-vs-global is visible. Slice 1: whole-sequence batch, single deterministic
pass, one level (excursions tested against the current structural key only).
Thresholds are a versioned prior, set by theory — never fit to a (BY-NC-SA)
validation corpus.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..analysis.key_induction import infer_key
from .key_tracking import DEFAULT_HOP_BEATS, DEFAULT_WINDOW_BEATS, KeyRegion, KeyTrackingResult, track_keys
from .sequence import Sequence

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..io.loaders import KeyProfileSet, StructuralKeyPriors

_EPS = 1e-9
_MODE_SCALE = {"major": "Ionian", "minor": "Natural Minor"}


@dataclass(frozen=True)
class Tonicization:
    """A diatonically-related excursion absorbed into its parent key area.

    ``degree`` is ``(tonic_pc − parent_tonic_pc) % 12`` (an interval class 0..11;
    display renders V / ii / vi). ``region_score`` is the absorbed window's
    confidence, so a consumer can see how strong the blip was."""

    degree: int
    tonic_pc: int
    mode: str
    start_beats: float
    end_beats: float
    start_seconds: float
    end_seconds: float
    region_score: float


@dataclass(frozen=True)
class StructuralKeyArea:
    """A structural key span: a key + the tonicizations absorbed within it."""

    start_beats: float
    end_beats: float
    start_seconds: float
    end_seconds: float
    tonic_pc: int
    mode: str
    tonicizations: tuple[Tonicization, ...]
    region_count: int   # source KeyRegions feeding this area (continuations + absorbed)
    window_count: int   # summed evidence depth

    @property
    def duration_beats(self) -> float:
        return self.end_beats - self.start_beats


@dataclass(frozen=True)
class StructuralKeyResult:
    """Structural key-areas reduced from the windowed local track.

    The home key (the anchor) is chosen by ``anchor_method`` — ``frame_weighted``
    by default (A6 brief-8); the global ``infer_key`` reading rides along as
    evidence (``global_*``), as does the full local ``tracking``. ``prior_version``
    cites the versioned thresholds.
    """

    areas: tuple[StructuralKeyArea, ...]
    home_tonic_pc: int
    home_mode: str
    anchor_method: str
    global_tonic_pc: int
    global_mode: str
    global_margin: float
    tracking: KeyTrackingResult
    prior_version: str
    window_beats: float
    hop_beats: float

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def _diatonic_pcs(tonic_pc: int, mode: str) -> frozenset[int]:
    from ..io.loaders import load_scales

    degrees = load_scales()[_MODE_SCALE[mode]].degrees
    return frozenset((tonic_pc + d) % 12 for d in degrees)


ANCHOR_METHODS = ("most_prevalent_region", "frame_weighted")


def _anchor(
    regions: list[KeyRegion],
    global_key: tuple[int, str],
    *,
    method: str = "most_prevalent_region",
    frame_bonus: float = 1.0,
) -> tuple[int, str]:
    """The home key, by summed local-region duration (``most_prevalent_region``).

    ``frame_weighted`` adds ``frame_bonus × duration`` to the opening and closing
    regions before the argmax: the structural frame is the place least likely to
    be a tonicization, so it is the most tonicization-robust home-key signal when
    the interior is full of tonicizations (a repeatedly-tonicized dominant can
    out-total the tonic by raw duration — A6 brief-7). A *bonus* on top of
    duration, not a replacement, so it never overturns a genuine duration majority.
    Symmetric risk (accepted): a piece ending in a *sustained, non-returning*
    modulation gets a closing-frame vote for that ending key — but A6 brief-8
    measured zero such regressions across the 24-song Winterreise set (real tonal
    closure rarely ends with the longest region off-tonic), so the net is a Pareto
    win that earned the default.
    """

    totals: dict[tuple[int, str], float] = {}
    first_seen: dict[tuple[int, str], float] = {}
    for r in regions:
        key = (r.tonic_pc, r.mode)
        totals[key] = totals.get(key, 0.0) + r.duration_beats
        first_seen.setdefault(key, r.start_beats)

    scores = dict(totals)
    if method == "frame_weighted" and frame_bonus > 0 and regions:
        for frame in (regions[0], regions[-1]):  # opening + closing assertions
            fk = (frame.tonic_pc, frame.mode)
            scores[fk] = scores.get(fk, 0.0) + frame_bonus * frame.duration_beats

    best = max(scores.values())
    tied = [k for k, v in scores.items() if best - v <= _EPS]
    if len(tied) == 1:
        return tied[0]
    if global_key in tied:  # prefer the global home-key estimate among ties
        return global_key
    # else earliest occurrence, then lexicographic
    return min(tied, key=lambda k: (first_seen[k], k[0], k[1]))


def _returns(regions: list[KeyRegion], i: int, current: tuple[int, str], diatonic: frozenset[int]) -> bool:
    """True if a later region re-establishes ``current`` with every intervening
    region diatonically related (a return *through* a foreign key doesn't count)."""

    for j in range(i + 1, len(regions)):
        if (regions[j].tonic_pc, regions[j].mode) == current:
            return True
        if regions[j].tonic_pc not in diatonic:
            return False
    return False


def reduce_to_structural_keys(
    sequence: Sequence,
    *,
    window_beats: float = DEFAULT_WINDOW_BEATS,
    hop_beats: float = DEFAULT_HOP_BEATS,
    profiles: "KeyProfileSet | None" = None,
    tracking: "KeyTrackingResult | None" = None,
    priors: "StructuralKeyPriors | None" = None,
    anchor_method: str = "frame_weighted",
) -> StructuralKeyResult:
    """Reduce a sequence's windowed local key track to structural key-areas.

    Absorbs brief, diatonically-related excursions (tonicizations) into their
    parent key; keeps sustained/structural key changes (modulations). Pass a
    precomputed ``tracking`` (e.g. with ``smoothing``/``disambiguate_relative``)
    to reduce that track instead of recomputing. Raises ``ValueError`` (via
    ``track_keys``/``infer_key``) on empty or uninformative material — never
    invents a key.

    ``anchor_method`` selects how the home key is chosen: ``frame_weighted``
    (default — adds a theory-set bonus to the opening + closing regions, the
    tonicization-robust home-key signal) or ``most_prevalent_region`` (the legacy
    slice-1 method — longest summed local-region duration; over-counts a
    repeatedly-tonicized dominant). A wrong home anchor poisons every downstream
    relatedness test. ``frame_weighted`` promoted to default after A6 brief-8
    validated it on the full 24-song Winterreise set: a Pareto improvement
    (+10.1pp on the global-key-miss subset, 0 regressions on correctly-anchored
    songs). Note its known limit: it can only promote a tonic region the local
    track already proposes (residual global-key misses are upstream — the
    `infer_key`/local-fit lever, not the anchor).
    """

    if anchor_method not in ANCHOR_METHODS:
        raise ValueError(
            f"anchor_method must be one of {ANCHOR_METHODS}, got {anchor_method!r}"
        )
    if priors is None:
        from ..io.loaders import load_structural_key_priors

        priors = load_structural_key_priors()
    if tracking is None:
        tracking = track_keys(sequence, window_beats=window_beats, hop_beats=hop_beats, profiles=profiles)
    else:
        window_beats, hop_beats = tracking.window_beats, tracking.hop_beats

    induction = infer_key(sequence, profiles=profiles)
    global_key = (induction.best.tonic_pc, induction.best.mode)

    regions = tracking.regions
    anchor = _anchor(
        regions, global_key,
        method=anchor_method, frame_bonus=priors.frame_anchor_bonus,
    )
    current = anchor

    areas: list[StructuralKeyArea] = []
    open_area: dict | None = None

    def _open(region: KeyRegion, key: tuple[int, str]) -> dict:
        # An empty area (end == start); regions that belong to it call _extend.
        return {
            "start_beats": region.start_beats, "start_seconds": region.start_seconds,
            "end_beats": region.start_beats, "end_seconds": region.start_seconds,
            "tonic_pc": key[0], "mode": key[1], "tonicizations": [],
            "region_count": 0, "window_count": 0,
        }

    def _extend(area: dict, region: KeyRegion) -> None:
        area["end_beats"], area["end_seconds"] = region.end_beats, region.end_seconds
        area["region_count"] += 1
        area["window_count"] += region.window_count

    def _close(area: dict) -> None:
        if area["region_count"] > 0:  # drop the empty leading anchor area, if any
            areas.append(StructuralKeyArea(
                start_beats=area["start_beats"], end_beats=area["end_beats"],
                start_seconds=area["start_seconds"], end_seconds=area["end_seconds"],
                tonic_pc=area["tonic_pc"], mode=area["mode"],
                tonicizations=tuple(area["tonicizations"]),
                region_count=area["region_count"], window_count=area["window_count"],
            ))

    for i, region in enumerate(regions):
        rkey = (region.tonic_pc, region.mode)
        if open_area is None:
            open_area = _open(region, current)

        if rkey == current:
            _extend(open_area, region)
            continue

        diatonic = _diatonic_pcs(current[0], current[1])
        related = region.tonic_pc in diatonic
        brief = region.duration_beats < priors.min_modulation_beats - _EPS
        # A structural modulation requires SUSTAINED presence (the min_modulation_beats
        # phrase-length floor) — this applies to *every* excursion, related or not. A
        # brief excursion is a tonicization: a diatonic one, or (when unrelated) a brief
        # chromatic one. Only a sustained region establishes a new structural key; this
        # stops a 2-beat unrelated blip from anchoring a large spurious area that then
        # absorbs everything around it (A6 brief-11, D911-11: a 2-beat G-major window —
        # 4 beats total in the piece — was anchoring a 122-beat area).
        if brief or (related and _returns(regions, i, current, diatonic)):
            open_area["tonicizations"].append(Tonicization(
                degree=(region.tonic_pc - current[0]) % 12,
                tonic_pc=region.tonic_pc, mode=region.mode,
                start_beats=region.start_beats, end_beats=region.end_beats,
                start_seconds=region.start_seconds, end_seconds=region.end_seconds,
                region_score=region.mean_score,
            ))
            _extend(open_area, region)
        else:  # modulation
            _close(open_area)
            current = rkey
            open_area = _open(region, current)
            _extend(open_area, region)

    if open_area is not None:
        _close(open_area)

    return StructuralKeyResult(
        areas=tuple(areas),
        home_tonic_pc=anchor[0],
        home_mode=anchor[1],
        anchor_method=anchor_method,
        global_tonic_pc=global_key[0],
        global_mode=global_key[1],
        global_margin=round(induction.margin, 6),
        tracking=tracking,
        prior_version=priors.version,
        window_beats=window_beats,
        hop_beats=hop_beats,
    )


__all__ = [
    "Tonicization",
    "StructuralKeyArea",
    "StructuralKeyResult",
    "reduce_to_structural_keys",
]
