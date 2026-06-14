"""Local key tracking: windowed key induction → key regions (3.5b extension)."""

from __future__ import annotations

import json

import pytest

from mts.core.pitch import Pitch
from mts.temporal import Event, Sequence, track_keys


def _chord(midi_notes, onset, duration):
    return [Event(onset, duration, Pitch.from_midi(m)) for m in midi_notes]


def _progression(tonic_midi, start, cycles=1):
    """I–IV–V–I over a tonic pedal in the major key of tonic_midi.

    The pedal keeps every sub-window decisive: a bare V–I window genuinely
    correlates better with the dominant key (surfaced, not smoothed — v1 has
    no hysteresis), so key-defining material must actually define the key.
    """
    events = []
    t = tonic_midi
    for c in range(cycles):
        base = start + 8 * c
        events.append(Event(base, 8, Pitch.from_midi(t - 12)))  # tonic pedal
        events += _chord([t, t + 4, t + 7], base, 2)
        events += _chord([t + 5, t + 9, t + 12], base + 2, 2)
        events += _chord([t + 7, t + 11, t + 14], base + 4, 2)
        events += _chord([t, t + 4, t + 7], base + 6, 2)
    return events


# --- windowed pc weights (the Sequence extension) -------------------------------------


def test_windowed_pc_weights_count_only_the_overlap():
    seq = Sequence.from_events([Event(0, 4, Pitch.from_midi(60))])
    assert seq.pc_weights(2, 6)[0] == pytest.approx(2.0)
    assert seq.pc_weights(2, 6)[1:] == (0.0,) * 11
    assert seq.pc_weights() == seq.pc_weights(None, None)  # default unchanged


# --- single key ------------------------------------------------------------------------


def test_single_key_yields_one_region_matching_global_induction():
    from mts.analysis import infer_key

    seq = Sequence.from_events(_progression(60, 0, cycles=2))
    result = track_keys(seq)
    assert len(result.regions) == 1
    region = result.regions[0]
    assert (region.tonic_pc, region.mode) == (0, "major")
    assert region.start_beats == pytest.approx(0.0)
    assert region.end_beats == pytest.approx(seq.duration_beats)
    best = infer_key(seq).candidates[0]
    assert (best.tonic_pc, best.mode) == (region.tonic_pc, region.mode)


def test_result_cites_parameters_and_profile_version():
    seq = Sequence.from_events(_progression(60, 0, cycles=2))
    result = track_keys(seq, window_beats=4.0, hop_beats=1.0)
    assert result.window_beats == 4.0
    assert result.hop_beats == 1.0
    assert result.profile_version  # same versioned prior as infer_key


# --- modulation ------------------------------------------------------------------------


def test_modulation_splits_into_regions_at_the_key_change():
    # 16 beats of C major, then 16 beats of F# major (a tritone apart).
    events = _progression(60, 0, cycles=2) + _progression(66, 16, cycles=2)
    result = track_keys(Sequence.from_events(events))
    assert (result.regions[0].tonic_pc, result.regions[0].mode) == (0, "major")
    assert (result.regions[-1].tonic_pc, result.regions[-1].mode) == (6, "major")
    # the boundary lands at the change within window resolution
    assert result.regions[0].end_beats == pytest.approx(16.0, abs=4.0)
    assert result.regions[-1].start_beats == pytest.approx(16.0, abs=4.0)
    # regions tile the tracked span without overlap
    for left, right in zip(result.regions, result.regions[1:]):
        assert left.end_beats == pytest.approx(right.start_beats)


def test_regions_carry_seconds_via_the_tempo_map():
    events = _progression(60, 0, cycles=2)
    seq = Sequence.from_events(events, bpm=60.0)  # 1 beat = 1 second
    region = track_keys(seq).regions[0]
    assert region.start_seconds == pytest.approx(region.start_beats)
    assert region.end_seconds == pytest.approx(region.end_beats)


# --- the honesty contract --------------------------------------------------------------


def test_silence_does_not_split_a_key_region():
    # same key on both sides of an 8-beat silence: no evidence != a key change
    events = _progression(60, 0) + _progression(60, 16)
    result = track_keys(Sequence.from_events(events))
    assert len(result.regions) == 1
    assert (result.regions[0].tonic_pc, result.regions[0].mode) == (0, "major")
    # ...but the silent windows are recorded as uninformative evidence
    assert any(not w.is_informative for w in result.windows)


def test_uninformative_everywhere_raises():
    # full chromatic, equal weight: uniform pc content in every window
    events = [Event(0, 4, Pitch.from_midi(60 + i)) for i in range(12)]
    with pytest.raises(ValueError):
        track_keys(Sequence.from_events(events))


def test_empty_sequence_and_bad_geometry_raise():
    seq = Sequence.from_events(_progression(60, 0))
    with pytest.raises(ValueError):
        track_keys(Sequence.from_events([]))
    with pytest.raises(ValueError):
        track_keys(seq, window_beats=0.0)
    with pytest.raises(ValueError):
        track_keys(seq, hop_beats=-1.0)


# --- output shape ----------------------------------------------------------------------


def test_to_dict_is_json_ready_with_window_evidence():
    result = track_keys(Sequence.from_events(_progression(60, 0, cycles=2)))
    payload = json.loads(json.dumps(result.to_dict()))
    assert payload["regions"][0]["tonic_pc"] == 0
    assert payload["regions"][0]["window_count"] >= 1
    assert payload["windows"]  # per-window evidence ships with the answer
    assert payload["profile_version"]


# --- relative-key disambiguation (opt-in, off by default) -------------------------------

def _relative_confusable_sequence() -> Sequence:
    """A window the bare argmax reads as C major but tonal hierarchy (the G#
    leading tone of A minor, outside the C-major collection) reads as A minor."""
    weights = {0: 3.3, 4: 2.3, 7: 2.0, 9: 2.0, 8: 2.0, 2: 1.0, 5: 1.0, 11: 1.0}
    events = [Event(0.0, dur, Pitch.from_midi(60 + pc)) for pc, dur in weights.items()]
    return Sequence.from_events(events)


def test_disambiguate_off_by_default_is_byte_identical():
    seq = Sequence.from_events(_progression(60, 0, cycles=2))
    explicit_off = track_keys(seq, disambiguate_relative=False)
    assert json.dumps(track_keys(seq).to_dict()) == json.dumps(explicit_off.to_dict())
    assert explicit_off.disambiguate_relative is False


def test_disambiguate_flips_a_relative_region():
    seq = _relative_confusable_sequence()
    off = track_keys(seq, window_beats=4.0, hop_beats=2.0)
    on = track_keys(seq, window_beats=4.0, hop_beats=2.0, disambiguate_relative=True)
    assert (off.regions[0].tonic_pc, off.regions[0].mode) == (0, "major")
    assert (on.regions[0].tonic_pc, on.regions[0].mode) == (9, "minor")
    assert on.disambiguate_relative is True


def test_disambiguate_does_not_over_trigger_on_a_clear_key():
    # A clear C-major progression is not a relative near-tie — the flag is a no-op.
    seq = Sequence.from_events(_progression(60, 0, cycles=2))
    off = track_keys(seq)
    on = track_keys(seq, disambiguate_relative=True)
    assert [(r.tonic_pc, r.mode) for r in on.regions] == [
        (r.tonic_pc, r.mode) for r in off.regions
    ]


# --- key-region smoothing (opt-in hysteresis, off by default) ---------------------------

from mts.io.loaders import load_key_smoothing  # noqa: E402
from mts.temporal.key_tracking import _smooth_labels  # noqa: E402


from mts.temporal import KeyWindow  # noqa: E402


def _windows(entries):
    """Informative windows with synthetic per-window labels + margins.

    entries: list of ((tonic_pc, mode), margin)."""
    return [
        KeyWindow(
            start_beats=float(i), end_beats=float(i) + 1, center_beats=float(i) + 0.5,
            tonic_pc=label[0], mode=label[1], score=0.5, margin=mg,
        )
        for i, (label, mg) in enumerate(entries)
    ]


def test_smooth_labels_absorbs_a_weak_blip_between_same_key():
    priors = load_key_smoothing()  # min_region_windows=2, min_region_margin=0.1
    # A A [B] A A, the B window short (1) + weak (margin 0.02 < 0.1).
    wins = _windows([((0, "major"), 0.3), ((0, "major"), 0.3), ((7, "major"), 0.02),
                     ((0, "major"), 0.3), ((0, "major"), 0.3)])
    labels = [(w.tonic_pc, w.mode) for w in wins]
    smoothed = _smooth_labels(wins, labels, priors)
    assert smoothed == [(0, "major")] * 5  # the blip absorbed, all one key


def test_smooth_labels_margin_override_keeps_confident_blip():
    priors = load_key_smoothing()
    wins = _windows([((0, "major"), 0.3), ((0, "major"), 0.3), ((7, "major"), 0.5),
                     ((0, "major"), 0.3), ((0, "major"), 0.3)])
    labels = [(w.tonic_pc, w.mode) for w in wins]
    # margin 0.5 >= 0.1: a confident brief modulation survives.
    assert _smooth_labels(wins, labels, priors) == labels


def test_smooth_labels_blip_between_two_keys_joins_longer_neighbour():
    priors = load_key_smoothing()
    # A A A [B] C  → the weak B joins the longer neighbour (A, count 3 > C count 1).
    wins = _windows([((0, "major"), 0.3), ((0, "major"), 0.3), ((0, "major"), 0.3),
                     ((7, "major"), 0.02), ((5, "major"), 0.02)])
    labels = [(w.tonic_pc, w.mode) for w in wins]
    smoothed = _smooth_labels(wins, labels, priors)
    assert smoothed[3] == (0, "major")  # B absorbed into the A run


# --- end-to-end through track_keys ------------------------------------------------------

def _blip_sequence(blip_pcs) -> Sequence:
    """Strong C major with one weak foreign 4-beat block (non-overlapping windows)."""
    events = []
    for t in range(0, 16, 2):
        events += _chord([60, 64, 67], float(t), 2.0)
    events += _chord([60 + pc for pc in blip_pcs], 16.0, 2.0)
    events += _chord([60 + pc for pc in blip_pcs], 18.0, 2.0)
    for t in range(20, 36, 2):
        events += _chord([60, 64, 67], float(t), 2.0)
    return Sequence.from_events(events)


def test_smoothing_off_by_default_is_byte_identical():
    seq = _blip_sequence([2, 5, 11])
    explicit_off = track_keys(seq, window_beats=4.0, hop_beats=4.0, smoothing=False)
    assert json.dumps(
        track_keys(seq, window_beats=4.0, hop_beats=4.0).to_dict()
    ) == json.dumps(explicit_off.to_dict())
    assert explicit_off.smoothing_version is None


def test_smoothing_absorbs_a_real_blip_region_keeping_window_evidence():
    seq = _blip_sequence([2, 5, 11])  # foreign window margin ~0.025 < 0.1
    off = track_keys(seq, window_beats=4.0, hop_beats=4.0)
    on = track_keys(seq, window_beats=4.0, hop_beats=4.0, smoothing=True)
    assert len(off.regions) == 3  # C, blip, C
    assert len(on.regions) == 1 and (on.regions[0].tonic_pc, on.regions[0].mode) == (0, "major")
    assert on.smoothing_version == "key-smoothing.1"
    # windows keep their raw argmax — the blip vote is still visible as evidence
    assert any(w.tonic_pc != 0 for w in on.windows if w.is_informative)


def test_smoothing_keeps_a_confident_brief_modulation():
    seq = _blip_sequence([1, 4, 8])  # foreign window margin ~0.29 >= 0.1
    on = track_keys(seq, window_beats=4.0, hop_beats=4.0, smoothing=True)
    assert len(on.regions) == 3  # the confident blip survives the margin override


def test_smoothing_composes_with_disambiguation():
    seq = _blip_sequence([2, 5, 11])
    result = track_keys(
        seq, window_beats=4.0, hop_beats=4.0,
        disambiguate_relative=True, smoothing=True,
    )
    assert result.smoothing_version == "key-smoothing.1"
    assert result.disambiguate_relative is True
