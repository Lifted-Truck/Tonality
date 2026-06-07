"""mts.dataset — the enriched dataset record (Phase 3 Slice 4).

The unit-of-record layer: it integrates ``analysis`` + ``temporal`` + ``context``
typed results into one reproducible :class:`DatasetRecord` (and a :class:`Dataset`
container). Sits *above* those layers — see ``record.py`` for the schema and the
flat-vs-recursive granularity decision, ``builders.py`` for assembly.
"""

from __future__ import annotations

from .builders import (
    dataset_from_sequence,
    record_from_chord,
    record_from_segment,
)
from .record import (
    SCHEMA_VERSION,
    AnalyticalContextSnapshot,
    Dataset,
    DatasetRecord,
    DisplayContextSnapshot,
    Identity,
    RealizationRecord,
    RecordAnalysis,
    SourceRef,
    TemporalPlacement,
    TemporalSummary,
)

__all__ = [
    "SCHEMA_VERSION",
    "AnalyticalContextSnapshot",
    "Dataset",
    "DatasetRecord",
    "DisplayContextSnapshot",
    "Identity",
    "RealizationRecord",
    "RecordAnalysis",
    "SourceRef",
    "TemporalPlacement",
    "TemporalSummary",
    "dataset_from_sequence",
    "record_from_chord",
    "record_from_segment",
]
