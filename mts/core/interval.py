"""Interval models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Interval:
    semitones: int
    name: str
    verbal: str
    diatonic_class: str
    quality: str
    inversion: int
    cents: Optional[float]
    ratio: Optional[str]
    category: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Interval":
        return cls(
            semitones=int(data["semitones"]),
            name=str(data["name"]),
            verbal=str(data["verbal"]),
            diatonic_class=str(data["diatonic_class"]),
            quality=str(data["quality"]),
            inversion=int(data["inversion"]),
            cents=(float(data["cents"]) if data.get("cents") is not None else None),
            ratio=(str(data["ratio"]) if data.get("ratio") is not None else None),
            category=(str(data["category"]) if data.get("category") is not None else None),
        )
