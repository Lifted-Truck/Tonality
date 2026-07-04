"""Groove extract / apply (gap 10): GrooveTemplate distillation + Live-parity apply.

The honesty bound (quantized → null groove) mirrors swing; the timing
round-trip (extract then re-apply onto the quantized loop reconstructs the
onsets) is the central correctness anchor.
"""

from __future__ import annotations

import pytest

from mts.core.pitch import Pitch
from mts.temporal import (
    Event,
    GrooveTemplate,
    Sequence,
    analyze_swing,
    apply_groove,
    extract_groove,
)


def _seq(spec):
    """spec: list of (onset, duration, midi, velocity-or-None)."""
    events = [Event(o, d, Pitch.from_midi(m, velocity=v)) for o, d, m, v in spec]
    return Sequence.from_events(events)


def _swung_loop(fraction, beats=4, vel=80):
    """One two-way division per beat; interior (offbeat) onset at `fraction`."""
    spec = []
    for b in range(beats):
        spec.append((float(b), fraction, 60, vel))
        spec.append((b + fraction, 1.0 - fraction, 62, vel))
    return _seq(spec)


# --- extract: the honesty bound ---------------------------------------------------------


def test_quantized_input_is_a_null_timing_groove():
    seq = _seq([(i * 0.5, 0.5, 60, 80) for i in range(4)])
    tmpl = extract_groove(seq, base_unit_beats=0.5, loop_length_beats=2.0)
    assert tmpl.max_abs_offset == 0.0
    assert all(s.offset in (0.0, None) for s in tmpl.slots)
    assert tmpl.is_null()


def test_flat_velocity_is_a_null_velocity_groove():
    # Off-grid timing but flat dynamics: timing groove present, velocity null.
    seq = _seq([(0.0, 0.5, 60, 64), (0.58, 0.5, 62, 64), (1.0, 0.5, 64, 64)])
    tmpl = extract_groove(seq, base_unit_beats=0.5, loop_length_beats=2.0)
    assert tmpl.max_abs_velocity_delta == 0.0
    assert all(s.velocity_delta in (0.0, None) for s in tmpl.slots)
    assert tmpl.max_abs_offset > 0.0  # the timing feel survives


def test_empty_slots_are_distinct_from_on_grid():
    # Onsets only on beats 0 and 1.0 of a 4-slot loop → slots 1 and 3 empty.
    seq = _seq([(0.0, 0.5, 60, 80), (1.0, 0.5, 62, 80)])
    tmpl = extract_groove(seq, base_unit_beats=0.5, loop_length_beats=2.0)
    by_index = {s.index: s for s in tmpl.slots}
    assert by_index[0].offset == 0.0 and by_index[0].onset_count == 1
    assert by_index[1].offset is None and by_index[1].onset_count == 0
    assert tmpl.filled_slots == 2


def test_polyphony_shares_a_slot():
    # A chord stab: three simultaneous onsets at beat 0 → one filled slot, n=3.
    seq = _seq([(0.0, 0.5, 60, 80), (0.0, 0.5, 64, 80), (0.0, 0.5, 67, 80)])
    tmpl = extract_groove(seq, base_unit_beats=0.5, loop_length_beats=1.0)
    assert tmpl.slots[0].onset_count == 3


# --- extract: geometry validation -------------------------------------------------------


def test_loop_length_must_divide_base():
    seq = _seq([(0.0, 0.5, 60, 80)])
    with pytest.raises(ValueError, match="whole multiple"):
        extract_groove(seq, base_unit_beats=0.5, loop_length_beats=1.3)


def test_base_must_be_positive():
    seq = _seq([(0.0, 0.5, 60, 80)])
    with pytest.raises(ValueError, match="base_unit_beats must be positive"):
        extract_groove(seq, base_unit_beats=0.0)


# --- apply: round-trips and identities --------------------------------------------------


def _quantize(seq, base):
    import math

    return _seq(
        [
            (int(math.floor(e.onset / base + 0.5)) * base, e.duration, e.pitch.midi, 80)
            for e in seq.events
        ]
    )


def test_timing_round_trip_reconstructs_onsets():
    loop = _seq(
        [(0.0, 0.5, 60, 90), (0.58, 0.5, 62, 70), (1.0, 0.5, 64, 90), (1.58, 0.5, 65, 70)]
    )
    base = 0.5
    tmpl = extract_groove(loop, base_unit_beats=base, loop_length_beats=2.0)
    quantized = _quantize(loop, base)
    res = apply_groove(quantized, tmpl, quantize=1.0, timing=1.0, random=0.0, amount=1.0)
    got = sorted(e.onset for e in res.sequence.events)
    want = sorted(e.onset for e in loop.events)
    for g, w in zip(got, want):
        assert g == pytest.approx(w, abs=1e-9)


def test_null_template_with_no_quantize_is_identity():
    loop = _seq([(0.0, 0.5, 60, 80), (0.5, 0.5, 62, 80), (1.0, 0.5, 64, 80)])
    tmpl = extract_groove(loop, base_unit_beats=0.5, loop_length_beats=2.0)
    assert tmpl.is_null()
    res = apply_groove(
        loop, tmpl, quantize=0.0, timing=2.0, velocity=3.0, amount=1.0, random=0.0
    )
    for before, after in zip(loop.events, res.sequence.events):
        assert after.onset == pytest.approx(before.onset)
        assert after.pitch.velocity == before.pitch.velocity
    assert res.moved_events == 0


def test_amount_zero_is_pure_quantization():
    loop = _seq([(0.07, 0.5, 60, 90), (0.61, 0.5, 62, 70)])
    base = 0.5
    tmpl = extract_groove(loop, base_unit_beats=base, loop_length_beats=1.0)
    res = apply_groove(loop, tmpl, quantize=1.0, timing=1.0, velocity=5.0, amount=0.0)
    # amount=0 disables feel; quantize=1 snaps to grid; velocity untouched by feel.
    assert sorted(e.onset for e in res.sequence.events) == pytest.approx([0.0, 0.5])
    assert sorted(e.pitch.velocity for e in res.sequence.events) == [70, 90]


# --- apply: velocity semantics (additive accent transfer) -------------------------------


def test_accent_contour_transfers_to_a_flat_loop():
    # Template from a loud-soft loop, applied to a flat loop, transfers the accents.
    source = _seq([(0.0, 0.5, 60, 100), (0.5, 0.5, 62, 60)])
    tmpl = extract_groove(source, base_unit_beats=0.5, loop_length_beats=1.0)
    flat = _seq([(0.0, 0.5, 72, 80), (0.5, 0.5, 74, 80)])
    res = apply_groove(flat, tmpl, quantize=1.0, timing=0.0, velocity=1.0, amount=1.0)
    vels = [e.pitch.velocity for e in res.sequence.events]
    assert vels == [100, 60]  # 80 + (+20), 80 + (-20)


def test_negative_velocity_reverses_accents():
    source = _seq([(0.0, 0.5, 60, 100), (0.5, 0.5, 62, 60)])
    tmpl = extract_groove(source, base_unit_beats=0.5, loop_length_beats=1.0)
    flat = _seq([(0.0, 0.5, 72, 80), (0.5, 0.5, 74, 80)])
    res = apply_groove(flat, tmpl, quantize=1.0, timing=0.0, velocity=-1.0, amount=1.0)
    assert [e.pitch.velocity for e in res.sequence.events] == [60, 100]


def test_velocity_clamped_to_midi_range():
    source = _seq([(0.0, 0.5, 60, 127), (0.5, 0.5, 62, 0)])
    tmpl = extract_groove(source, base_unit_beats=0.5, loop_length_beats=1.0)
    flat = _seq([(0.0, 0.5, 72, 120), (0.5, 0.5, 74, 10)])
    res = apply_groove(flat, tmpl, quantize=1.0, timing=0.0, velocity=5.0, amount=1.0)
    for e in res.sequence.events:
        assert 0 <= e.pitch.velocity <= 127


def test_velocity_none_preserved_when_template_silent():
    loop = _seq([(0.0, 0.5, 60, None), (0.5, 0.5, 62, None)])
    tmpl = extract_groove(loop, base_unit_beats=0.5, loop_length_beats=1.0)
    assert tmpl.mean_velocity is None
    res = apply_groove(loop, tmpl, quantize=1.0, timing=0.0, velocity=1.0)
    assert all(e.pitch.velocity is None for e in res.sequence.events)


# --- apply: determinism -----------------------------------------------------------------


def test_random_requires_seed():
    loop = _seq([(0.0, 0.5, 60, 80)])
    tmpl = extract_groove(loop, base_unit_beats=0.5, loop_length_beats=1.0)
    with pytest.raises(ValueError, match="explicit seed"):
        apply_groove(loop, tmpl, random=0.5)


def test_random_is_deterministic_for_a_seed():
    loop = _seq([(0.07, 0.5, 60, 90), (0.61, 0.5, 62, 70), (1.0, 0.5, 64, 80)])
    base = 0.5
    tmpl = extract_groove(loop, base_unit_beats=base, loop_length_beats=2.0)
    a = apply_groove(loop, tmpl, random=0.5, seed=42)
    b = apply_groove(loop, tmpl, random=0.5, seed=42)
    assert [e.onset for e in a.sequence.events] == [e.onset for e in b.sequence.events]


def test_random_jitter_keyed_to_onset_not_order():
    # Same onsets, different MIDI assignment / construction order → same jitter.
    base = 0.5
    s1 = _seq([(0.07, 0.5, 60, 80), (0.61, 0.5, 67, 80)])
    s2 = _seq([(0.61, 0.5, 62, 80), (0.07, 0.5, 64, 80)])
    tmpl = extract_groove(s1, base_unit_beats=base, loop_length_beats=1.0)
    a = apply_groove(s1, tmpl, random=0.7, seed=7)
    b = apply_groove(s2, tmpl, random=0.7, seed=7)
    onsets_a = sorted(round(e.onset, 9) for e in a.sequence.events)
    onsets_b = sorted(round(e.onset, 9) for e in b.sequence.events)
    assert onsets_a == onsets_b


def test_different_seeds_generally_differ():
    loop = _seq([(0.07, 0.5, 60, 90), (0.61, 0.5, 62, 70)])
    tmpl = extract_groove(loop, base_unit_beats=0.5, loop_length_beats=1.0)
    a = apply_groove(loop, tmpl, random=0.8, seed=1)
    b = apply_groove(loop, tmpl, random=0.8, seed=2)
    assert [e.onset for e in a.sequence.events] != [e.onset for e in b.sequence.events]


# --- the swing special case -------------------------------------------------------------


def test_groove_generalizes_swing():
    # base = half the felt beat (the 1/8 grid): offbeat slots carry the swing.
    fraction = 2 / 3
    loop = _swung_loop(fraction, beats=4)
    swing = analyze_swing(loop)
    assert swing.feel == "swung"

    tmpl = extract_groove(loop, base_unit_beats=0.5, loop_length_beats=4.0)
    # Beat slots (even) sit on grid; offbeat slots (odd) carry (f-0.5)/0.5.
    expected = (swing.mean_fraction - 0.5) / 0.5
    offbeat = [tmpl.slots[i].offset for i in (1, 3, 5, 7)]
    assert all(o == pytest.approx(expected) for o in offbeat)
    assert all(tmpl.slots[i].offset == pytest.approx(0.0) for i in (0, 2, 4, 6))


# --- template JSON round-trip -----------------------------------------------------------


def test_template_to_dict_from_dict_round_trip():
    loop = _seq([(0.0, 0.5, 60, 90), (0.58, 0.5, 62, 70), (1.0, 0.5, 64, 80)])
    tmpl = extract_groove(loop, base_unit_beats=0.5, loop_length_beats=2.0)
    restored = GrooveTemplate.from_dict(tmpl.to_dict())
    assert restored == tmpl


# --- RE-3b: the voice parameter actually restricts the groove ---------------------------


def test_voice_restricts_the_groove_to_one_part():
    # Two parts on the same offbeat grid; groove only the drums.
    drums = [Event(b + 0.5, 0.5, Pitch.from_midi(36, velocity=80), voice="drums")
             for b in range(4)]
    keys = [Event(b + 0.5, 0.5, Pitch.from_midi(60, velocity=80), voice="keys")
            for b in range(4)]
    seq = Sequence.from_events(drums + keys)
    swung = _swung_loop(0.6)  # template with offbeat slots pushed late
    tmpl = extract_groove(swung, base_unit_beats=0.5, loop_length_beats=2.0)

    result = apply_groove(seq, tmpl, voice="drums")
    assert result.voice == "drums"  # the applied scope is cited in the result
    drum_onsets = sorted(e.onset for e in result.sequence.events if e.voice == "drums")
    key_onsets = sorted(e.onset for e in result.sequence.events if e.voice == "keys")
    assert key_onsets == [0.5, 1.5, 2.5, 3.5]  # untouched — used to be grooved too
    assert drum_onsets != [0.5, 1.5, 2.5, 3.5]  # the named part moved
    # and the change counters only count the grooved part
    assert result.moved_events <= len(drums)


def test_voice_none_grooves_everything():
    events = [Event(b + 0.5, 0.5, Pitch.from_midi(60, velocity=80), voice="keys")
              for b in range(4)]
    seq = Sequence.from_events(events)
    tmpl = extract_groove(_swung_loop(0.6), base_unit_beats=0.5, loop_length_beats=2.0)
    all_grooved = apply_groove(seq, tmpl)
    only_other = apply_groove(seq, tmpl, voice="absent-part")
    assert all_grooved.moved_events > 0
    assert only_other.moved_events == 0  # nothing matches the named voice
    assert [e.onset for e in only_other.sequence.events] == [0.5, 1.5, 2.5, 3.5]
