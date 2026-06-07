"""Temporal layer: time-bearing events/sequences over the identity model.

Sits above ``core`` and ``analysis`` (it references them; they do not reference
it). Canonical time unit is the quarter-note beat. The chain is
**event → realization → identity key** (ROADMAP Decision 2): read the pitches
sounding across a window as a ``Realization`` and reduce to a key.
"""

from __future__ import annotations

from .tempo import TempoChange, TempoMap
from .meter import TimeSignature, MetricPosition, MeterChange, MeterMap
from .sequence import Event, Sequence

__all__ = [
    "TempoChange",
    "TempoMap",
    "TimeSignature",
    "MetricPosition",
    "MeterChange",
    "MeterMap",
    "Event",
    "Sequence",
]
