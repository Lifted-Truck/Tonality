"""Rhythmic atoms (Phase 4.6 WS0): metric placement, syncopation, durations/IOIs."""

from __future__ import annotations

import json

import pytest

from mts.core.pitch import Pitch
from mts.temporal import (
    Event,
    MeterChange,
    MeterMap,
    Sequence,
    TimeSignature,
    analyze_rhythm,
)
from mts.temporal.rhythmic import beat_unit_of


def _seq(notes, *, time_signature=(4, 4), meter=None):
    """notes: (onset, duration) tuples; pitch is irrelevant to rhythm."""
    events = [Event(o, d, Pitch.from_midi(60)) for o, d in notes]
    if meter is not None:
        return Sequence.from_events(events, meter=meter)
    return Sequence.from_events(events, time_signature=time_signature)


# --- beat unit (the felt beat) ----------------------------------------------------------


def test_beat_unit_simple_and_compound():
    assert beat_unit_of(TimeSignature(4, 4)) == 1.0
    assert beat_unit_of(TimeSignature(3, 4)) == 1.0  # 3/4 is simple
    assert beat_unit_of(TimeSignature(2, 2)) == 2.0
    assert beat_unit_of(TimeSignature(6, 8)) == 1.5  # dotted quarter
    assert beat_unit_of(TimeSignature(9, 8)) == 1.5
    assert beat_unit_of(TimeSignature(12, 8)) == 1.5
    assert beat_unit_of(TimeSignature(6, 4)) == 3.0  # two dotted halves


# --- metric placement -------------------------------------------------------------------


def test_placement_classes_in_common_time():
    result = analyze_rhythm(
        _seq([(0.0, 0.25), (1.0, 0.25), (1.5, 0.25), (1.75, 0.25)])
    )
    assert result.placements == ("downbeat", "beat", "offbeat", "subdivision")


def test_placement_uses_the_compound_felt_beat():
    result = analyze_rhythm(
        _seq([(0.0, 0.25), (1.5, 0.25), (0.75, 0.25), (0.5, 0.25)], time_signature=(6, 8))
    )
    by_onset = {n.onset: n.placement for n in result.notes}
    assert by_onset[0.0] == "downbeat"
    assert by_onset[1.5] == "beat"        # the second dotted-quarter beat
    assert by_onset[0.75] == "offbeat"    # half of the felt beat
    assert by_onset[0.5] == "subdivision"  # an eighth — finer than the half-beat


def test_placement_across_bars_and_meter_changes():
    meter = MeterMap(
        (MeterChange(0, TimeSignature(4, 4)), MeterChange(1, TimeSignature(3, 4)))
    )
    result = analyze_rhythm(_seq([(4.0, 0.5), (5.0, 0.5)], meter=meter))
    assert result.notes[0].bar == 1
    assert result.notes[0].placement == "downbeat"  # bar 1 starts at beat 4
    assert result.notes[1].placement == "beat"
    assert result.notes[1].beat_unit == 1.0


# --- syncopation ------------------------------------------------------------------------


def test_offbeat_held_through_the_beat_line_is_syncopated():
    held = analyze_rhythm(_seq([(0.5, 1.0)]))
    assert held.notes[0].is_syncopated is True
    short = analyze_rhythm(_seq([(0.5, 0.5)]))
    assert short.notes[0].is_syncopated is False  # resolves at the beat line


def test_weak_beat_held_through_the_downbeat_is_syncopated():
    held = analyze_rhythm(_seq([(3.0, 2.0)]))  # beat 4 of 4/4, into the next bar
    assert held.notes[0].is_syncopated is True
    contained = analyze_rhythm(_seq([(3.0, 1.0)]))
    assert contained.notes[0].is_syncopated is False


def test_downbeats_are_never_syncopated():
    result = analyze_rhythm(_seq([(0.0, 6.0)]))  # held across the bar line
    assert result.notes[0].is_syncopated is False


def test_charleston_figure_counts_one_syncopation():
    # dotted-quarter + eighth-tied figure: onset 1.5 held through beat 2
    result = analyze_rhythm(_seq([(0.0, 1.5), (1.5, 2.5)]))
    assert result.placements == ("downbeat", "offbeat")
    assert result.syncopation_count == 1
    assert result.notes[1].is_syncopated is True


# --- durations and IOIs -----------------------------------------------------------------


def test_durations_and_inter_onset_intervals():
    result = analyze_rhythm(_seq([(0.0, 0.5), (1.0, 1.0), (3.0, 1.0)]))
    assert result.durations == (0.5, 1.0, 1.0)
    assert result.iois == (1.0, 2.0)
    assert result.notes[0].ioi_to_next == 1.0
    assert result.notes[-1].ioi_to_next is None


# --- line discipline (shared with melodic atoms) ------------------------------------------


def test_multi_voice_requires_an_explicit_voice():
    events = [
        Event(0, 1, Pitch.from_midi(60), voice="a"),
        Event(0, 1, Pitch.from_midi(67), voice="b"),
    ]
    seq = Sequence.from_events(events)
    with pytest.raises(ValueError, match="pass voice="):
        analyze_rhythm(seq)
    assert analyze_rhythm(seq, voice="a").notes[0].midi == 60


def test_overlapping_notes_are_not_a_line():
    with pytest.raises(ValueError, match="monophonic"):
        analyze_rhythm(_seq([(0.0, 2.0), (1.0, 2.0)]))


# --- output shape -------------------------------------------------------------------------


def test_to_dict_is_json_ready():
    result = analyze_rhythm(_seq([(0.0, 1.5), (1.5, 2.5)]))
    payload = json.loads(json.dumps(result.to_dict()))
    assert payload["syncopation_count"] == 1
    assert payload["notes"][1]["placement"] == "offbeat"
    assert payload["notes"][1]["beat_unit"] == 1.0
