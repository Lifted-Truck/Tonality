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
from ..session import SessionCatalog
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
# One cache for all ten versioned prior/profile loaders (RE-5f): filename
# -> (mtime_ns, parsed entries). Base catalogs keep their own caches.
_VERSIONED_CACHE: dict[str, tuple[int, tuple]] = {}
# (source_mtimes, {args_key: mappings}) — the function-mapping generator cache
# (RE-5b), keyed by scales.json + chord_qualities.json mtimes.
_FUNCTION_MAPPINGS_CACHE: tuple[tuple[int, int], dict[tuple, list]] | None = None
# (key, index) — chord-quality mask index (RE-5c), keyed by base-catalog
# identity + the given session's chord fingerprint (RE-6b).
_CHORD_MASK_INDEX_CACHE: tuple[tuple, dict[int, tuple]] | None = None


@dataclass(frozen=True)
class FunctionMapping:
    degree_pc: int
    chord_quality: str
    intervals: tuple[int, ...]
    role: str
    modal_label: str
    # RE-3g: the generator emits this (e.g. tonic-prolongation variants); the
    # loader used to drop it on the floor.
    role_subtype: str | None = None
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


def _load_versioned(
    filename: str,
    parse_one,
    *,
    kind: str,
    empty_message: str,
    version: str | None,
):
    """Generic mtime-keyed versioned-prior loader (RE-5f).

    The ten prior/profile loaders shared an identical ~40-line block —
    mtime cache, parse each JSON entry, select by ``version`` (``None`` =
    first/default) or raise with the known versions. Only the per-entry
    ``parse_one(payload)`` body and the labels differ; they now live in small
    ``_parse_*`` functions and this helper carries the boilerplate. Simpler,
    table-driven, and cleaner to port (Phase 8).
    """
    path = DATA_DIR / filename
    mtime = path.stat().st_mtime_ns
    cached = _VERSIONED_CACHE.get(filename)
    if cached is not None and cached[0] == mtime:
        entries = cached[1]
    else:
        entries = tuple(parse_one(payload) for payload in _read_json(filename))
        if not entries:
            raise ValueError(empty_message)
        _VERSIONED_CACHE[filename] = (mtime, entries)
    if version is None:
        return entries[0]
    for entry in entries:
        if entry.version == version:
            return entry
    known = ", ".join(e.version for e in entries)
    raise ValueError(f"Unknown {kind} version {version!r} (known: {known})")


def _parse_key_profile(payload: dict) -> "KeyProfileSet":
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
    return KeyProfileSet(
        version=str(payload["version"]),
        source=str(payload.get("source", "")),
        profiles=profiles,
    )


def load_key_profiles(version: str | None = None) -> KeyProfileSet:
    """Load a versioned key-profile set from ``data/key_profiles.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime,
    like the catalogs.
    """
    return _load_versioned(
        "key_profiles.json", _parse_key_profile,
        kind="key-profile", version=version,
        empty_message="key_profiles.json contains no profile sets",
    )


@dataclass(frozen=True)
class MelodicTendencyPrior:
    """One versioned melodic-tendency table (a versioned empirical prior).

    ``stability`` maps mode -> 12 per-pc stability values, **frozen** from the
    key profiles they were derived from (never read live — a profile default
    flip must not silently move tendency scales). Attraction is
    ``(s_target/s_source) / distance**distance_exponent`` over step targets
    within ``max_step_semitones``; ``chord_anchor_boost`` multiplies the
    stability of chord tones (both roles) when a chord context is given.
    ``target_policies`` is the closed vocabulary the ``targets`` parameter
    accepts. Results cite ``version`` (ROADMAP "versioned-priors pattern").
    """

    version: str
    source: str
    stability: dict[str, tuple[float, ...]]
    distance_exponent: int
    chord_anchor_boost: float
    max_step_semitones: int
    target_policies: tuple[str, ...]


def _parse_melodic_tendency(payload: dict) -> "MelodicTendencyPrior":
    stability: dict[str, tuple[float, ...]] = {}
    for mode, values in dict(payload["stability"]).items():
        table = tuple(float(v) for v in values)
        if len(table) != 12:
            raise ValueError(
                f"Melodic-tendency prior {payload['version']!r}/{mode!r} must have 12 values"
            )
        stability[str(mode)] = table
    if not stability:
        raise ValueError(f"Melodic-tendency prior {payload['version']!r} defines no modes")
    policies = tuple(str(p) for p in payload["target_policies"])
    if not policies:
        raise ValueError(f"Melodic-tendency prior {payload['version']!r} defines no target policies")
    return MelodicTendencyPrior(
        version=str(payload["version"]),
        source=str(payload.get("source", "")),
        stability=stability,
        distance_exponent=int(payload["distance_exponent"]),
        chord_anchor_boost=float(payload["chord_anchor_boost"]),
        max_step_semitones=int(payload["max_step_semitones"]),
        target_policies=policies,
    )


def load_melodic_tendency(version: str | None = None) -> MelodicTendencyPrior:
    """Load a versioned melodic-tendency prior from ``data/melodic_tendency.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime,
    like the other versioned priors.
    """
    return _load_versioned(
        "melodic_tendency.json", _parse_melodic_tendency,
        kind="melodic-tendency", version=version,
        empty_message="melodic_tendency.json contains no priors",
    )


def _parse_naming_weights(payload: dict) -> "NamingWeights":
    weights = {str(k): float(v) for k, v in dict(payload["weights"]).items()}
    if not weights:
        raise ValueError(f"Naming weights {payload['version']!r} define no signals")
    return NamingWeights(
        version=str(payload["version"]),
        source=str(payload.get("source", "")),
        weights=weights,
        ambiguity_margin=float(payload.get("ambiguity_margin", 0.0)),
        marginalization=dict(payload.get("marginalization", {})),
    )


def load_naming_weights(version: str | None = None) -> NamingWeights:
    """Load a versioned naming-weight table from ``data/naming_weights.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    return _load_versioned(
        "naming_weights.json", _parse_naming_weights,
        kind="naming-weights", version=version,
        empty_message="naming_weights.json contains no weight tables",
    )


def _parse_swing_prior(payload: dict) -> "SwingFeelPriors":
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
    return priors


def load_swing_priors(version: str | None = None) -> SwingFeelPriors:
    """Load a versioned swing-feel prior from ``data/swing_feel.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    return _load_versioned(
        "swing_feel.json", _parse_swing_prior,
        kind="swing-feel", version=version,
        empty_message="swing_feel.json contains no prior tables",
    )


def _parse_succession_weights(payload: dict) -> "SuccessionWeights":
    weights = {str(k): float(v) for k, v in dict(payload["weights"]).items()}
    if not weights:
        raise ValueError(f"Succession weights {payload['version']!r} define no signals")
    return SuccessionWeights(
        version=str(payload["version"]),
        source=str(payload.get("source", "")),
        weights=weights,
    )


def load_succession_weights(version: str | None = None) -> SuccessionWeights:
    """Load a versioned succession-weight table from ``data/succession_weights.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    return _load_versioned(
        "succession_weights.json", _parse_succession_weights,
        kind="succession-weights", version=version,
        empty_message="succession_weights.json contains no weight tables",
    )


def _parse_relative_key_weights(payload: dict) -> "RelativeKeyWeights":
    weights = {str(k): float(v) for k, v in dict(payload["weights"]).items()}
    if not weights:
        raise ValueError(f"Relative-key weights {payload['version']!r} define no signals")
    return RelativeKeyWeights(
        version=str(payload["version"]),
        source=str(payload.get("source", "")),
        weights=weights,
        near_tie_margin=float(payload["near_tie_margin"]),
        decision_margin=float(payload["decision_margin"]),
    )


def load_relative_key_weights(version: str | None = None) -> RelativeKeyWeights:
    """Load a versioned relative-key tie-breaker from ``data/relative_key_weights.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    return _load_versioned(
        "relative_key_weights.json", _parse_relative_key_weights,
        kind="relative-key", version=version,
        empty_message="relative_key_weights.json contains no weight tables",
    )


def _parse_key_smoothing(payload: dict) -> "KeySmoothingPriors":
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
    return priors


def load_key_smoothing(version: str | None = None) -> KeySmoothingPriors:
    """Load a versioned key-region smoothing prior from ``data/key_smoothing.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    return _load_versioned(
        "key_smoothing.json", _parse_key_smoothing,
        kind="key-smoothing", version=version,
        empty_message="key_smoothing.json contains no prior tables",
    )


def _parse_key_inertia(payload: dict) -> "KeyInertiaPriors":
    priors = KeyInertiaPriors(
        version=str(payload["version"]),
        source=str(payload.get("source", "")),
        switch_penalty=float(payload["switch_penalty"]),
    )
    if priors.switch_penalty < 0:
        raise ValueError(
            f"Key inertia {priors.version!r}: switch_penalty must be >= 0"
        )
    return priors


def load_key_inertia(version: str | None = None) -> KeyInertiaPriors:
    """Load a versioned key-inertia prior from ``data/key_inertia.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    return _load_versioned(
        "key_inertia.json", _parse_key_inertia,
        kind="key-inertia", version=version,
        empty_message="key_inertia.json contains no prior tables",
    )


def _parse_scoring_prior(payload: dict) -> "ScoringPrior":
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
    return prior


def load_scoring_prior(version: str | None = None) -> ScoringPrior:
    """Load a versioned induction scoring prior from ``data/scoring_priors.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    return _load_versioned(
        "scoring_priors.json", _parse_scoring_prior,
        kind="scoring-prior", version=version,
        empty_message="scoring_priors.json contains no prior tables",
    )


def _parse_meter_profile(payload: dict) -> "MeterProfileSet":
    profiles = {
        str(sig): tuple(float(w) for w in weights)
        for sig, weights in dict(payload["profiles"]).items()
    }
    if not profiles:
        raise ValueError(f"Meter profile set {payload['version']!r} defines no meters")
    return MeterProfileSet(
        version=str(payload["version"]),
        source=str(payload.get("source", "")),
        grid_beats=float(payload["grid_beats"]),
        profiles=profiles,
    )


def load_meter_profiles(version: str | None = None) -> MeterProfileSet:
    """Load a versioned metric-profile set from ``data/meter_profiles.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    return _load_versioned(
        "meter_profiles.json", _parse_meter_profile,
        kind="meter-profile", version=version,
        empty_message="meter_profiles.json contains no profile sets",
    )


def _parse_structural_key_prior(payload: dict) -> "StructuralKeyPriors":
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
    return priors


def load_structural_key_priors(version: str | None = None) -> StructuralKeyPriors:
    """Load a versioned structural-key prior from ``data/structural_key.json``.

    ``version=None`` returns the first (default) entry. Cached by file mtime.
    """
    return _load_versioned(
        "structural_key.json", _parse_structural_key_prior,
        kind="structural-key", version=version,
        empty_message="structural_key.json contains no prior tables",
    )



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
        When *None* (RE-6b) the base catalog is returned as-is — there is no
        given session (RE-6b): with none, the base catalog is returned.
    """
    scales = dict(_base_scales())
    if session is not None and session.scales:
        for manual in session.scales.values():
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
        merged in.  When *None* (RE-6b) the base catalog is returned as-is.
    """
    qualities = dict(_base_chord_qualities())
    if session is not None and session.chords:
        for manual in session.chords.values():
            if manual.name not in qualities:
                qualities[manual.name] = manual
    return qualities


def chord_qualities_by_mask(
    session: SessionCatalog | None = None,
) -> dict[int, tuple[ChordQuality, ...]]:
    """Chord qualities indexed by mask, one entry per canonical name (aliases
    collapsed) — the lookup `interpret_chord` needs per root (RE-5c).

    Cached on the *base* catalog object (itself mtime-cached) plus a fingerprint
    of the given session's chords, so the per-segment `interpret_chord` path
    stops rebuilding this index (and copying the whole catalog dict) every call.
    ``session=None`` (RE-6b) indexes the base catalog only.
    """
    global _CHORD_MASK_INDEX_CACHE
    session_chords = session.chords if session is not None else {}
    base = _base_chord_qualities()
    session_fingerprint = tuple(sorted(session_chords)) if session_chords else ()
    key = (id(base), session_fingerprint)
    cached = _CHORD_MASK_INDEX_CACHE
    if cached is not None and cached[0] == key:
        return cached[1]

    by_mask: dict[int, list[ChordQuality]] = {}
    seen_names: set[str] = set()
    # Base first (its .values() include alias entries → dedup by name), then any
    # session chords whose name isn't already taken — matching load_chord_qualities.
    for source in (base.values(), session_chords.values() if session_chords else ()):
        for quality in source:
            if quality.name in seen_names:
                continue
            seen_names.add(quality.name)
            by_mask.setdefault(quality.mask, []).append(quality)
    index = {mask: tuple(qs) for mask, qs in by_mask.items()}
    _CHORD_MASK_INDEX_CACHE = (key, index)
    return index


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

    # Cache the default-templates path (the only uncached loader — RE-5b). The
    # full functional table used to regenerate inside per-candidate loops
    # (~2.1 ms per recommend_next_chord). Keyed by the args that shape the
    # output, guarded by the two source files' mtimes like the twelve other
    # loaders. Custom `templates` bypass the cache (rare, tests/CLI only).
    cache_key: tuple | None = None
    if templates is None:
        global _FUNCTION_MAPPINGS_CACHE
        source_mtime = (
            (DATA_DIR / "scales.json").stat().st_mtime_ns,
            (DATA_DIR / "chord_qualities.json").stat().st_mtime_ns,
        )
        cache_key = (mode_key, include_flag, frozenset(feature_set))
        cached = _FUNCTION_MAPPINGS_CACHE
        if cached is not None and cached[0] == source_mtime and cache_key in cached[1]:
            return cached[1][cache_key]

    generated = generate_functions_for_scale(
        scale,
        chord_qualities,
        templates=template_collection,
        enabled_features=feature_set,
        include_nondiatonic=include_flag,
    )

    mappings = [
        FunctionMapping(
            degree_pc=item.degree_pc,
            chord_quality=item.chord_quality,
            intervals=item.intervals,
            role=item.role,
            modal_label=item.modal_label,
            role_subtype=item.role_subtype,
            tags=item.tags,
        )
        for item in generated
    ]
    if cache_key is not None:
        if _FUNCTION_MAPPINGS_CACHE is None or _FUNCTION_MAPPINGS_CACHE[0] != source_mtime:
            _FUNCTION_MAPPINGS_CACHE = (source_mtime, {})
        _FUNCTION_MAPPINGS_CACHE[1][cache_key] = mappings
    return mappings
