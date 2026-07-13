"""gap E slice 2 — pairwise part-relation atoms (mts.temporal.relations).

The engine relates labeled parts pairwise and reports FACTS, never a verdict:
onset synchrony/interlock/overlap (an exact partition), groove congruence,
register gap, directional chord-tone support, and the motion mix. These tests
pin the arithmetic, the no-classification contract, the honest-null behavior,
and parity with the MCP tool — on a synthetic texture and on real Schubert.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mts.temporal import Sequence, part_relations
from mts.temporal.sequence import Event
from mts.core.pitch import Pitch

CORPUS = Path(__file__).resolve().parents[1] / "validation" / "corpus" / "swd"
SCHUBERT = CORPUS / "01_RawData" / "score_midi" / "Schubert_D911-01.mid"


def _seq(rows):
    return Sequence.from_events(
        Event(onset=o, duration=d, pitch=Pitch.from_midi(m), voice=v)
        for o, d, m, v in rows
    )


def _texture():
    """kick + bass (doubling the kick's onsets) + a held C-major pad + a topline
    of C-major chord tones over it."""
    rows = []
    for b in range(4):
        rows += [(float(b), 0.1, 36, "kick"), (float(b), 0.5, 48, "bass")]
    rows += [(0.0, 4.0, 60, "pad"), (0.0, 4.0, 64, "pad"), (0.0, 4.0, 67, "pad")]
    for b, p in enumerate((60, 64, 67, 72)):
        rows.append((float(b), 0.5, p, "topline"))
    return _seq(rows)


def _rel(result, a, b):
    for r in result.relations:
        if r.voice_a == a and r.voice_b == b:
            return r
    raise KeyError((a, b))


def test_rhythmic_partition_is_exact_and_sums_to_one():
    result = part_relations(_texture())
    assert result.relations, "expected pairs"
    for r in result.relations:
        assert r.onset_synchrony + r.interlock + r.overlap == pytest.approx(1.0)
        for x in (r.onset_synchrony, r.interlock, r.overlap, r.groove_congruence):
            assert 0.0 <= x <= 1.0


def test_bass_doubling_kick_reads_full_synchrony():
    r = _rel(part_relations(_texture()), "bass", "kick")
    assert r.onset_synchrony == 1.0        # bass onsets exactly with the kick
    assert r.interlock == 0.0 and r.overlap == 0.0
    assert r.groove_congruence == 1.0      # same beat-phase (both on integer beats)
    # sorted labels a=bass(48) b=kick(36): gap = kick - bass = -12
    assert r.register_gap_mean == -12.0


def test_topline_over_pad_is_chord_tone_dominant():
    # a=pad, b=topline (sorted): support_b_vs_a = topline pitches that are chord
    # tones of the pad's simultaneous pcs — every topline note is a C-major tone.
    r = _rel(part_relations(_texture()), "pad", "topline")
    assert r.chord_tone_support_b_vs_a == 1.0
    assert r.overlap == 0.75 and r.onset_synchrony == 0.25   # 3 of 4 onsets over the held pad
    assert r.co_sounding_moments == 4


def test_static_part_under_a_moving_line_reads_oblique():
    # bass holds 48 under a rising topline sharing its onsets → all oblique.
    r = _rel(part_relations(_texture()), "bass", "topline")
    assert r.motion_mix == {"oblique": 3}
    assert r.motion_transitions == 3


def test_interlock_fires_for_a_hocket():
    # A on the beat, B strictly in A's rests (and vice versa) → no synchrony.
    rows = []
    for b in range(4):
        rows += [(b * 0.5, 0.2, 60, "A"), (b * 0.5 + 0.25, 0.2, 67, "B")]
    r = _rel(part_relations(_seq(rows)), "A", "B")
    assert r.onset_synchrony == 0.0
    assert r.interlock == pytest.approx(1.0)   # every onset lands in the other's rest
    assert r.overlap == 0.0


def test_chord_tone_support_is_directional():
    # A single C melody over an F-major chord: C supports F-major (it's the 5th),
    # but only one of {F,A,C} sits in the momentary single pc of the melody.
    rows = [(0.0, 1.0, 60, "mel"), (0.0, 1.0, 65, "harm"),
            (0.0, 1.0, 69, "harm"), (0.0, 1.0, 72, "harm")]
    r = _rel(part_relations(_seq(rows)), "harm", "mel")
    # a=harm, b=mel: mel(C=0) is a chord tone of harm {5,9,0} → support_b_vs_a=1.0
    assert r.chord_tone_support_b_vs_a == 1.0
    # harm pcs vs mel's single pc {0}: only C(0) of {5,9,0} matches → 1/3
    assert r.chord_tone_support_a_vs_b == pytest.approx(1 / 3)


def test_facts_never_a_verdict():
    # No field names a classification — the caller judges from the atoms.
    r = _rel(part_relations(_texture()), "bass", "kick")
    keys = set(r.to_dict())
    for forbidden in ("kind", "role", "relation", "label", "verdict", "type", "is_doubling"):
        assert forbidden not in keys


def test_unvoiced_part_is_relatable_and_sorted_last():
    rows = [(0.0, 1.0, 60, "lead"), (1.0, 1.0, 62, "lead"),
            (0.0, 1.0, 48, None), (1.0, 1.0, 50, None)]
    result = part_relations(_seq(rows))
    r = result.relations[0]
    assert (r.voice_a, r.voice_b) == ("lead", None)   # None sorts last
    # both are single-pitch labeled? one is unvoiced → no motion claims for the pair
    assert r.motion_mix == {}


def test_fewer_than_two_parts_raises():
    with pytest.raises(ValueError):
        part_relations(_seq([(0.0, 1.0, 60, "only"), (1.0, 1.0, 62, "only")]))


def test_deterministic():
    a = part_relations(_texture()).to_dict()
    b = part_relations(_texture()).to_dict()
    assert a == b


@pytest.mark.skipif(not SCHUBERT.exists(), reason="SWD smoke corpus not vendored")
def test_real_midi_smoke():
    from mts.io.midi import sequence_from_midi_file

    result = part_relations(sequence_from_midi_file(str(SCHUBERT)))
    r = _rel(result, "t1c1", "t2c0")   # vocal ~ piano
    # rhythmic partition holds on real music
    assert r.onset_synchrony + r.interlock + r.overlap == pytest.approx(1.0)
    # the vocal line is largely chord-tone over the piano's harmony (a Lied)
    assert r.chord_tone_support_a_vs_b > 0.6
    # the piano part is chordal → it makes no single-pitch motion claim
    assert r.motion_mix == {}


def test_mcp_parity():
    from mts.mcp import tools

    events = [[0.0, 1.0, 60, 80, "lead"], [1.0, 1.0, 64, 80, "lead"],
              [0.0, 2.0, 48, 80, "bass"]]
    seq = _seq([(0.0, 1.0, 60, "lead"), (1.0, 1.0, 64, "lead"), (0.0, 2.0, 48, "bass")])
    assert tools.part_relations(events) == part_relations(seq).to_dict()


def test_sounding_by_beat_matches_naive_filter():
    """#214: the onset-sorted sweep must be set-identical to the O(n) per-beat
    filter it replaces, including held/overlapping notes and exact boundaries."""
    from mts.temporal.relations import _sounding_by_beat
    from mts.temporal.sequence import Event
    from mts.core.pitch import Pitch

    events = [
        Event(0.0, 4.0, Pitch.from_midi(48), "x"),   # long held note
        Event(0.5, 0.2, Pitch.from_midi(60), "x"),   # short, inside the held one
        Event(1.0, 1.0, Pitch.from_midi(64), "x"),
        Event(1.0, 2.0, Pitch.from_midi(67), "x"),   # co-onset, different length
        Event(3.5, 0.5, Pitch.from_midi(72), "x"),
    ]
    # query beats: onsets, offsets (boundary — half-open, so offset is NOT sounding),
    # midpoints, before-start, after-end, and an unsorted order to exercise the sweep.
    beats = [4.0, 0.0, 0.6, 1.0, 2.0, 3.0, 3.5, 4.0, -1.0, 0.7, 0.69999, 2.9999]
    swept = _sounding_by_beat(events, beats)
    for beat, got in zip(beats, swept):
        naive = {e for e in events if e.sounds_at(beat)}
        assert set(got) == naive, f"mismatch at beat {beat}"
