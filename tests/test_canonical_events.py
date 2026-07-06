"""RE-4a/d: one canonical event form on the whole temporal tool surface, and
honest absence typed as its own exception.

Before this, FOUR positional conventions coexisted (voice-at-3 as string,
velocity-at-3, velocity-at-3 + voice-at-4, and 3-only with extras rejected),
and `structural_keys`' declared schema lied about its own. Every temporal
tool now parses [onset, duration, midi, velocity?, voice?] through one
parser, with the legacy string-at-3 voice form still read (JSON types keep
it unambiguous).
"""

from __future__ import annotations

import pytest

from mts.analysis import InsufficientInformation
from mts.mcp import tools

CANON = [
    [0.0, 1.0, 60, 80, "a"], [1.0, 1.0, 62, 90, "a"],
    [0.0, 1.0, 67, None, "b"], [1.0, 1.0, 69, 70, "b"],
]


def test_every_temporal_tool_accepts_the_canonical_five_form():
    assert tools.key_tracking(CANON * 4)["regions"]
    assert tools.structural_keys(CANON * 4)["areas"]
    assert tools.voice_pair_motion(CANON)["transitions"][0]["motion"] == "parallel"
    assert tools.melodic_analysis([[0, 1, 60, 80, "m"], [1, 1, 62, 80, "m"]])
    assert tools.rhythmic_analysis([[float(b), 1.0, 60, 100, "m"] for b in range(8)])
    meter_events = [[float(b), 1.0, 60, (100 if b % 4 == 0 else 60), "m"] for b in range(16)]
    assert tools.meter_estimation(meter_events)["candidates"]
    assert tools.coalesce_events(CANON, onset_window_beats=0.01)["events"]


def test_legacy_forms_still_read():
    # string at index 3 = the old voice-at-3 convention (several tools)
    legacy_voice = [[0, 1, 60, "a"], [1, 1, 62, "a"], [0, 1, 67, "b"], [1, 1, 69, "b"]]
    assert tools.voice_pair_motion(legacy_voice)["transitions"]
    assert tools.structural_keys(legacy_voice * 4)["areas"]
    # numeric at index 3 = the old velocity-at-3 convention (meter tools)
    legacy_vel = [[float(b), 1.0, 60, (100 if b % 4 == 0 else 60)] for b in range(16)]
    assert tools.meter_estimation(legacy_vel)["candidates"]
    # and key_tracking no longer hard-rejects >3-element events
    assert tools.key_tracking(legacy_voice * 4)["regions"]


def test_contradictory_form_raises_instead_of_guessing():
    # a string at 3 (legacy voice) combined with a voice at 4 is contradictory
    with pytest.raises(ValueError, match="[Cc]ontradictory|canonical|legacy"):
        tools.key_tracking([[0, 1, 60, "a", "b"]] * 4)


def test_velocity_reaches_the_event(monkeypatch):
    seq = tools._canonical_sequence(CANON)
    by_midi = {(e.pitch.midi, e.onset): e for e in seq.events}
    assert by_midi[(60, 0.0)].pitch.velocity == 80
    assert by_midi[(67, 0.0)].pitch.velocity is None
    assert by_midi[(69, 1.0)].voice == "b"


# --- RE-4d: honest absence is typed ------------------------------------------------------


def test_absence_is_insufficient_information_and_a_valueerror():
    from mts.analysis import infer_key

    with pytest.raises(InsufficientInformation):
        infer_key([0.0] * 12)
    with pytest.raises(ValueError):  # back-compat: it IS a ValueError subclass
        infer_key([1.0] * 12)


def test_pipelines_no_longer_swallow_real_input_errors():
    # midi_file_analysis used to absorb EVERY ValueError from track_keys as
    # "no tonal information" — a real input error must now propagate.
    import mts.mcp.tools as t

    with pytest.raises(ValueError, match="does not compose"):
        t.midi_file_analysis(
            "/nonexistent-never-read.mid",
            disambiguate_relative_keys=True,
            key_inertia=True,
        )
