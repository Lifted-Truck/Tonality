"""Tests for the Phase 3 Slice 4 dataset record schema (``mts.dataset``)."""

import json

import pytest

from mts.analysis.analytical_context import AnalyticalContext
from mts.context.context import DisplayContext
from mts.core.chord import Chord
from mts.core.pitch import Pitch
from mts.core.realization import Realization
from mts.dataset import (
    SCHEMA_VERSION,
    Dataset,
    DatasetRecord,
    dataset_from_sequence,
    record_from_chord,
    record_from_segment,
)
from mts.dataset.record import (
    KIND_OBJECT,
    KIND_SEGMENT,
    SourceRef,
)
from mts.io.loaders import load_chord_qualities, load_scales
from mts.temporal.segmentation import segment
from mts.temporal.sequence import Event, Sequence


def _cmaj7() -> Chord:
    return Chord.from_quality(0, load_chord_qualities()["maj7"])


def _ev(midi, onset, dur):
    return Event(onset, dur, Pitch.from_midi(midi))


# --- record_from_chord: identity + analysis (the always-present core) -------

def test_chord_record_core_is_numeric_and_complete():
    rec = record_from_chord(_cmaj7())
    assert rec.schema_version == SCHEMA_VERSION
    assert rec.kind == KIND_OBJECT
    assert rec.identity.mask == _cmaj7().mask
    assert rec.identity.pcs == [0, 4, 7, 11]
    assert rec.identity.cardinality == 4
    # Analysis tier populated for a rooted chord identity.
    assert rec.analysis.chord is not None
    assert rec.analysis.chord.root_pc == 0
    assert rec.analysis.interpretations is not None
    # No register / temporal / context supplied -> those tiers are absent.
    assert rec.realization is None
    assert rec.placement is None
    assert rec.analytical_context is None
    assert rec.display_context is None
    assert rec.display is None


def test_chord_record_is_json_serialisable():
    rec = record_from_chord(_cmaj7())
    blob = json.dumps(rec.to_dict())
    assert "interpretations" in blob


# --- the register tier ------------------------------------------------------

def test_chord_record_with_realization_adds_register_tier():
    real = Realization.from_midi([48, 52, 55, 59], root_pc=0)  # C maj7 voicing
    rec = record_from_chord(_cmaj7(), realization=real)
    assert rec.realization is not None
    assert rec.realization.midi == [48, 52, 55, 59]
    assert rec.realization.voicing.bass_midi == 48
    assert rec.realization.voicing.rooted is True


# --- the analytical context tier (in_key placement) -------------------------

def test_chord_record_in_key_requires_tonal_center():
    cmajor = load_scales()["Ionian"]
    ctx = AnalyticalContext(tonic_pc=0, key=cmajor)
    rec = record_from_chord(_cmaj7(), analytical_context=ctx)
    assert rec.analysis.in_key is not None
    assert rec.analysis.in_key.is_diatonic is True
    assert rec.analytical_context.tonic_pc == 0
    assert rec.analytical_context.key_name == "Ionian"
    assert rec.analytical_context.key_degrees == list(cmajor.degrees)


def test_chord_record_without_tonic_has_no_in_key():
    ctx = AnalyticalContext()  # empty frame
    rec = record_from_chord(_cmaj7(), analytical_context=ctx)
    assert rec.analysis.in_key is None


# --- the display (derived) tier + reproducibility ---------------------------

def test_display_block_rendered_and_context_snapshotted():
    disp = DisplayContext()
    disp.set("spelling", "flats")
    rec = record_from_chord(_cmaj7(), display_context=disp)
    assert rec.display is not None
    assert rec.display.root_name  # spelled
    # The snapshot captures the effective setting so the block reproduces.
    assert rec.display_context.settings["spelling"] == "flats"


def test_record_is_reproducible():
    disp = DisplayContext()
    a = record_from_chord(_cmaj7(), display_context=disp)
    b = record_from_chord(_cmaj7(), display_context=disp)
    assert a.to_dict() == b.to_dict()


# --- minimal() projection ---------------------------------------------------

def test_minimal_sheds_provenance_keeps_numeric_core():
    disp = DisplayContext()
    ctx = AnalyticalContext(tonic_pc=0)
    full = record_from_chord(
        _cmaj7(),
        analytical_context=ctx,
        display_context=disp,
        source=SourceRef(spec_level="named chord", notation="Cmaj7", kind="chord"),
    )
    lean = full.minimal()
    # numeric core preserved
    assert lean.identity == full.identity
    assert lean.analysis == full.analysis
    # reproducibility/presentation layer dropped
    assert lean.source is None
    assert lean.analytical_context is None
    assert lean.display_context is None
    assert lean.display is None


# --- segment & sequence builders (the temporal tier) ------------------------

def _two_chord_sequence() -> Sequence:
    return Sequence.from_events(
        [
            _ev(60, 0, 2), _ev(64, 0, 2), _ev(67, 0, 2),   # C major, bar 1
            _ev(62, 2, 2), _ev(65, 2, 2), _ev(69, 2, 2),   # D minor, beats 3-4
        ]
    )


def test_segment_record_has_placement_and_rootless_identity():
    seq = _two_chord_sequence()
    segs = segment(seq)
    rec = record_from_segment(segs[0], sequence=seq, index=0)
    assert rec.kind == KIND_SEGMENT
    assert rec.index == 0
    # rootless PC-set identity -> namings enumerated, no single rooted chord
    assert rec.analysis.interpretations is not None
    assert rec.analysis.chord is None
    # register tier present (the segment's representative voicing)
    assert rec.realization is not None
    # temporal placement, enriched from the sequence
    assert rec.placement.onset_beats == 0.0
    assert rec.placement.duration_beats == 2.0
    assert rec.placement.bar == 0
    assert rec.placement.onset_seconds == 0.0


def test_segment_record_without_sequence_has_beat_only_placement():
    seq = _two_chord_sequence()
    seg = segment(seq)[0]
    rec = record_from_segment(seg)  # no sequence -> no seconds/metre
    assert rec.placement.onset_seconds is None
    assert rec.placement.bar is None
    assert rec.placement.duration_beats == 2.0


def test_dataset_from_sequence_groups_records_with_temporal_summary():
    seq = _two_chord_sequence()
    ds = dataset_from_sequence(seq)
    assert isinstance(ds, Dataset)
    assert len(ds.records) == 2
    assert [r.index for r in ds.records] == [0, 1]
    assert ds.temporal is not None
    assert ds.temporal.tempo_bpm == 120.0
    assert ds.temporal.time_signature == "4/4"
    assert ds.temporal.harmonic_rhythm.segment_count == 2


def test_dataset_is_json_serialisable_and_minimal_projects():
    seq = _two_chord_sequence()
    ds = dataset_from_sequence(seq, display_context=DisplayContext())
    json.dumps(ds.to_dict())  # must not raise
    lean = ds.minimal()
    assert lean.display_context is None
    assert all(r.display_context is None for r in lean.records)
    assert len(lean.records) == len(ds.records)
