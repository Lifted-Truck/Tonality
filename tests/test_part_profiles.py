"""Part content descriptors (gap E slice 1).

Oracle: a synthetic three-part texture whose profiles are computable by hand —
a moving topline (pure line), a sustained chordal pad, a one-pitch dense kick.
Covers the descriptor math, the facts-never-a-verdict contract (no kind label),
the unvoiced part, determinism, real-MIDI smoke, and MCP parity.
"""

import pytest

from mts.mcp.tools import _canonical_sequence
from mts.temporal import part_profiles

TOPLINE = [[i * 0.5, 0.5, m, "topline"]
           for i, m in enumerate([72, 74, 76, 77, 79, 77, 76, 74])]
PAD = [[bar * 1.0, 1.0, p, "pad"]
       for bar, pcs in enumerate([[48, 52, 55], [45, 48, 52], [47, 50, 53], [48, 52, 55]])
       for p in pcs]
KICK = [[i * 0.25, 0.1, 36, "kick"] for i in range(16)]


def _by_voice(events):
    result = part_profiles(_canonical_sequence(events))
    return {p.voice: p for p in result.profiles}


def test_three_part_texture_separates_on_the_descriptors():
    p = _by_voice(TOPLINE + PAD + KICK)
    # simultaneity: line = 1.0, chordal pad = 3.0
    assert p["topline"].simultaneity == 1.0
    assert p["pad"].simultaneity == 3.0
    assert p["kick"].simultaneity == 1.0
    # pitch identity: kick is one pitch class with zero mobility and zero entropy
    assert p["kick"].distinct_pcs == 1
    assert p["kick"].pitch_mobility == 0.0
    assert p["kick"].pc_entropy_norm == 0.0
    # sustain: kick is percussive (<<1), pad overlaps (3 held notes -> 3.0)
    assert p["kick"].sustain_ratio < 0.5
    assert p["pad"].sustain_ratio == pytest.approx(3.0)
    # register bands are honest
    assert p["kick"].register_lo == p["kick"].register_hi == 36
    assert p["topline"].register_lo == 72 and p["topline"].register_hi == 79


def test_descriptor_arithmetic_exact():
    p = _by_voice(TOPLINE)["topline"]
    assert p.n_events == 8 and p.n_onsets == 8
    assert p.span_beats == pytest.approx(4.0)        # 0 .. 3.5+0.5
    assert p.onset_density == pytest.approx(2.0)     # 8 onsets / 4 beats
    assert p.sustain_ratio == pytest.approx(1.0)     # perfect legato line
    # mobility: mean |delta| over [72,74,76,77,79,77,76,74] = (2+2+1+2+2+1+2)/7
    assert p.pitch_mobility == pytest.approx(12 / 7)


def test_facts_never_a_verdict():
    result = part_profiles(_canonical_sequence(TOPLINE + PAD))
    payload = result.to_dict()
    for profile in payload["profiles"]:
        assert "kind" not in profile and "role" not in profile
        assert "label" not in profile  # no fabricated classification, ever


def test_unvoiced_events_form_their_own_part_sorted_last():
    events = TOPLINE + [[0, 1, 40], [1, 1, 40]]
    result = part_profiles(_canonical_sequence(events))
    assert [p.voice for p in result.profiles] == ["topline", None]


def test_empty_sequence_raises():
    with pytest.raises(ValueError, match="non-empty"):
        part_profiles(_canonical_sequence([]))


def test_degenerate_span_raises_rather_than_blowing_up():
    # #207: a part collapsed to a single instant (near-zero total span) used to
    # return onset_density = 1e8, a silent unbounded blow-up presented as fact.
    # It now errors, don't-guess, like the empty-sequence guard.
    from mts.temporal import Sequence, Event
    from mts.core.pitch import Pitch

    seq = Sequence(
        events=(Event(0.0, 1e-8, Pitch.from_midi(60), "v"),), tempo=None, meter=None
    )
    with pytest.raises(ValueError, match="degenerate span"):
        part_profiles(seq)


def test_short_but_real_part_is_not_over_eagerly_refused():
    # control: genuine short notes (grace-note scale, 0.05 beat) still profile.
    result = part_profiles(_canonical_sequence([[0, 0.05, 60, "v"], [0.5, 0.05, 62, "v"]]))
    assert result.profiles[0].onset_density > 0


def test_deterministic():
    events = TOPLINE + PAD + KICK
    a = part_profiles(_canonical_sequence(events)).to_dict()
    b = part_profiles(_canonical_sequence(events)).to_dict()
    assert a == b


def test_real_midi_smoke():
    from pathlib import Path
    from mts.io.midi import sequence_from_midi_file

    path = (Path(__file__).resolve().parents[1] / "validation" / "corpus" / "swd"
            / "01_RawData" / "score_midi" / "Schubert_D911-01.mid")
    if not path.is_file():
        pytest.skip("vendored SWD smoke corpus not present")
    result = part_profiles(sequence_from_midi_file(str(path)))
    by_voice = {p.voice: p for p in result.profiles}
    # the vocal line is a pure line; the piano is chordal — the descriptors see it
    assert by_voice["t1c1"].simultaneity == 1.0
    assert by_voice["t2c0"].simultaneity > 2.0


def test_mcp_part_profiles_matches_engine():
    from mts.mcp import tools

    events = TOPLINE + PAD + KICK
    engine = part_profiles(_canonical_sequence(events)).to_dict()
    assert tools.part_profiles(events) == engine
