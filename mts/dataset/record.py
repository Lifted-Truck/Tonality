"""The enriched dataset record: the unit of analytical output (Phase 3 Slice 4).

A :class:`DatasetRecord` is the reproducible, enriched unit emitted per musical
object/event. It layers the core data-model chain — ``identity`` (always),
``analysis`` (numeric enrichment), optional ``realization`` (register), optional
temporal ``placement`` — and captures, for **reproducibility**, the provenance and
the analytical/display contexts that produced it. A :class:`Dataset` groups records
(a progression, a segmented sequence) with shared context and a temporal summary.

Layering: this package sits *above* ``analysis``, ``temporal``, and ``context`` —
it integrates their typed results into one record, which is exactly why it cannot
live in ``analysis/results.py`` (that leaf must stay numeric/PC-only and may not
import temporal/context). The numeric core stays **canonical**; the ``display``
block is explicitly *derived* and travels with the :class:`DisplayContextSnapshot`
that produced it, so the same input + same context reproduces it byte-for-byte.

**Granularity (Phase 3 Slice 4 decision).** Records are *flat leaves* grouped by a
:class:`Dataset` container — not a recursive record. Forward-compat for an eventual
recursive model is preserved by composition: every record carries a ``kind`` level
discriminator and a stable ``index`` handle, and ``Dataset`` is a *grouping* (not an
asserted flat, non-overlapping partition). A future parent/child *musical* layer
(harmonic segmentation nesting non-harmonic tones; a form/section layer) lands
additively as ``Dataset``-nesting or a ``DatasetRecord.children`` field — never a
leaf-schema teardown. See ROADMAP Phase 3 Slice 4 "reflection point".
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field, replace

from ..analysis.analytical_context import ChordInKey
from ..analysis.results import (
    AnalyticalContextSnapshot,
    ChordAnalysisResult,
    ChordInterpretations,
    ChordNaming,
    ScaleAnalysisResult,
    VoicingAnalysis,
)
from ..context.result_format import ChordAnalysisDisplay
from ..temporal.segmentation import HarmonicRhythm

SCHEMA_VERSION = "1.0"

# Record ``kind`` discriminator — the level a record describes. The set is small
# and open: a future hierarchy (harmony, form) adds entries without a migration.
KIND_OBJECT = "object"    # a timeless identity (a named chord / scale / PC set)
KIND_EVENT = "event"      # a single time-placed event
KIND_SEGMENT = "segment"  # a stable-PC-set span of a sequence


# ---------------------------------------------------------------------------
# Provenance & context snapshots (the reproducibility layer)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceRef:
    """Where a record came from: the original notation and how it parsed.

    ``notation`` is the verbatim input (e.g. ``"Cmaj7"``, ``"[0,4,7]"``,
    ``"60,64,67"``) when known; ``kind`` is the input family (``"chord"`` /
    ``"scale"`` / ``"pcset"`` / ``"midi"`` / ``"sequence"``); ``spec_level`` is the
    lattice label of the parsed input.
    """

    spec_level: str
    notation: str | None = None
    kind: str | None = None


# AnalyticalContextSnapshot moved to mts/analysis/results.py (the naming slice
# labels readings with the context they are conditional on, and analysis may
# not import this layer). Re-exported here unchanged for existing consumers.


@dataclass(frozen=True)
class DisplayContextSnapshot:
    """Frozen capture of the resolved :class:`DisplayContext` settings.

    ``settings`` is the *effective* (layer-resolved) key→value map, so a consumer
    can re-render the spelled ``display`` block deterministically.
    """

    settings: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Record tiers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Identity:
    """The identity key — always present. Numeric/PC-only."""

    mask: int
    pcs: list[int]
    cardinality: int
    spec_level: str


@dataclass(frozen=True)
class RecordAnalysis:
    """The numeric enrichment tier. Each field is present when applicable.

    ``chord`` / ``scale`` are the full single-reading analyses; ``interpretations``
    enumerates every valid naming of the set; ``in_key`` places a (rooted) chord in
    an analytical frame. All numeric — spelling is rendered at the edge.
    """

    chord: ChordAnalysisResult | None = None
    scale: ScaleAnalysisResult | None = None
    interpretations: ChordInterpretations | None = None
    in_key: ChordInKey | None = None
    naming: ChordNaming | None = None  # the chosen reading (Slice 5), context-conditional


@dataclass(frozen=True)
class RealizationRecord:
    """The register tier — present only when the input was register-bearing."""

    midi: list[int]
    voicing: VoicingAnalysis


@dataclass(frozen=True)
class TemporalPlacement:
    """Where a record sits in time — present only for time-based material.

    Beats are quarter-note beats. ``onset_seconds`` / ``duration_seconds`` and the
    metric ``bar`` / ``beat`` are ``None`` when no tempo/meter context was supplied.
    """

    onset_beats: float
    duration_beats: float
    onset_seconds: float | None = None
    duration_seconds: float | None = None
    bar: int | None = None
    beat: float | None = None


# ---------------------------------------------------------------------------
# The record & the container
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DatasetRecord:
    """The enriched, reproducible unit emitted per musical object/event.

    Numeric core (``identity`` / ``analysis`` / ``realization`` / ``placement``) is
    canonical; ``source`` + the two context snapshots + the derived ``display``
    block are the reproducibility/presentation layer that :meth:`minimal` sheds.
    """

    schema_version: str
    kind: str
    identity: Identity
    analysis: RecordAnalysis
    index: int | None = None
    realization: RealizationRecord | None = None
    placement: TemporalPlacement | None = None
    source: SourceRef | None = None
    analytical_context: AnalyticalContextSnapshot | None = None
    display_context: DisplayContextSnapshot | None = None
    display: ChordAnalysisDisplay | None = None

    def minimal(self) -> "DatasetRecord":
        """A copy with provenance/context/display dropped (numeric core only)."""

        return replace(
            self,
            source=None,
            analytical_context=None,
            display_context=None,
            display=None,
        )

    def to_dict(self) -> dict:
        """Plain-dict representation suitable for JSON / MCP serialisation."""

        return dataclasses.asdict(self)


@dataclass(frozen=True)
class TemporalSummary:
    """Sequence-level temporal facts shared by a :class:`Dataset`'s records."""

    tempo_bpm: float | None = None
    time_signature: str | None = None
    harmonic_rhythm: HarmonicRhythm | None = None


@dataclass(frozen=True)
class Dataset:
    """An ordered group of :class:`DatasetRecord`s (a progression / sequence).

    A *grouping*, deliberately **not** asserted to be a flat, non-overlapping,
    exhaustive partition of a timeline — that openness is what lets a future
    recursive/hierarchical model land by composition (see module docstring).
    """

    schema_version: str
    records: list[DatasetRecord]
    analytical_context: AnalyticalContextSnapshot | None = None
    display_context: DisplayContextSnapshot | None = None
    temporal: TemporalSummary | None = None

    def minimal(self) -> "Dataset":
        """A copy with shared context dropped and every record made minimal."""

        return replace(
            self,
            records=[r.minimal() for r in self.records],
            analytical_context=None,
            display_context=None,
        )

    def to_dict(self) -> dict:
        """Plain-dict representation suitable for JSON / MCP serialisation."""

        return dataclasses.asdict(self)


__all__ = [
    "SCHEMA_VERSION",
    "KIND_OBJECT",
    "KIND_EVENT",
    "KIND_SEGMENT",
    "SourceRef",
    "AnalyticalContextSnapshot",
    "DisplayContextSnapshot",
    "Identity",
    "RecordAnalysis",
    "RealizationRecord",
    "TemporalPlacement",
    "DatasetRecord",
    "TemporalSummary",
    "Dataset",
]
