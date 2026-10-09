"""TONALITY_MIDI_ROOTS — the allowed-directories policy for file-reading tools.

Julian's ruling (2026-10-09, BOUNDARIES.md surface 3): an env-var allowlist with
an UNRESTRICTED default. These pin both halves — the default must not break
direct use, and an opted-in deployment must not be escapable by `..`, a symlink,
or a sibling directory that merely shares a name prefix.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from mts.mcp import tools

FIXTURE = Path(__file__).parent / "golden" / "fixtures" / "pipeline.mid"
FILE_TOOLS = (tools.midi_file_analysis, tools.piano_roll_view)


@pytest.fixture
def library(tmp_path):
    """An allowed dir holding a real MIDI file, and a forbidden sibling."""
    allowed = tmp_path / "allowed"
    forbidden = tmp_path / "allowed-not"   # shares the prefix: string-prefix bug bait
    for d in (allowed, forbidden):
        d.mkdir()
        shutil.copy(FIXTURE, d / "song.mid")
    return allowed, forbidden


@pytest.mark.parametrize("tool", FILE_TOOLS)
def test_unset_means_unrestricted(tool, monkeypatch, library):
    monkeypatch.delenv(tools.MIDI_ROOTS_ENV, raising=False)
    assert tool(path=str(library[1] / "song.mid"))


@pytest.mark.parametrize("tool", FILE_TOOLS)
def test_empty_means_unrestricted(tool, monkeypatch, library):
    monkeypatch.setenv(tools.MIDI_ROOTS_ENV, "")
    assert tool(path=str(library[1] / "song.mid"))


@pytest.mark.parametrize("tool", FILE_TOOLS)
def test_inside_an_allowed_root_is_read(tool, monkeypatch, library):
    monkeypatch.setenv(tools.MIDI_ROOTS_ENV, str(library[0]))
    assert tool(path=str(library[0] / "song.mid"))


@pytest.mark.parametrize("tool", FILE_TOOLS)
def test_outside_every_root_is_refused(tool, monkeypatch, library):
    """The must-fail control: remove the guard and this reads the file."""
    monkeypatch.setenv(tools.MIDI_ROOTS_ENV, str(library[0]))
    with pytest.raises(ValueError, match="outside the directories this server allows"):
        tool(path=str(library[1] / "song.mid"))


def test_a_sibling_sharing_the_prefix_is_not_inside(monkeypatch, library):
    """`/x/allowed-not` starts with the string `/x/allowed` but is not inside it."""
    allowed, forbidden = library
    assert str(forbidden).startswith(str(allowed))
    monkeypatch.setenv(tools.MIDI_ROOTS_ENV, str(allowed))
    with pytest.raises(ValueError, match="outside"):
        tools.midi_file_analysis(path=str(forbidden / "song.mid"))


def test_parent_references_cannot_climb_out(monkeypatch, library):
    allowed, forbidden = library
    monkeypatch.setenv(tools.MIDI_ROOTS_ENV, str(allowed))
    with pytest.raises(ValueError, match="outside"):
        tools.midi_file_analysis(path=str(allowed / ".." / forbidden.name / "song.mid"))


def test_a_symlink_inside_cannot_point_outside(monkeypatch, library):
    allowed, forbidden = library
    link = allowed / "escape.mid"
    link.symlink_to(forbidden / "song.mid")
    monkeypatch.setenv(tools.MIDI_ROOTS_ENV, str(allowed))
    with pytest.raises(ValueError, match="outside"):
        tools.midi_file_analysis(path=str(link))


def test_any_of_several_roots_admits(monkeypatch, library, tmp_path):
    other = tmp_path / "elsewhere"
    other.mkdir()
    monkeypatch.setenv(tools.MIDI_ROOTS_ENV, os.pathsep.join([str(other), str(library[0])]))
    assert tools.midi_file_analysis(path=str(library[0] / "song.mid"))


@pytest.mark.parametrize("value", [os.pathsep, "   ", "relative/dir"])
def test_a_set_but_unusable_variable_fails_closed(value, monkeypatch, library):
    """An operator who set the variable meant to restrict; a typo must not open
    everything up."""
    monkeypatch.setenv(tools.MIDI_ROOTS_ENV, value)
    with pytest.raises(ValueError, match="disabled until"):
        tools.midi_file_analysis(path=str(library[0] / "song.mid"))


def test_the_refusal_never_lists_the_allowed_roots(monkeypatch, library):
    allowed, forbidden = library
    monkeypatch.setenv(tools.MIDI_ROOTS_ENV, str(allowed))
    with pytest.raises(ValueError) as info:
        tools.midi_file_analysis(path=str(forbidden / "song.mid"))
    # The forbidden path is the caller's own argument, and it contains the allowed
    # dir as a string prefix, so check for the root's distinct form: as a directory.
    assert str(allowed) + os.sep not in str(info.value).replace(str(forbidden), "")


def test_a_refused_path_is_never_opened(monkeypatch, library):
    """Policy before I/O: a refused path must not even reach the reader."""
    import mts.dataset.pipelines as pipelines

    def _must_not_open(*_a, **_k):
        raise AssertionError("the reader ran for a refused path")

    monkeypatch.setattr(pipelines, "analyze_midi_file", _must_not_open)
    monkeypatch.setenv(tools.MIDI_ROOTS_ENV, str(library[0]))
    with pytest.raises(ValueError, match="outside"):
        tools.midi_file_analysis(path=str(library[1] / "song.mid"))
