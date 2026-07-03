"""JSON data loaders for music theory models."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ..core.bitmask import validate_pc
from ..core.interval import Interval
from ..core.quality import ChordQuality
from ..core.scale import Scale
from ..analysis.builders import SessionCatalog, _DEFAULT_SESSION
from ..theory.functions import (
    DEFAULT_FEATURES_MAJOR,
    DEFAULT_FEATURES_MINOR,
    TEMPLATES_MAJOR,
    TEMPLATES_MINOR,
    FunctionTemplate,
    generate_functions_for_scale,
)

# Catalogs/priors ship inside the package (mts/data/) so an *installed* copy
# works — parents[1] is the mts package dir, valid in a checkout and a wheel.
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Parsed base catalogs, cached per (path, mtime). Catalog objects are frozen
# dataclasses, so sharing them across the dicts returned to callers is safe;
# the JSON is re-read only when the file changes on disk.
_BASE_SCALES_CACHE: tuple[Path, int, dict[str, Scale]] | None = None
_BASE_QUALITIES_CACHE: tuple[Path, int, dict[str, ChordQuality]] | None = None
_KEY_PROFILES_CACHE: tuple[Path, int, tuple["KeyProfileSet", ...]] | None = None
_NAMING_WEIGHTS_CACHE: tuple[Path, int, tuple["NamingWeights", ...]] | None = None
_SWING_FEEL_CACHE: tuple[Path, int, tuple["SwingFeelPriors", ...]] | None = None
_SUCCESSION_WEIGHTS_CACHE: tuple[Path, int, tuple["SuccessionWeights", ...]] | None = None
_RELATIVE_KEY_CACHE: tuple[Path, int, tuple["RelativeKeyWeights", ...]] | None = None
_KEY_SMOOTHING_CACHE: tuple[Path, int, tuple["KeySmoothingPriors", ...]] | None = None
_KEY_INERTIA_CACHE: tuple[Path, int, tuple["KeyInertiaPriors", ...]] | None = None
_SCORING_PRIORS_CACHE: tuple[Path, int, tuple["ScoringPrior", ...]] | None = None
_METER_PROFILES_CACHE: tuple[Path, int, tuple["MeterProfileSet", ...]] | None = None
_STRUCTURAL_KEY_CACHE: tuple[Path, int, tuple["StructuralKeyPriors", ...]] | None = None


@dataclass(frozen=True)
class FunctionMapping:
    degree_pc: int
    chord_quality: str
    intervals: tuple[int, ...]
    role: str
    modal_label: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class NamingWeights:
    """One versioned naming-signal weight table (a versioned empirical prior).

    ``weights`` maps signal name → weight; ``ambiguity_margin`` is the
    top-two score gap below which a naming is flagged ambiguous;
    ``marginalization`` configures how multi-key namings combine per-key
    scores. Results cite ``version`` (ROADMAP "versioned-priors pattern").
    """

    version: str
    source: str
    weights: dict[str, float]
    ambiguity_margin: float
    marginalization: dict


@dataclass(frozen=True)
class SwingFeelPriors:
    """One versioned swing-feel classification table (a versioned empirical prior).

    ``straight_tolerance`` is the half-width around the even split (0.5)
    within which a mean division fraction still reads as straight;
    ``consistency_tolerance`` is the fraction-stddev ceiling above which a
    line has no single feel (``mixed``); ``min_divisions`` is the evidence
    floor below which no feel claim is made. Results cite ``version``
    (ROADMAP "versioned-priors pattern").
    """

    version: str
    source: str
    straight_tolerance: float
    consistency_tolerance: float
    min_divisions: int


@dataclass(frozen=True)
class SuccessionWeights:
    """One versioned next-chord scoring table (a versioned empirical prior).

    ``weights`` maps a succession signal name (functional + voice-leading) to
    its score contribution; the two scaled signals are ``common_tone`` (per
    shared pitch class) and ``vl_distance`` (per semitone of motion, a
    penalty). ``color_shift`` carries a weight of 0 in ``succession.1`` —
    reported, not preferred. Results cite ``version`` (ROADMAP
    "versioned-priors pattern"; the per-style corpus transition prior is the
    planned successor — gap 14).
    """

    version: str
    source: str
    weights: dict[str, float]


@dataclass(frozen=True)
class RelativeKeyWeights:
    """One versioned relative-major/minor tie-breaker table (a versioned prior).

    ``weights`` maps a tonal-hierarchy signal name to its score weight (positive
    score favors the minor reading); ``near_tie_margin`` is the correlation gap
    below which the top key and its relative partner count as a tie worth
    breaking; ``decision_margin`` is the tie-break-score band that stays honestly
    ambiguous. Results cite ``version`` (ROADMAP "versioned-priors pattern").
    """

    version: str
    source: str
    weights: dict[str, float]
    near_tie_margin: float
    decision_margin: float


@dataclass(frozen=True)
class KeySmoothingPriors:
    """One versioned key-region smoothing table (a versioned empirical prior).

    Opt-in hysteresis for local key tracking: a region with fewer than
    ``min_region_windows`` windows whose ``mean_margin`` is below
    ``min_region_margin`` is a low-confidence blip and is absorbed into its
    stronger neighbour; a short region with a strong margin is a confident brief
    modulation and is kept. Results cite ``version`` (ROADMAP
    "versioned-priors pattern").
    """

    version: str
    source: str
    min_region_windows: int
    min_region_margin: float


@dataclass(frozen=True)
class KeyInertiaPriors:
    """One versioned key-inertia (continuity prior) table (a versioned prior).

    Opt-in transition-penalized local key tracking (A6 brief-13; Temperley's
    deterministic key-inertia): ``switch_penalty`` is a flat, one-time score cost
    subtracted when the Viterbi path changes the ``(tonic, mode)`` state between
    consecutive informative windows. Penalizes switching, not distance; theory-set,
    not corpus-fit. Results cite ``version``.
    """

    version: str
    source: str
    switch_penalty: float


@dataclass(frozen=True)
class ScoringPrior:
    """One versioned ruleset-induction scoring table (a versioned empirical prior).

    Documents the mining + interestingness configuration so an induction result is
    reproducible and self-describing: the ``measure`` (Fisher's exact) and
    ``null_model`` (independence given marginals), the piece-presence
    ``min_support_pieces`` floor, ``exploratory_floor_pieces`` (below which results
    are flagged exploratory), the BH-FDR ``fdr_q``, the ``arity_cap`` on conjunction
    length, and ``weight_scale`` mapping |leverage| → soft-rule weight. Results cite
    ``version`` (ROADMAP "versioned-priors pattern").
    """

    version: str
    source: str
    measure: str
    null_model: str
    min_support_pieces: int
    exploratory_floor_pieces: int
    fdr_q: float
    arity_cap: int
    weight_scale: float


@dataclass(frozen=True)
class StructuralKeyPriors:
    """One versioned structural-key-reduction table (a versioned empirical prior).

    Distinguishes a tonicization (a brief, diatonically-related excursion absorbed
    into the parent key) from a modulation (a sustained/structural key change
    kept): ``min_modulation_beats`` is the duration floor below which a related
    excursion reads as a tonicization; ``min_area_beats`` floors a structural
    modulation area (reserved); ``require_return`` gates the prolongational
    return rule (reserved). ``frame_anchor_bonus`` weights the opening + closing
    regions when ``anchor_method='frame_weighted'`` is selected (the structural
    frame is the most tonicization-robust home-key signal — A6 brief-7). Defaults
    are theory-set, never corpus-fit. Results cite ``version`` (ROADMAP
    "versioned-priors pattern").
    """

    version: str
    source: str
    min_modulation_beats: float
    min_area_beats: float
    require_return: bool
    frame_anchor_bonus: float = 1.0


@dataclass(frozen=True)
class MeterProfileSet:
    """One versioned set of metric-profile templates (a versioned empirical prior).

    ``profiles`` maps a ``"num/den"`` signature to a per-grid-position weight
    template (metric salience, one value per ``grid_beats`` slot across one bar).
    Meter estimation folds onset salience onto each candidate bar and correlates
    it with the template, weighted by the bar-period autocorrelation. Results
    cite ``version`` (ROADMAP "versioned-priors pattern").
    """

    version: str
    source: str
    grid_beats: float
    profiles: dict[str, tuple[float, ...]]


@dataclass(frozen=True)
class KeyProfileSet:
    """One versioned set of key profiles (a versioned empirical prior).

    ``profiles`` maps a mode name (e.g. ``"major"``) to 12 per-pc weights with
    the tonic at index 0. Results derived from a profile set cite ``version``
    so rankings stay reproducible (ROADMAP "versioned-priors pattern").
    """

    version: str
    source: str
    profiles: dict[str, tuple[float, ...]]


def _read_json(name: str) -> list[dict]:
    path = DATA_DIR / name
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"JSON file {name} must contain a list")
    return data


def load_key_profiles(version: str | None = None) -> KeyProfileSet:
    """Load a versioned key-profile set from ``data/key_profiles.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime,
    like the catalogs.
    """
    global _KEY_PROFILES_CACHE
    path = DATA_DIR / "key_profiles.json"
    mtime = path.stat().st_mtime_ns
    if _KEY_PROFILES_CACHE is not None and _KEY_PROFILES_CACHE[:2] == (path, mtime):
        entries = _KEY_PROFILES_CACHE[2]
    else:
        parsed: list[KeyProfileSet] = []
        for payload in _read_json("key_profiles.json"):
            profiles: dict[str, tuple[float, ...]] = {}
            for mode, values in dict(payload["profiles"]).items():
                weights = tuple(float(v) for v in values)
                if len(weights) != 12:
                    raise ValueError(
                        f"Key profile {payload['version']!r}/{mode!r} must have 12 weights"
                    )
                profiles[str(mode)] = weights
            if not profiles:
                raise ValueError(f"Key profile set {payload['version']!r} defines no modes")
            parsed.append(
                KeyProfileSet(
                    version=str(payload["version"]),
                    source=str(payload.get("source", "")),
                    profiles=profiles,
                )
            )
        if not parsed:
            raise ValueError("key_profiles.json contains no profile sets")
        entries = tuple(parsed)
        _KEY_PROFILES_CACHE = (path, mtime, entries)
    if version is None:
        return entries[0]
    for entry in entries:
        if entry.version == version:
            return entry
    known = ", ".join(e.version for e in entries)
    raise ValueError(f"Unknown key-profile version {version!r} (known: {known})")


def load_naming_weights(version: str | None = None) -> NamingWeights:
    """Load a versioned naming-weight table from ``data/naming_weights.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    global _NAMING_WEIGHTS_CACHE
    path = DATA_DIR / "naming_weights.json"
    mtime = path.stat().st_mtime_ns
    if _NAMING_WEIGHTS_CACHE is not None and _NAMING_WEIGHTS_CACHE[:2] == (path, mtime):
        entries = _NAMING_WEIGHTS_CACHE[2]
    else:
        parsed: list[NamingWeights] = []
        for payload in _read_json("naming_weights.json"):
            weights = {str(k): float(v) for k, v in dict(payload["weights"]).items()}
            if not weights:
                raise ValueError(f"Naming weights {payload['version']!r} define no signals")
            parsed.append(
                NamingWeights(
                    version=str(payload["version"]),
                    source=str(payload.get("source", "")),
                    weights=weights,
                    ambiguity_margin=float(payload.get("ambiguity_margin", 0.0)),
                    marginalization=dict(payload.get("marginalization", {})),
                )
            )
        if not parsed:
            raise ValueError("naming_weights.json contains no weight tables")
        entries = tuple(parsed)
        _NAMING_WEIGHTS_CACHE = (path, mtime, entries)
    if version is None:
        return entries[0]
    for entry in entries:
        if entry.version == version:
            return entry
    known = ", ".join(e.version for e in entries)
    raise ValueError(f"Unknown naming-weights version {version!r} (known: {known})")


def load_swing_priors(version: str | None = None) -> SwingFeelPriors:
    """Load a versioned swing-feel prior from ``data/swing_feel.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    global _SWING_FEEL_CACHE
    path = DATA_DIR / "swing_feel.json"
    mtime = path.stat().st_mtime_ns
    if _SWING_FEEL_CACHE is not None and _SWING_FEEL_CACHE[:2] == (path, mtime):
        entries = _SWING_FEEL_CACHE[2]
    else:
        parsed: list[SwingFeelPriors] = []
        for payload in _read_json("swing_feel.json"):
            priors = SwingFeelPriors(
                version=str(payload["version"]),
                source=str(payload.get("source", "")),
                straight_tolerance=float(payload["straight_tolerance"]),
                consistency_tolerance=float(payload["consistency_tolerance"]),
                min_divisions=int(payload["min_divisions"]),
            )
            if not 0.0 < priors.straight_tolerance < 0.5:
                raise ValueError(f"Swing prior {priors.version!r}: straight_tolerance out of (0, 0.5)")
            if priors.min_divisions < 1:
                raise ValueError(f"Swing prior {priors.version!r}: min_divisions must be >= 1")
            parsed.append(priors)
        if not parsed:
            raise ValueError("swing_feel.json contains no prior tables")
        entries = tuple(parsed)
        _SWING_FEEL_CACHE = (path, mtime, entries)
    if version is None:
        return entries[0]
    for entry in entries:
        if entry.version == version:
            return entry
    known = ", ".join(e.version for e in entries)
    raise ValueError(f"Unknown swing-feel version {version!r} (known: {known})")


def load_succession_weights(version: str | None = None) -> SuccessionWeights:
    """Load a versioned succession-weight table from ``data/succession_weights.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    global _SUCCESSION_WEIGHTS_CACHE
    path = DATA_DIR / "succession_weights.json"
    mtime = path.stat().st_mtime_ns
    if (
        _SUCCESSION_WEIGHTS_CACHE is not None
        and _SUCCESSION_WEIGHTS_CACHE[:2] == (path, mtime)
    ):
        entries = _SUCCESSION_WEIGHTS_CACHE[2]
    else:
        parsed: list[SuccessionWeights] = []
        for payload in _read_json("succession_weights.json"):
            weights = {str(k): float(v) for k, v in dict(payload["weights"]).items()}
            if not weights:
                raise ValueError(
                    f"Succession weights {payload['version']!r} define no signals"
                )
            parsed.append(
                SuccessionWeights(
                    version=str(payload["version"]),
                    source=str(payload.get("source", "")),
                    weights=weights,
                )
            )
        if not parsed:
            raise ValueError("succession_weights.json contains no weight tables")
        entries = tuple(parsed)
        _SUCCESSION_WEIGHTS_CACHE = (path, mtime, entries)
    if version is None:
        return entries[0]
    for entry in entries:
        if entry.version == version:
            return entry
    known = ", ".join(e.version for e in entries)
    raise ValueError(f"Unknown succession-weights version {version!r} (known: {known})")


def load_relative_key_weights(version: str | None = None) -> RelativeKeyWeights:
    """Load a versioned relative-key tie-breaker from ``data/relative_key_weights.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    global _RELATIVE_KEY_CACHE
    path = DATA_DIR / "relative_key_weights.json"
    mtime = path.stat().st_mtime_ns
    if _RELATIVE_KEY_CACHE is not None and _RELATIVE_KEY_CACHE[:2] == (path, mtime):
        entries = _RELATIVE_KEY_CACHE[2]
    else:
        parsed: list[RelativeKeyWeights] = []
        for payload in _read_json("relative_key_weights.json"):
            weights = {str(k): float(v) for k, v in dict(payload["weights"]).items()}
            if not weights:
                raise ValueError(
                    f"Relative-key weights {payload['version']!r} define no signals"
                )
            parsed.append(
                RelativeKeyWeights(
                    version=str(payload["version"]),
                    source=str(payload.get("source", "")),
                    weights=weights,
                    near_tie_margin=float(payload["near_tie_margin"]),
                    decision_margin=float(payload["decision_margin"]),
                )
            )
        if not parsed:
            raise ValueError("relative_key_weights.json contains no weight tables")
        entries = tuple(parsed)
        _RELATIVE_KEY_CACHE = (path, mtime, entries)
    if version is None:
        return entries[0]
    for entry in entries:
        if entry.version == version:
            return entry
    known = ", ".join(e.version for e in entries)
    raise ValueError(f"Unknown relative-key version {version!r} (known: {known})")


def load_key_smoothing(version: str | None = None) -> KeySmoothingPriors:
    """Load a versioned key-region smoothing prior from ``data/key_smoothing.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    global _KEY_SMOOTHING_CACHE
    path = DATA_DIR / "key_smoothing.json"
    mtime = path.stat().st_mtime_ns
    if _KEY_SMOOTHING_CACHE is not None and _KEY_SMOOTHING_CACHE[:2] == (path, mtime):
        entries = _KEY_SMOOTHING_CACHE[2]
    else:
        parsed: list[KeySmoothingPriors] = []
        for payload in _read_json("key_smoothing.json"):
            priors = KeySmoothingPriors(
                version=str(payload["version"]),
                source=str(payload.get("source", "")),
                min_region_windows=int(payload["min_region_windows"]),
                min_region_margin=float(payload["min_region_margin"]),
            )
            if priors.min_region_windows < 1:
                raise ValueError(
                    f"Key smoothing {priors.version!r}: min_region_windows must be >= 1"
                )
            parsed.append(priors)
        if not parsed:
            raise ValueError("key_smoothing.json contains no prior tables")
        entries = tuple(parsed)
        _KEY_SMOOTHING_CACHE = (path, mtime, entries)
    if version is None:
        return entries[0]
    for entry in entries:
        if entry.version == version:
            return entry
    known = ", ".join(e.version for e in entries)
    raise ValueError(f"Unknown key-smoothing version {version!r} (known: {known})")


def load_key_inertia(version: str | None = None) -> KeyInertiaPriors:
    """Load a versioned key-inertia prior from ``data/key_inertia.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    global _KEY_INERTIA_CACHE
    path = DATA_DIR / "key_inertia.json"
    mtime = path.stat().st_mtime_ns
    if _KEY_INERTIA_CACHE is not None and _KEY_INERTIA_CACHE[:2] == (path, mtime):
        entries = _KEY_INERTIA_CACHE[2]
    else:
        parsed: list[KeyInertiaPriors] = []
        for payload in _read_json("key_inertia.json"):
            priors = KeyInertiaPriors(
                version=str(payload["version"]),
                source=str(payload.get("source", "")),
                switch_penalty=float(payload["switch_penalty"]),
            )
            if priors.switch_penalty < 0:
                raise ValueError(
                    f"Key inertia {priors.version!r}: switch_penalty must be >= 0"
                )
            parsed.append(priors)
        if not parsed:
            raise ValueError("key_inertia.json contains no prior tables")
        entries = tuple(parsed)
        _KEY_INERTIA_CACHE = (path, mtime, entries)
    if version is None:
        return entries[0]
    for entry in entries:
        if entry.version == version:
            return entry
    known = ", ".join(e.version for e in entries)
    raise ValueError(f"Unknown key-inertia version {version!r} (known: {known})")


def load_scoring_prior(version: str | None = None) -> ScoringPrior:
    """Load a versioned induction scoring prior from ``data/scoring_priors.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    global _SCORING_PRIORS_CACHE
    path = DATA_DIR / "scoring_priors.json"
    mtime = path.stat().st_mtime_ns
    if _SCORING_PRIORS_CACHE is not None and _SCORING_PRIORS_CACHE[:2] == (path, mtime):
        entries = _SCORING_PRIORS_CACHE[2]
    else:
        parsed: list[ScoringPrior] = []
        for payload in _read_json("scoring_priors.json"):
            prior = ScoringPrior(
                version=str(payload["version"]),
                source=str(payload.get("source", "")),
                measure=str(payload["measure"]),
                null_model=str(payload["null_model"]),
                min_support_pieces=int(payload["min_support_pieces"]),
                exploratory_floor_pieces=int(payload["exploratory_floor_pieces"]),
                fdr_q=float(payload["fdr_q"]),
                arity_cap=int(payload["arity_cap"]),
                weight_scale=float(payload["weight_scale"]),
            )
            if prior.min_support_pieces < 1:
                raise ValueError(
                    f"Scoring prior {prior.version!r}: min_support_pieces must be >= 1"
                )
            if prior.arity_cap < 1:
                raise ValueError(
                    f"Scoring prior {prior.version!r}: arity_cap must be >= 1"
                )
            if not 0.0 < prior.fdr_q < 1.0:
                raise ValueError(
                    f"Scoring prior {prior.version!r}: fdr_q must be in (0, 1)"
                )
            parsed.append(prior)
        if not parsed:
            raise ValueError("scoring_priors.json contains no prior tables")
        entries = tuple(parsed)
        _SCORING_PRIORS_CACHE = (path, mtime, entries)
    if version is None:
        return entries[0]
    for entry in entries:
        if entry.version == version:
            return entry
    known = ", ".join(e.version for e in entries)
    raise ValueError(f"Unknown scoring-prior version {version!r} (known: {known})")


def load_meter_profiles(version: str | None = None) -> MeterProfileSet:
    """Load a versioned metric-profile set from ``data/meter_profiles.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    global _METER_PROFILES_CACHE
    path = DATA_DIR / "meter_profiles.json"
    mtime = path.stat().st_mtime_ns
    if _METER_PROFILES_CACHE is not None and _METER_PROFILES_CACHE[:2] == (path, mtime):
        entries = _METER_PROFILES_CACHE[2]
    else:
        parsed: list[MeterProfileSet] = []
        for payload in _read_json("meter_profiles.json"):
            profiles = {
                str(sig): tuple(float(w) for w in weights)
                for sig, weights in dict(payload["profiles"]).items()
            }
            if not profiles:
                raise ValueError(f"Meter profile set {payload['version']!r} defines no meters")
            parsed.append(
                MeterProfileSet(
                    version=str(payload["version"]),
                    source=str(payload.get("source", "")),
                    grid_beats=float(payload["grid_beats"]),
                    profiles=profiles,
                )
            )
        if not parsed:
            raise ValueError("meter_profiles.json contains no profile sets")
        entries = tuple(parsed)
        _METER_PROFILES_CACHE = (path, mtime, entries)
    if version is None:
        return entries[0]
    for entry in entries:
        if entry.version == version:
            return entry
    known = ", ".join(e.version for e in entries)
    raise ValueError(f"Unknown meter-profile version {version!r} (known: {known})")


def load_structural_key_priors(version: str | None = None) -> StructuralKeyPriors:
    """Load a versioned structural-key prior from ``data/structural_key.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    global _STRUCTURAL_KEY_CACHE
    path = DATA_DIR / "structural_key.json"
    mtime = path.stat().st_mtime_ns
    if _STRUCTURAL_KEY_CACHE is not None and _STRUCTURAL_KEY_CACHE[:2] == (path, mtime):
        entries = _STRUCTURAL_KEY_CACHE[2]
    else:
        parsed: list[StructuralKeyPriors] = []
        for payload in _read_json("structural_key.json"):
            priors = StructuralKeyPriors(
                version=str(payload["version"]),
                source=str(payload.get("source", "")),
                min_modulation_beats=float(payload["min_modulation_beats"]),
                min_area_beats=float(payload["min_area_beats"]),
                require_return=bool(payload["require_return"]),
                frame_anchor_bonus=float(payload.get("frame_anchor_bonus", 1.0)),
            )
            if priors.min_modulation_beats <= 0 or priors.min_area_beats <= 0:
                raise ValueError(
                    f"Structural-key prior {priors.version!r}: beat floors must be > 0"
                )
            if priors.frame_anchor_bonus < 0:
                raise ValueError(
                    f"Structural-key prior {priors.version!r}: frame_anchor_bonus must be >= 0"
                )
            parsed.append(priors)
        if not parsed:
            raise ValueError("structural_key.json contains no prior tables")
        entries = tuple(parsed)
        _STRUCTURAL_KEY_CACHE = (path, mtime, entries)
    if version is None:
        return entries[0]
    for entry in entries:
        if entry.version == version:
            return entry
    known = ", ".join(e.version for e in entries)
    raise ValueError(f"Unknown structural-key version {version!r} (known: {known})")


def load_intervals() -> list[Interval]:
    entries: list[Interval] = []
    for payload in _read_json("intervals.json"):
        semitones = int(payload["semitones"])
        validate_pc(semitones)
        entries.append(Interval.from_dict(payload))
    return entries


def _base_scales() -> dict[str, Scale]:
    """Parse the scale catalog JSON, cached until the file's mtime changes."""
    global _BASE_SCALES_CACHE
    path = DATA_DIR / "scales.json"
    mtime = path.stat().st_mtime_ns
    if _BASE_SCALES_CACHE is not None:
        cached_path, cached_mtime, cached_scales = _BASE_SCALES_CACHE
        if cached_path == path and cached_mtime == mtime:
            return cached_scales
    scales: dict[str, Scale] = {}
    for payload in _read_json("scales.json"):
        name = str(payload["name"])
        degrees = payload["degrees"]
        if not isinstance(degrees, list) or not degrees:
            raise ValueError(f"Scale {name} must define degree list")
        for degree in degrees:
            validate_pc(int(degree))
        aliases_field = payload.get("aliases", [])
        if aliases_field is None:
            aliases_field = []
        if not isinstance(aliases_field, list):
            raise ValueError(f"Scale {name} aliases must be a list if provided")
        aliases: list[str] = []
        for alias in aliases_field:
            alias_str = str(alias).strip()
            if alias_str:
                aliases.append(alias_str)
        scale = Scale.from_degrees(name, degrees, aliases)
        if name in scales:
            raise ValueError(f"Duplicate scale name detected: {name}")
        scales[name] = scale
        for alias in scale.aliases:
            if alias in scales:
                raise ValueError(f"Duplicate scale alias detected: {alias}")
            scales[alias] = scale
    _BASE_SCALES_CACHE = (path, mtime, scales)
    return scales


def load_scales(session: SessionCatalog | None = None) -> dict[str, Scale]:
    """Load the scale catalog from JSON, merged with any session-registered scales.

    Parameters
    ----------
    session:
        The ``SessionCatalog`` whose user-defined scales should be merged in.
        When *None* the module-level default session is used, preserving the
        original behaviour for standalone scripts and the CLI.
    """
    _session = session if session is not None else _DEFAULT_SESSION
    scales = dict(_base_scales())
    if _session.scales:
        for manual in _session.scales.values():
            if manual.name not in scales:
                scales[manual.name] = manual
    return scales


def _base_chord_qualities() -> dict[str, ChordQuality]:
    """Parse the chord-quality catalog JSON, cached until the file's mtime changes."""
    global _BASE_QUALITIES_CACHE
    path = DATA_DIR / "chord_qualities.json"
    mtime = path.stat().st_mtime_ns
    if _BASE_QUALITIES_CACHE is not None:
        cached_path, cached_mtime, cached_qualities = _BASE_QUALITIES_CACHE
        if cached_path == path and cached_mtime == mtime:
            return cached_qualities
    qualities: dict[str, ChordQuality] = {}
    for payload in _read_json("chord_qualities.json"):
        name = str(payload["name"])
        intervals = payload["intervals"]
        tensions = payload.get("tensions", [])
        if not isinstance(intervals, list) or not intervals:
            raise ValueError(f"Chord quality {name} must define interval list")
        for interval in intervals:
            validate_pc(int(interval))
        for tension in tensions:
            validate_pc(int(tension))
        aliases_field = payload.get("aliases", [])
        if aliases_field is None:
            aliases_field = []
        if not isinstance(aliases_field, list):
            raise ValueError(f"Chord quality {name} aliases must be a list if provided")
        aliases = [str(alias).strip() for alias in aliases_field if str(alias).strip()]
        quality = ChordQuality.from_intervals(name, intervals, tensions, aliases=aliases)
        if name in qualities:
            raise ValueError(f"Duplicate chord quality name detected: {name}")
        qualities[name] = quality
        for alias in quality.aliases:
            if alias in qualities:
                raise ValueError(f"Duplicate chord quality alias detected: {alias}")
            qualities[alias] = quality
    _BASE_QUALITIES_CACHE = (path, mtime, qualities)
    return qualities


def load_chord_qualities(session: SessionCatalog | None = None) -> dict[str, ChordQuality]:
    """Load the chord-quality catalog from JSON, merged with any session-registered qualities.

    Parameters
    ----------
    session:
        The ``SessionCatalog`` whose user-defined chord qualities should be
        merged in.  When *None* the module-level default session is used.
    """
    _session = session if session is not None else _DEFAULT_SESSION
    qualities = dict(_base_chord_qualities())
    if _session.chords:
        for manual in _session.chords.values():
            if manual.name not in qualities:
                qualities[manual.name] = manual
    return qualities


def load_function_mappings(
    mode: str,
    *,
    strategy: str = "dynamic",
    features: Iterable[str] | None = None,
    include_borrowed: bool | None = None,
    templates: Sequence[FunctionTemplate] | None = None,
) -> list[FunctionMapping]:
    """
    Synthesize functional mappings from scale data and templates.

    Functions are generated by the theory generator in mts/theory/functions.py.
    ``strategy`` is retained for back-compat but only ``"dynamic"`` is supported;
    the legacy static JSON tables were removed.
    """

    mode_key = mode.lower()
    if strategy != "dynamic":
        raise ValueError(
            f"Unsupported strategy: {strategy!r}. Only 'dynamic' is supported "
            "(the legacy static function tables were removed)."
        )

    scales = load_scales()
    chord_qualities = load_chord_qualities()

    if mode_key == "major":
        scale_name = "Ionian"
        template_collection = TEMPLATES_MAJOR if templates is None else templates
        default_features: set[str] = set(DEFAULT_FEATURES_MAJOR)
        default_include_borrowed = False
    elif mode_key == "minor":
        scale_name = "Natural Minor"
        template_collection = TEMPLATES_MINOR if templates is None else templates
        default_features = set(DEFAULT_FEATURES_MINOR)
        default_include_borrowed = True
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    if scale_name not in scales:
        raise ValueError(f"Scale {scale_name!r} required for mode {mode} was not loaded")
    scale = scales[scale_name]

    feature_set: set[str] = set(default_features)
    if features:
        feature_set.update(features)

    include_flag = default_include_borrowed if include_borrowed is None else include_borrowed

    generated = generate_functions_for_scale(
        scale,
        chord_qualities,
        templates=template_collection,
        enabled_features=feature_set,
        include_nondiatic=include_flag,
    )

    return [
        FunctionMapping(
            degree_pc=item.degree_pc,
            chord_quality=item.chord_quality,
            intervals=item.intervals,
            role=item.role,
            modal_label=item.modal_label,
            tags=item.tags,
        )
        for item in generated
    ]
