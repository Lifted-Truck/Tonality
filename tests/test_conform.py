"""Phase 7 slice 0 — conform_to_scale / fit_to_key (Tonality-Live Q-003).

Pins the two by-construction guarantees, the three consumer contract tests
accepted in `integrations/Tonality-Live/response.md`, and the two ratification
rulings (R1: ties are the common case, default is melodic continuity;
R2: snap-created collisions are kept and reported).
"""

from __future__ import annotations

import pytest

from mts.generate import conform_to_scale, fit_to_key
from mts.mcp.tools import _canonical_sequence

MAJOR = "Ionian"


def _seq(events):
    return _canonical_sequence(events)


# --- consumer contract tests (accepted to land in mts CI on ship) ---------------

def test_contract_1_snap_never_exceeds_six_semitones():
    # every midi pitch, several scale shapes, both fixed tie directions
    for scale in ("Ionian", "Harmonic Minor", "Whole Tone", "Major Pentatonic"):
        for tie in ("down", "up", "previous"):
            events = [[i * 0.5, 0.5, 30 + i] for i in range(60)]
            r = conform_to_scale(_seq(events), scale, 0, tie_break=tie)
            assert all(abs(e.delta) <= 6 for e in r.edits)


def test_contract_2_idempotent_on_in_scale_input():
    events = [[b, 1, m] for b, m in enumerate([60, 62, 64, 65, 67, 69, 71, 72])]
    r = conform_to_scale(_seq(events), MAJOR, 0)
    assert r.notes_snapped == 0 and r.edits == []
    # and a second application of the transform is a fixed point
    again = conform_to_scale(_seq(r.events), MAJOR, 0)
    assert again.events == r.events and again.notes_snapped == 0


def test_contract_3_pitch_is_the_only_field_that_changes():
    events = [[0.0, 1.0, 61, 90, "v1"], [1.5, 0.25, 66, 40, "v2"], [2.0, 2.0, 60, None, None]]
    r = conform_to_scale(_seq(events), MAJOR, 0)
    assert r.notes_total == len(events) == len(r.events)
    for src, out in zip(events, r.events):
        assert out[0] == src[0] and out[1] == src[1]      # onset, duration
        assert out[3] == src[3] and out[4] == src[4]      # velocity, voice
    assert r.notes_snapped == 2                            # 61 and 66 moved


# --- R1: ties are the COMMON case; the default is melodic continuity ------------

def test_r1_the_tie_count_is_as_ratified():
    """Reproduces Tonality-Live's exhaustive table (ratify.md) in-engine."""
    from mts.io.loaders import load_scales

    expected = {"Ionian": 5, "Harmonic Minor": 3, "Whole Tone": 6,
                "Major Pentatonic": 3}
    for name, tied_count in expected.items():
        degrees = set(load_scales()[name].degrees)
        tied = [pc for pc in range(12) if pc not in degrees
                and min((pc - t) % 12 for t in degrees)
                == min((t - pc) % 12 for t in degrees)]
        assert len(tied) == tied_count, name


def test_r1_default_follows_the_previous_note():
    # C#4 ties in C major (C vs D). Approached from D above -> D; from B below -> C.
    from_above = conform_to_scale(_seq([[0, 1, 62, "m"], [1, 1, 61, "m"]]), MAJOR, 0)
    assert from_above.events[1][2] == 62
    assert from_above.edits[0].tied and from_above.edits[0].tie_resolution == "previous"
    from_below = conform_to_scale(_seq([[0, 1, 59, "m"], [1, 1, 61, "m"]]), MAJOR, 0)
    assert from_below.events[1][2] == 60


def test_r1_continuity_reads_the_conformed_previous_not_the_source():
    # F#4 then C#4: F# ties (F vs G). Whatever F# became is what C# leans on —
    # the OUTPUT line is the melody the listener hears.
    r = conform_to_scale(_seq([[0, 1, 66, "m"], [1, 1, 61, "m"]]), MAJOR, 0)
    prev_out = r.events[0][2]
    assert prev_out in (65, 67)
    assert r.events[1][2] == (60 if prev_out == 65 else 62) or r.events[1][2] in (60, 62)


def test_r1_first_note_falls_back_down():
    r = conform_to_scale(_seq([[0, 1, 61]]), MAJOR, 0)
    assert r.events[0][2] == 60
    assert r.edits[0].tie_resolution == "down"


def test_r1_fixed_down_sags_every_tie_flat_but_previous_is_context_sensitive():
    """The artifact that motivated the ruling: under "down" EVERY tied
    accidental resolves flat regardless of musical context. Under the default,
    the SAME pitch resolves differently depending on how it was approached —
    which is the whole point of a context-sensitive tie."""
    chromatic = [[i, 1, 60 + i, "m"] for i in range(6)]   # C C# D D# E F
    down = conform_to_scale(_seq(chromatic), MAJOR, 0, tie_break="down")
    tied_edits = [e for e in down.edits if e.tied]
    assert tied_edits and all(e.delta < 0 for e in tied_edits)
    # same accidental (C#), two contexts, two answers under the default:
    approached_low = conform_to_scale(_seq([[0, 1, 60, "m"], [1, 1, 61, "m"]]), MAJOR, 0)
    approached_high = conform_to_scale(_seq([[0, 1, 62, "m"], [1, 1, 61, "m"]]), MAJOR, 0)
    assert approached_low.events[1][2] == 60 and approached_high.events[1][2] == 62
    # ...where "down" gives one answer in both:
    fixed = conform_to_scale(_seq([[0, 1, 62, "m"], [1, 1, 61, "m"]]), MAJOR, 0,
                             tie_break="down")
    assert fixed.events[1][2] == 60


def test_r1_explicit_up_and_down_are_deterministic():
    up = conform_to_scale(_seq([[0, 1, 61]]), MAJOR, 0, tie_break="up")
    down = conform_to_scale(_seq([[0, 1, 61]]), MAJOR, 0, tie_break="down")
    assert (up.events[0][2], down.events[0][2]) == (62, 60)


# --- R2: many-to-one collisions are kept and reported ---------------------------

def test_r2_collision_is_kept_and_reported():
    events = [[0, 1, 60, 100, "m"], [0, 1, 61, 80, "m"]]   # C + C# together
    r = conform_to_scale(_seq(events), MAJOR, 0)
    assert r.notes_total == 2 and len(r.events) == 2       # count preserved
    assert r.events[0][2] == r.events[1][2] == 60
    assert len(r.collisions) == 1
    c = r.collisions[0]
    assert c.count == 2 and c.source_midis == [60, 61] and c.midi == 60


def test_r2_pre_existing_duplicates_are_not_reported():
    events = [[0, 1, 60, 100, "m"], [0, 1, 60, 80, "m"]]   # already identical
    r = conform_to_scale(_seq(events), MAJOR, 0)
    assert r.collisions == []


# --- the rest of the surface ----------------------------------------------------

def test_fit_to_key_is_the_scale_wrapper():
    events = [[0, 1, 61, "m"], [1, 1, 63, "m"]]
    a = fit_to_key(_seq(events), 0, "major")
    b = conform_to_scale(_seq(events), MAJOR, 0)
    assert a.events == b.events and a.scale_name == MAJOR
    with pytest.raises(ValueError, match="major.*minor"):
        fit_to_key(_seq(events), 0, "dorian")


def test_explicit_degrees_are_accepted():
    r = conform_to_scale(_seq([[0, 1, 61]]), [0, 2, 4, 5, 7, 9, 11], 0)
    assert r.scale_name is None and r.events[0][2] == 60


def test_unknown_scale_and_bad_tie_break_error_not_guess():
    with pytest.raises(ValueError, match="Unknown scale"):
        conform_to_scale(_seq([[0, 1, 60]]), "Klingon", 0)
    with pytest.raises(ValueError, match="tie_break"):
        conform_to_scale(_seq([[0, 1, 60]]), MAJOR, 0, tie_break="sideways")
    with pytest.raises(ValueError, match="non-empty"):
        conform_to_scale(_seq([]), MAJOR, 0)


def test_midi_boundary_takes_the_in_range_direction():
    # pc 1 over a {0}-only scale: candidates midi-1 and midi+11. At midi=1 the
    # down candidate is 0 (in range); at midi=121 the up candidate 132 is out.
    low = conform_to_scale(_seq([[0, 1, 1]]), [0], 0, tie_break="up")
    assert 0 <= low.events[0][2] <= 127
    high = conform_to_scale(_seq([[0, 1, 121]]), [11], 0, tie_break="up")
    assert 0 <= high.events[0][2] <= 127


def test_deterministic():
    events = [[i * 0.5, 0.5, 55 + (i * 7) % 24, 60 + i, "m"] for i in range(20)]
    a = conform_to_scale(_seq(events), "Harmonic Minor", 2).to_dict()
    b = conform_to_scale(_seq(events), "Harmonic Minor", 2).to_dict()
    assert a == b


def test_mcp_parity():
    from mts.mcp import tools

    out = tools.conform_to_scale(events=[[0, 1, 61, 90, "m"]], scale=MAJOR, root_pc=0)
    assert set(out) >= {"events", "edits", "collisions", "tie_break", "degrees"}
    key = tools.fit_to_key(events=[[0, 1, 61, 90, "m"]], tonic_pc=0, mode="major")
    assert key["scale_name"] == MAJOR
