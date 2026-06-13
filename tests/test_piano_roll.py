"""Phase 5 slice 2: the piano-roll overlay descriptor."""

from __future__ import annotations

import json

import pytest

from mts.analysis import AnalyticalContext
from mts.core.pitch import Pitch
from mts.io.loaders import load_scales
from mts.representation import piano_roll_descriptor
from mts.temporal import Event, Sequence, track_keys


def _progression():
    """C - F - G - C, one bar each, two voices (bass + a triad top)."""
    events = []
    for i, (root, top) in enumerate(
        [(48, (60, 64, 67)), (53, (60, 65, 69)), (55, (59, 62, 67)), (48, (60, 64, 67))]
    ):
        onset = float(i * 4)
        events.append(Event(onset, 4.0, Pitch.from_midi(root, velocity=90), voice="bass"))
        for m in top:
            events.append(Event(onset, 4.0, Pitch.from_midi(m, velocity=70), voice="top"))
    return Sequence.from_events(events, bpm=120.0)


# --- note geometry (the genuinely new layer) ---------------------------------------------


def test_notes_carry_both_time_bases_and_metadata():
    seq = Sequence.from_events(
        [Event(0.0, 2.0, Pitch.from_midi(60, velocity=80, channel=2), voice="lead")],
        bpm=60.0,  # 1 beat == 1 second
    )
    result = piano_roll_descriptor(seq, chord_overlays=False)
    assert result.spec_level == "registered_time"
    [note] = result.notes
    assert (note.midi, note.pc, note.voice, note.velocity) == (60, 0, "lead", 80)
    assert note.onset_beats == 0.0 and note.duration_beats == 2.0
    assert note.onset_seconds == pytest.approx(0.0)
    assert note.duration_seconds == pytest.approx(2.0)  # 60 bpm


def test_seconds_track_tempo():
    seq = Sequence.from_events(
        [Event(4.0, 2.0, Pitch.from_midi(60))], bpm=120.0  # 2 beats/sec
    )
    [note] = piano_roll_descriptor(seq, chord_overlays=False).notes
    assert note.onset_seconds == pytest.approx(2.0)
    assert note.duration_seconds == pytest.approx(1.0)


def test_pitch_extent_and_duration_reported():
    result = piano_roll_descriptor(_progression(), chord_overlays=False)
    assert result.low_midi == 48
    assert result.high_midi == 69
    assert result.duration_beats == pytest.approx(16.0)
    assert result.duration_seconds == pytest.approx(8.0)  # 16 beats @ 120 bpm


# --- chord-region overlays (reuse the dataset; names cannot diverge) ----------------------


def test_chord_regions_carry_naming_and_span():
    scales = load_scales()
    context = AnalyticalContext(tonic_pc=0, key=scales["Ionian"])
    result = piano_roll_descriptor(_progression(), analytical_context=context)
    assert len(result.chord_regions) == 4
    first = result.chord_regions[0]
    assert first.start_beats == 0.0 and first.end_beats == pytest.approx(4.0)
    assert first.start_seconds == pytest.approx(0.0)
    assert first.root_pc == 0 and first.quality == "maj"  # C major
    assert first.functional_role == "tonic"
    assert first.tonic_pc == 0 and first.key_name == "Ionian"


def test_overlay_names_match_the_dataset_builder():
    from mts.dataset.builders import dataset_from_sequence

    scales = load_scales()
    context = AnalyticalContext(tonic_pc=0, key=scales["Ionian"])
    seq = _progression()
    dataset = dataset_from_sequence(seq, analytical_context=context)
    overlays = piano_roll_descriptor(seq, analytical_context=context).chord_regions
    for record, overlay in zip(dataset.records, overlays):
        chosen = record.analysis.naming.chosen
        assert overlay.root_pc == chosen.interpretation.root_pc
        assert overlay.quality == chosen.interpretation.quality


def test_chord_overlays_can_be_disabled():
    result = piano_roll_descriptor(_progression(), chord_overlays=False)
    assert result.chord_regions == []
    assert result.notes  # notes still present


# --- key-band backdrop (per-region conditioning) ------------------------------------------


def test_key_bands_from_tracking_and_local_conditioning():
    # 16 beats C major then 16 beats F# major (tonic pedals keep it decisive)
    events = []
    for base, tonic in ((0, 60), (16, 66)):
        for cycle in (0, 8):
            events.append(Event(base + cycle, 8, Pitch.from_midi(tonic - 12)))
            for offset, root in ((0, 0), (2, 5), (4, 7), (6, 0)):
                onset = base + cycle + offset
                events += [
                    Event(onset, 2, Pitch.from_midi(tonic + root + iv)) for iv in (0, 4, 7)
                ]
    seq = Sequence.from_events(events)
    regions = track_keys(seq)
    result = piano_roll_descriptor(seq, key_regions=regions)

    assert len(result.key_bands) == len(regions.regions)
    assert result.key_bands[0].tonic_pc == 0
    assert result.key_bands[-1].tonic_pc == 6
    assert result.key_bands[0].mean_margin == pytest.approx(regions.regions[0].mean_margin)

    # overlays conditioned per-region: late F#-region tonic chord names on F#
    late_tonic = [
        r for r in result.chord_regions
        if r.start_beats >= 20 and set(r.pcs) == {6, 10, 1}
    ]
    assert late_tonic and late_tonic[0].root_pc == 6
    assert late_tonic[0].margin is not None


# --- validation + output shape -------------------------------------------------------------


def test_empty_sequence_raises():
    with pytest.raises(ValueError, match="with events"):
        piano_roll_descriptor(Sequence.from_events([]))


def test_to_dict_is_json_ready():
    result = piano_roll_descriptor(_progression())
    payload = json.loads(json.dumps(result.to_dict()))
    assert payload["spec_level"] == "registered_time"
    assert payload["notes"][0]["midi"] == 48
    assert payload["chord_regions"][0]["pcs"]
