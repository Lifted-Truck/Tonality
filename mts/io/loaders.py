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

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Parsed base catalogs, cached per (path, mtime). Catalog objects are frozen
# dataclasses, so sharing them across the dicts returned to callers is safe;
# the JSON is re-read only when the file changes on disk.
_BASE_SCALES_CACHE: tuple[Path, int, dict[str, Scale]] | None = None
_BASE_QUALITIES_CACHE: tuple[Path, int, dict[str, ChordQuality]] | None = None
_KEY_PROFILES_CACHE: tuple[Path, int, tuple["KeyProfileSet", ...]] | None = None


@dataclass(frozen=True)
class FunctionMapping:
    degree_pc: int
    chord_quality: str
    intervals: tuple[int, ...]
    role: str
    modal_label: str
    tags: tuple[str, ...] = ()


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
