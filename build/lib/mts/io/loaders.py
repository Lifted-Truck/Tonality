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
from ..analysis.builders import SESSION_SCALES, SESSION_CHORDS
from ..theory.functions import (
    DEFAULT_FEATURES_MAJOR,
    DEFAULT_FEATURES_MINOR,
    TEMPLATES_MAJOR,
    TEMPLATES_MINOR,
    FunctionTemplate,
    generate_functions_for_scale,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class FunctionMapping:
    degree_pc: int
    chord_quality: str
    intervals: tuple[int, ...]
    role: str
    modal_label: str
    tags: tuple[str, ...] = ()


def _read_json(name: str) -> list[dict]:
    path = DATA_DIR / name
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"JSON file {name} must contain a list")
    return data


def load_intervals() -> list[Interval]:
    entries: list[Interval] = []
    for payload in _read_json("intervals.json"):
        semitones = int(payload["semitones"])
        validate_pc(semitones)
        entries.append(Interval.from_dict(payload))
    return entries


def load_scales() -> dict[str, Scale]:
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
    if SESSION_SCALES:
        for manual in SESSION_SCALES.values():
            if manual.name not in scales:
                scales[manual.name] = manual
    return scales


def load_chord_qualities() -> dict[str, ChordQuality]:
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
        qualities[name] = ChordQuality.from_intervals(name, intervals, tensions)
    if SESSION_CHORDS:
        for manual in SESSION_CHORDS.values():
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

    The default strategy ("dynamic") uses the theory generator introduced in
    mts/theory/functions.py. Pass strategy="static" only if you need to load
    the legacy JSON tables in data/functions_major.json or data/functions_minor.json.
    """

    mode_key = mode.lower()
    if strategy not in {"dynamic", "static"}:
        raise ValueError(f"Unsupported strategy: {strategy}")

    if strategy == "static":
        raise ValueError(
            "Static function tables are deprecated. "
            "Use strategy='dynamic' with appropriate features/templates instead."
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
