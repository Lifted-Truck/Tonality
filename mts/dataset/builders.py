"""Builders: assemble :class:`DatasetRecord` / :class:`Dataset` from objects.

These are the integration points — they call the existing typed-analysis entry
points (``analyze_chord``, ``analyze_voicing``, ``interpret_chord``,
``contextualize_chord``, ``segment`` / ``harmonic_rhythm``) and the display-edge
formatter, then nest the results into a record. Nothing new is *computed* here; the
builders only *assemble* and capture context for reproducibility.

Each builder takes optional ``analytical_context`` (numeric tonal frame) and
``display_context`` (spelling/label choices). When a display context is supplied,
the derived spelled ``display`` block is rendered and the context is snapshotted
alongside it so the record reproduces.
"""

from __future__ import annotations

from ..analysis.analytical_context import AnalyticalContext, contextualize_chord
from ..analysis.chord_analysis import (
    ChordAnalysisRequest,
    analyze_chord,
    analyze_voicing,
)
from ..analysis.equivalence import interpret_chord
from ..analysis.naming import name_chord
from ..context.context import DisplayContext
from ..context.result_format import format_chord_analysis
from ..core.chord import Chord
from ..core.realization import Realization
from ..core.spec_level import SpecLevel
from ..temporal.segmentation import Segment, harmonic_rhythm, segment
from ..temporal.sequence import Sequence
from .record import (
    SCHEMA_VERSION,
    KIND_OBJECT,
    KIND_SEGMENT,
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

_EPS = 1e-9


# ---------------------------------------------------------------------------
# Snapshot helpers (capture context for reproducibility)
# ---------------------------------------------------------------------------

def _snapshot_analytical(
    context: AnalyticalContext | None,
) -> AnalyticalContextSnapshot | None:
    if context is None:
        return None
    return AnalyticalContextSnapshot(
        tonic_pc=context.tonic_pc,
        key_name=context.key.name if context.key is not None else None,
        key_degrees=list(context.key.degrees) if context.key is not None else None,
    )


def _resolve_display_settings(context: DisplayContext) -> dict:
    """The *effective* (layer-resolved) settings across all layers."""

    keys: set[str] = set()
    for layer in context._layers:  # resolved snapshot of the full key space
        keys.update(layer.settings.keys())
    return {key: context.get(key) for key in sorted(keys)}


def _snapshot_display(
    context: DisplayContext | None,
) -> DisplayContextSnapshot | None:
    if context is None:
        return None
    return DisplayContextSnapshot(settings=_resolve_display_settings(context))


# ---------------------------------------------------------------------------
# Record builders
# ---------------------------------------------------------------------------

def record_from_chord(
    chord: Chord,
    *,
    realization: Realization | None = None,
    analytical_context: AnalyticalContext | None = None,
    display_context: DisplayContext | None = None,
    source: SourceRef | None = None,
    include_inversions: bool = True,
    index: int | None = None,
) -> DatasetRecord:
    """Build an ``object``-kind record for a rooted chord identity.

    Always populates identity + chord analysis + every valid naming. Adds the
    register tier when ``realization`` is given, the ``in_key`` placement when the
    analytical context carries a tonal center, and the spelled ``display`` block
    when a display context is supplied.
    """

    tonic_pc = analytical_context.tonic_pc if analytical_context is not None else None

    chord_result = analyze_chord(
        ChordAnalysisRequest(
            chord=chord,
            tonic_pc=tonic_pc,
            include_inversions=include_inversions,
        )
    )
    interpretations = interpret_chord(chord.pcs)

    in_key = None
    if analytical_context is not None and analytical_context.has_tonic:
        in_key = contextualize_chord(chord, analytical_context)

    analysis = RecordAnalysis(
        chord=chord_result,
        interpretations=interpretations,
        in_key=in_key,
        naming=name_chord(chord, analytical_context, realization=realization),
    )

    realization_record = None
    if realization is not None:
        voicing = analyze_voicing(realization)
        realization_record = RealizationRecord(
            midi=[p.midi for p in realization.pitches],
            voicing=voicing,
        )

    display = None
    if display_context is not None:
        display = format_chord_analysis(chord_result, display_context)

    return DatasetRecord(
        schema_version=SCHEMA_VERSION,
        kind=KIND_OBJECT,
        index=index,
        identity=Identity(
            mask=chord.mask,
            pcs=list(chord.pcs),
            cardinality=len(set(chord.pcs)),
            spec_level=SpecLevel.NAMED_CHORD.label,
        ),
        analysis=analysis,
        realization=realization_record,
        source=source,
        analytical_context=_snapshot_analytical(analytical_context),
        display_context=_snapshot_display(display_context),
        display=display,
    )


def record_from_segment(
    seg: Segment,
    *,
    sequence: Sequence | None = None,
    analytical_context: AnalyticalContext | None = None,
    display_context: DisplayContext | None = None,
    source: SourceRef | None = None,
    index: int | None = None,
) -> DatasetRecord:
    """Build a ``segment``-kind record from a temporal :class:`Segment`.

    A segment is a *rootless* PC-set span: its identity enumerates namings
    (``interpret_chord``), and ``naming`` carries the contextually-chosen
    reading (Slice 5) — conditional on the supplied analytical context, or an
    intrinsic-only ranking when none is given. The segment's representative
    realization is a rootless voicing template, analysed register-aware. When
    ``sequence`` is given, the placement is enriched with seconds and metric
    bar/beat.
    """

    placement = _placement_for_span(seg.start, seg.duration_beats, sequence)
    voicing = analyze_voicing(seg.realization)

    return DatasetRecord(
        schema_version=SCHEMA_VERSION,
        kind=KIND_SEGMENT,
        index=index,
        identity=Identity(
            mask=seg.mask,
            pcs=list(seg.pcs),
            cardinality=len(set(seg.pcs)),
            spec_level=SpecLevel.INTERVAL_SHAPE.label,
        ),
        analysis=RecordAnalysis(
            interpretations=seg.interpret(),
            naming=name_chord(seg.pcs, analytical_context, realization=seg.realization),
        ),
        realization=RealizationRecord(
            midi=[p.midi for p in seg.realization.pitches],
            voicing=voicing,
        ),
        placement=placement,
        source=source,
        analytical_context=_snapshot_analytical(analytical_context),
        display_context=_snapshot_display(display_context),
    )


def _placement_for_span(
    onset_beats: float,
    duration_beats: float,
    sequence: Sequence | None,
) -> TemporalPlacement:
    """A :class:`TemporalPlacement`, enriched with seconds/metre if a sequence is given."""

    if sequence is None:
        return TemporalPlacement(onset_beats=onset_beats, duration_beats=duration_beats)

    end_beats = onset_beats + duration_beats
    onset_seconds = sequence.seconds_at(onset_beats)
    duration_seconds = sequence.seconds_at(end_beats) - onset_seconds
    metric = sequence.metric_position(onset_beats)
    return TemporalPlacement(
        onset_beats=onset_beats,
        duration_beats=duration_beats,
        onset_seconds=onset_seconds,
        duration_seconds=duration_seconds,
        bar=metric.bar,
        beat=metric.beat_in_bar,
    )


# ---------------------------------------------------------------------------
# Dataset builder
# ---------------------------------------------------------------------------

def dataset_from_sequence(
    sequence: Sequence,
    *,
    analytical_context: AnalyticalContext | None = None,
    display_context: DisplayContext | None = None,
    source: SourceRef | None = None,
) -> Dataset:
    """Segment ``sequence`` into a :class:`Dataset` of ``segment``-kind records.

    Records carry their stable ``index``; the dataset's ``temporal`` summary holds
    the starting tempo/meter and the harmonic-rhythm metrics.
    """

    segments = segment(sequence)
    records = [
        record_from_segment(
            seg,
            sequence=sequence,
            analytical_context=analytical_context,
            display_context=display_context,
            index=i,
        )
        for i, seg in enumerate(segments)
    ]

    signature = sequence.meter.changes[0].signature
    temporal = TemporalSummary(
        tempo_bpm=sequence.tempo.bpm_at(0.0),
        time_signature=f"{signature.numerator}/{signature.denominator}",
        harmonic_rhythm=harmonic_rhythm(sequence),
    )

    return Dataset(
        schema_version=SCHEMA_VERSION,
        records=records,
        analytical_context=_snapshot_analytical(analytical_context),
        display_context=_snapshot_display(display_context),
        temporal=temporal,
    )


__all__ = [
    "record_from_chord",
    "record_from_segment",
    "dataset_from_sequence",
]
