"""JSON data loaders for music theory models."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from ..core.bitmask import validate_pc
from ..core.interval import Interval
from ..core.quality import ChordQuality
from ..core.scale import Scale

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class FunctionMapping:
    degree_pc: int
    chord_quality: str
    intervals: Tuple[int, ...]
    role: str
    modal_label: str


def _read_json(name: str) -> Iterable[dict]:
    path = DATA_DIR / name
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"JSON file {name} must contain a list")
    return data


def load_intervals() -> List[Interval]:
    entries: List[Interval] = []
    for payload in _read_json("intervals.json"):
        semitones = int(payload["semitones"])
        validate_pc(semitones)
        entries.append(Interval.from_dict(payload))
    return entries


def load_scales() -> Dict[str, Scale]:
    scales: Dict[str, Scale] = {}
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
        aliases: List[str] = []
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
    return scales


def load_chord_qualities() -> Dict[str, ChordQuality]:
    qualities: Dict[str, ChordQuality] = {}
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
    return qualities


def load_function_mappings(mode: str) -> List[FunctionMapping]:
    filename = {
        "major": "functions_major.json",
        "minor": "functions_minor.json",
    }.get(mode.lower())
    if not filename:
        raise ValueError(f"Unsupported mode: {mode}")

    mappings: List[FunctionMapping] = []
    for payload in _read_json(filename):
        degree_pc = int(payload["degree_pc"])
        validate_pc(degree_pc)
        intervals_field = payload.get("intervals")
        if not isinstance(intervals_field, list) or not intervals_field:
            raise ValueError(f"Function mapping {mode} degree {degree_pc} must define intervals")
        intervals: List[int] = []
        for interval in intervals_field:
            value = int(interval)
            validate_pc(value)
            intervals.append(value)
        mappings.append(
            FunctionMapping(
                degree_pc=degree_pc,
                chord_quality=str(payload["chord_quality"]),
                intervals=tuple(intervals),
                role=str(payload["role"]),
                modal_label=str(payload["modal_label"]),
            )
        )
    return mappings
