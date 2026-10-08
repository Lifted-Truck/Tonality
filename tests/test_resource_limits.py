"""Every guard from the security slice, each proven on its OWN path (2026-10-08).

Each test feeds an input just over a budget. That choice is deliberate: if a
guard is ever removed, the input stays cheap enough to run (seconds, tens of MB)
and the test FAILS CLEANLY on a missing ValueError, rather than taking the
machine down the way the original 1.2 GB/s inputs did. A guard tested only with
1e18 would prove nothing the day it regressed — it would just eat the runner.
"""

from __future__ import annotations

import json
import socket
import threading

import pytest

from mts.core.pitch import Pitch
from mts.limits import MAX_GRID_CELLS, MAX_SPAN_BEATS
from mts.mcp import tools
from mts.mcp.tools import _canonical_sequence
from mts.temporal.meter import MeterMap, TimeSignature
from mts.temporal.sequence import Event, Sequence


def _two_notes(span):
    return [[0, 1, 60], [span - 1, 1, 64]]


# --- core invariants ------------------------------------------------------------

@pytest.mark.parametrize("onset,duration", [
    (float("nan"), 1.0), (0.0, float("nan")), (float("inf"), 1.0), (0.0, float("inf")),
])
def test_event_rejects_non_finite_time(onset, duration):
    """NaN passed the old range checks (every comparison with NaN is False)."""
    with pytest.raises(ValueError, match="finite"):
        Event(onset=onset, duration=duration, pitch=Pitch.from_midi(60))


def test_sequence_rejects_a_span_over_the_limit():
    with pytest.raises(ValueError, match="MAX_SPAN_BEATS"):
        _canonical_sequence(_two_notes(MAX_SPAN_BEATS + 10))
    _canonical_sequence(_two_notes(MAX_SPAN_BEATS))          # the limit itself is allowed


# --- the grid budget, at each of its sites --------------------------------------

def test_key_tracking_hop_budget():
    span = 2_000
    hop = span / (MAX_GRID_CELLS * 1.05)                     # ~105k windows
    with pytest.raises(ValueError, match="key tracking.*MAX_GRID_CELLS"):
        tools.key_tracking(events=_two_notes(span), window_beats=8.0, hop_beats=hop)


def test_meter_tracking_hop_budget():
    span = 2_000
    hop = span / (MAX_GRID_CELLS * 1.05)
    with pytest.raises(ValueError, match="meter tracking.*MAX_GRID_CELLS"):
        tools.meter_tracking(events=[[i, 0.5, 60] for i in range(0, span, 4)],
                             window_beats=16.0, hop_beats=hop)


def test_segmentation_subdivision_budget():
    with pytest.raises(ValueError, match="chord segmentation.*subdivisions"):
        tools.segment_chords(events=_two_notes(4), subdivisions=MAX_GRID_CELLS + 1)


def test_groove_slot_budget():
    with pytest.raises(ValueError, match="groove extraction"):
        tools.extract_groove(events=[[0, 0.5, 60], [0.5, 0.5, 62]], base_unit_beats=0.5,
                             loop_length_beats=0.5 * (MAX_GRID_CELLS + 1))


def test_bar_enumeration_budget():
    """A MIDI time-signature byte can encode a denominator up to 2**255; at
    4/2**19 a 4-beat span already needs 131,072 bars."""
    seq = Sequence.from_events(
        [Event(onset=0.0, duration=4.0, pitch=Pitch.from_midi(60))],
        meter=MeterMap.constant(4, 2**19),
    )
    with pytest.raises(ValueError, match="bar enumeration"):
        seq.meter.bar_spans(seq.duration_beats)


# --- the boundary validator -----------------------------------------------------

def test_validator_rejects_type_confusion_as_a_caller_error():
    with pytest.raises(ValueError, match="pcs must be"):
        tools.set_class_info(pcs={"k": 1})
    with pytest.raises(ValueError, match="path must be a string"):
        tools.midi_file_analysis(path=7)        # open(7) would read fd 7 of the server


def test_validator_accepts_integral_floats_like_the_stdio_door():
    assert tools.scale_analysis(scale_name="Ionian", tonic=0.0)
    with pytest.raises(ValueError):
        tools.scale_analysis(scale_name="Ionian", tonic=3.5)   # int() used to truncate it


def test_validator_rejects_non_finite_numbers_anywhere():
    with pytest.raises(ValueError, match="finite"):
        tools.key_tracking(events=json.loads("[[0, 1e999, 60]]"))   # valid JSON → inf


def test_scale_names_accepts_note_names_on_the_stdio_door_too():
    """Was a door-dependent bug: `list[int]` made pydantic reject the note names
    the docstring promises, while the bridge and import accepted them."""
    pytest.importorskip("mcp")
    from mcp.server.fastmcp.utilities.func_metadata import func_metadata

    func_metadata(tools.scale_names).arg_model.model_validate({"pcs": ["C", "E", "G"]})


def test_validate_ruleset_reports_instead_of_raising():
    """Its contract is to report every error as data — even "not an object"."""
    report = tools.validate_ruleset(ruleset="not a ruleset")
    assert report["valid"] is False and report["errors"]


# --- file and name boundaries ---------------------------------------------------

def test_missing_caller_file_is_the_callers_error():
    with pytest.raises(ValueError, match="could not read the MIDI file"):
        tools.midi_file_analysis(path="/nonexistent/x.mid")


def test_overlong_library_name_is_refused_before_open():
    """It used to reach open() and leak the absolute install path in the error."""
    import mts
    from pathlib import Path

    with pytest.raises(ValueError, match="at most 128") as info:
        tools.load_named_ruleset(name="a" * 5000)
    # Check for THIS machine's real paths rather than spelling out home-path
    # prefixes — a literal prefix pair on one line trips the leak gate's
    # pattern, and the real paths are the stronger assertion anyway.
    for secret in (str(Path.home()), str(Path(mts.__file__).resolve().parents[1])):
        assert secret not in str(info.value)


def test_malformed_transition_matrix_is_the_callers_error():
    with pytest.raises(ValueError, match="malformed transition matrix"):
        tools.transition_cross_entropy(matrix={"zz": 1}, held_out_corpus=[[[0, "maj"]]])


# --- the HTTP bridge ------------------------------------------------------------

@pytest.fixture()
def bridge_port():
    from mts.mcp.bridge import make_server

    server = make_server("127.0.0.1", 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server.server_address[1]
    server.shutdown()


def _status(port, content_length: bytes) -> bytes:
    body = b'{"pcs":[0,4,7]}'
    s = socket.create_connection(("127.0.0.1", port))
    s.settimeout(3)
    s.sendall(b"POST /call/set_class_info HTTP/1.1\r\nHost: x\r\nContent-Length: "
              + content_length + b"\r\n\r\n" + body)
    out = b""
    try:
        while chunk := s.recv(4096):
            out += chunk
    except socket.timeout:
        out += b"<<no response>>"
    s.close()
    return out.split(b"\r\n")[0]


@pytest.mark.parametrize("length,expected", [
    (b"15", b" 200 "), (b"abc", b" 400 "), (b"-1", b" 400 "), (b"1000000000", b" 413 "),
])
def test_bridge_content_length(bridge_port, length, expected):
    """Each bad form was live: no response, a blocked read, an unbounded wait."""
    assert expected in _status(bridge_port, length)
