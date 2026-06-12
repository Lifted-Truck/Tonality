"""Performed-input tolerance (gap 12): onset coalescing + grid snap, opt-in."""

from __future__ import annotations

import json

import pytest

from mts.core.pitch import Pitch
from mts.temporal import Event, Sequence, analyze_rhythm, coalesce, segment


def _humanized_chords():
    """The theory-review probe: two chords with ~5 ms jitter at 120 bpm."""
    return Sequence.from_events([
        Event(0.0, 2.0, Pitch.from_midi(60)), Event(0.013, 1.99, Pitch.from_midi(64)),
        Event(0.021, 1.98, Pitch.from_midi(67)),
        Event(2.0, 2.0, Pitch.from_midi(65)), Event(2.008, 1.99, Pitch.from_midi(69)),
        Event(2.017, 1.98, Pitch.from_midi(72)),
    ])


# --- the acceptance case: the review's verified misreadings, repaired -------------------


def test_humanized_chords_segment_cleanly_after_coalescing():
    raw = _humanized_chords()
    assert len(segment(raw)) == 10  # the review finding, still true on raw input
    cleaned = coalesce(raw, onset_window_beats=0.05)
    segments = segment(cleaned.sequence)
    assert len(segments) == 2
    assert [s.pcs for s in segments] == [(0, 4, 7), (0, 5, 9)]
    # four jittered notes moved, plus the exact note whose offset joined its
    # cluster's (earliest) anchor — anchor semantics apply to every member
    assert cleaned.moved_events == 5
    assert cleaned.max_shift_beats == pytest.approx(0.021)
    assert cleaned.dropped == []


def test_humanized_melody_places_on_the_beat_after_coalescing():
    raw = Sequence.from_events([
        Event(0.013, 0.5, Pitch.from_midi(60)),
        Event(1.008, 0.5, Pitch.from_midi(62)),
        Event(2.01, 0.5, Pitch.from_midi(64)),
    ])
    assert analyze_rhythm(raw).placements == ["subdivision"] * 3
    cleaned = coalesce(raw, onset_window_beats=0.0, snap_grid_beats=0.25)
    assert analyze_rhythm(cleaned.sequence).placements == ["downbeat", "beat", "beat"]


# --- mechanics ---------------------------------------------------------------------------


def test_offsets_coalesce_too_healing_legato_seams():
    raw = Sequence.from_events([
        Event(0.0, 1.99, Pitch.from_midi(60)),   # ends just short of beat 2
        Event(2.008, 1.0, Pitch.from_midi(62)),  # starts just after
    ])
    cleaned = coalesce(raw, onset_window_beats=0.05)
    first, second = cleaned.sequence.events
    assert first.offset == pytest.approx(second.onset)  # seam healed


def test_anchor_is_the_earliest_point_and_chains_do_not_extend():
    raw = Sequence.from_events([
        Event(0.00, 1.0, Pitch.from_midi(60)),
        Event(0.04, 1.0, Pitch.from_midi(64)),  # within window of anchor 0.0
        Event(0.07, 1.0, Pitch.from_midi(67)),  # within 0.04's window but NOT anchor's
    ])
    cleaned = coalesce(raw, onset_window_beats=0.05)
    onsets = [e.onset for e in cleaned.sequence.events]
    assert onsets == [0.0, 0.0, 0.07]  # no unbounded chaining


def test_grace_note_shorter_than_window_is_dropped_and_reported():
    raw = Sequence.from_events([
        Event(0.0, 2.0, Pitch.from_midi(60)),
        Event(0.01, 0.02, Pitch.from_midi(59)),  # collapses to nothing
    ])
    cleaned = coalesce(raw, onset_window_beats=0.05)
    assert len(cleaned.sequence.events) == 1
    [lost] = cleaned.dropped
    assert (lost.midi, lost.onset) == (59, 0.01)


def test_voice_velocity_and_maps_survive():
    raw = Sequence.from_events(
        [Event(0.01, 1.0, Pitch.from_midi(60, velocity=99, channel=3), voice="lead")],
        bpm=90.0,
    )
    cleaned = coalesce(raw, onset_window_beats=0.05, snap_grid_beats=0.5)
    [event] = cleaned.sequence.events
    assert (event.voice, event.pitch.velocity, event.pitch.channel) == ("lead", 99, 3)
    assert cleaned.sequence.tempo == raw.tempo


def test_exact_input_passes_through_untouched():
    raw = Sequence.from_events([Event(0.0, 1.0, Pitch.from_midi(60)),
                                Event(1.0, 1.0, Pitch.from_midi(62))])
    cleaned = coalesce(raw, onset_window_beats=0.05)
    assert cleaned.sequence.events == raw.events
    assert cleaned.moved_events == 0
    assert cleaned.max_shift_beats == 0.0


def test_parameter_validation():
    raw = Sequence.from_events([Event(0.0, 1.0, Pitch.from_midi(60))])
    with pytest.raises(ValueError, match=">= 0"):
        coalesce(raw, onset_window_beats=-0.1)
    with pytest.raises(ValueError, match="positive"):
        coalesce(raw, onset_window_beats=0.05, snap_grid_beats=0.0)
    with pytest.raises(ValueError, match="Nothing to do"):
        coalesce(raw, onset_window_beats=0.0)


def test_result_metadata_is_json_ready_and_cites_parameters():
    cleaned = coalesce(_humanized_chords(), onset_window_beats=0.05)
    payload = json.loads(json.dumps(cleaned.to_dict()))
    assert payload["onset_window_beats"] == 0.05
    assert payload["snap_grid_beats"] is None
    assert payload["moved_events"] == 5
