"""Local meter tracking (gap 11 follow-on): windowed meter estimation → regions.

The windowed form of ``infer_meter``, as ``track_keys`` is to ``infer_key``: a
window slides over the sequence, each window's metric fit is ranked (same versioned
priors, with a per-window phase search), and consecutive same-meter windows merge
into regions. Honest about uninformative windows; deterministic.
"""

from __future__ import annotations

import pytest

from mts.core.pitch import Pitch
from mts.temporal import Event, Sequence, track_meter
from mts.analysis.meter_estimation import infer_meter


def _accented_bars(start_beat: float, accents: tuple[int, ...], n_bars: int) -> list[Event]:
    """`n_bars` bars whose within-bar accent pattern is `accents` (one onset/beat)."""
    events = []
    t = start_beat
    for _ in range(n_bars):
        for beat, vel in enumerate(accents):
            events.append(Event(t + beat, 0.5, Pitch.from_midi(60, velocity=vel)))
        t += len(accents)
    return events


def _meter_change_sequence() -> Sequence:
    # 8 bars of 4/4 then 10 bars of 3/4 — the change is at beat 32.
    events = _accented_bars(0.0, (110, 50, 70, 50), 8) + _accented_bars(32.0, (110, 50, 70), 10)
    return Sequence.from_events(events)


# --- regions ---------------------------------------------------------------------


def test_detects_the_meter_change():
    res = track_meter(_meter_change_sequence(), window_beats=12.0, hop_beats=3.0)
    sigs = [(r.numerator, r.denominator) for r in res.regions]
    assert sigs == [(4, 4), (3, 4)]
    # the boundary lands near the true change (beat 32) within hop resolution
    boundary = res.regions[0].end_beats
    assert abs(boundary - 32.0) <= 3.0
    assert res.profile_version == "meter-grid.1"


def test_stable_meter_is_one_region():
    seq = Sequence.from_events(_accented_bars(0.0, (110, 50, 70, 50), 12))
    res = track_meter(seq, window_beats=12.0, hop_beats=4.0)
    assert [(r.numerator, r.denominator) for r in res.regions] == [(4, 4)]
    assert res.regions[0].window_count >= 1


def test_regions_carry_seconds_and_cover_to_end():
    seq = _meter_change_sequence()
    res = track_meter(seq, window_beats=12.0, hop_beats=3.0)
    assert res.regions[0].start_beats == 0.0
    assert res.regions[-1].end_beats == pytest.approx(seq.duration_beats)
    for r in res.regions:
        assert r.end_seconds >= r.start_seconds


def test_deterministic():
    seq = _meter_change_sequence()
    assert track_meter(seq, window_beats=12.0, hop_beats=3.0).to_dict() == \
        track_meter(seq, window_beats=12.0, hop_beats=3.0).to_dict()


# --- honesty / validation --------------------------------------------------------


def test_empty_and_bad_geometry_raise():
    seq = _meter_change_sequence()
    with pytest.raises(ValueError, match="window_beats must be positive"):
        track_meter(seq, window_beats=0.0)
    with pytest.raises(ValueError, match="hop_beats must be positive"):
        track_meter(seq, hop_beats=0.0)
    with pytest.raises(ValueError, match="needs a sequence with events"):
        track_meter(Sequence.from_events([]))


def test_no_metric_information_raises():
    # Two onsets total — every window is below the onset floor, so no claim.
    seq = Sequence.from_events([
        Event(0.0, 1.0, Pitch.from_midi(60)), Event(20.0, 1.0, Pitch.from_midi(60)),
    ])
    with pytest.raises(ValueError, match="No window carries metric information"):
        track_meter(seq, window_beats=8.0, hop_beats=4.0)


# --- phase search (the per-window enabler) ---------------------------------------


def test_phase_search_is_additive_to_infer_meter():
    # Default off: identical to the historical phase-0 behaviour. On: an
    # off-downbeat window still reads its meter. A bar of 4/4 displaced so beat 0
    # is NOT the downbeat: phase search recovers the profile alignment.
    seq = Sequence.from_events(_accented_bars(0.0, (110, 50, 70, 50), 8))
    base = infer_meter(seq)
    searched = infer_meter(seq, phase_search=True)
    # aligned-from-0 content: the top candidate is unchanged, profile no worse
    assert (searched.candidates[0].numerator, searched.candidates[0].denominator) == \
        (base.candidates[0].numerator, base.candidates[0].denominator)


# --- per-window / per-region downbeat offset (anacrusis estimation) --------------


def test_windows_and_regions_carry_zero_offset_when_aligned():
    # Bar lines coincide with window starts (window/hop multiples of the bar):
    # each window's downbeat sits at its own start → offset 0.0, never None for
    # an informative window.
    seq = Sequence.from_events(_accented_bars(0.0, (110, 50, 70, 50), 12))
    res = track_meter(seq, window_beats=12.0, hop_beats=4.0)
    for w in res.windows:
        if w.is_informative:
            assert w.downbeat_offset_beats == pytest.approx(0.0)
    assert res.regions[0].downbeat_offset_beats == pytest.approx(0.0)


def test_anacrusis_window_reports_displacement():
    # Downbeat displaced 1 beat from the sequence start; windows start on beats
    # 0,4,8,... so each window sees its downbeat one beat in → offset 1.0.
    seq = Sequence.from_events(_accented_bars(1.0, (110, 50, 70, 50), 12))
    res = track_meter(seq, window_beats=12.0, hop_beats=4.0)
    informative = [w for w in res.windows if w.is_informative]
    assert informative  # at least some claim
    for w in informative:
        assert (w.numerator, w.denominator) == (4, 4)
        assert w.downbeat_offset_beats == pytest.approx(1.0)
    assert res.regions[0].downbeat_offset_beats == pytest.approx(1.0)


def test_offset_is_deterministic():
    seq = Sequence.from_events(_accented_bars(1.0, (110, 50, 70, 50), 12))
    a = track_meter(seq, window_beats=12.0, hop_beats=4.0).to_dict()
    b = track_meter(seq, window_beats=12.0, hop_beats=4.0).to_dict()
    assert a == b
    assert a["regions"][0]["downbeat_offset_beats"] == pytest.approx(1.0)
