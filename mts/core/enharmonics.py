"""Enharmonic naming utilities."""

from __future__ import annotations

from typing import Dict, List

PC_TO_NAMES: Dict[int, List[str]] = {
    0: ["C", "B#", "Dbb"],
    1: ["C#", "Db"],
    2: ["D", "C##", "Ebb"],
    3: ["D#", "Eb", "Fbb"],
    4: ["E", "Fb", "D##"],
    5: ["F", "E#", "Gbb"],
    6: ["F#", "Gb", "E##"],
    7: ["G", "F##", "Abb"],
    8: ["G#", "Ab"],
    9: ["A", "G##", "Bbb"],
    10: ["A#", "Bb", "Cbb"],
    11: ["B", "Cb", "A##"],
}


def primary_name(pc: int) -> str:
    names = PC_TO_NAMES.get(pc)
    if not names:
        raise ValueError(f"No enharmonic names for pitch class {pc}")
    return names[0]
