"""Tests for the generative named-voicing vocabulary (suggest_voicings)."""

from mts.analysis.voicings import suggest_voicings
from mts.core.chord import Chord
from mts.io.loaders import load_chord_qualities


def _chord(name: str) -> Chord:
    return Chord.from_quality(0, load_chord_qualities()[name])


def test_closed_is_the_plain_stack():
    vs = suggest_voicings(_chord("maj7"))
    closed = vs.get("closed")
    assert closed is not None
    assert closed.semitones_from_root == [0, 4, 7, 11]
    assert set(closed.intervals_mod_12) == {0, 4, 7, 11}


def test_seventh_chord_has_the_rich_vocabulary():
    labels = set(suggest_voicings(_chord("maj7")).labels)
    # A four-note 7th chord supports drops, spread, rootless, and shell.
    assert {"closed", "drop2", "drop3", "spread", "rootless-a", "rootless-b", "shell"} <= labels


def test_triad_excludes_voicings_that_need_four_notes_or_a_seventh():
    labels = set(suggest_voicings(_chord("maj")).labels)
    assert "closed" in labels
    assert "drop3" not in labels       # needs a 4th voice
    assert "rootless-a" not in labels  # needs a 7th
    assert "shell" not in labels       # needs a 3rd and a 7th


def test_rootless_omits_the_root():
    rootless = suggest_voicings(_chord("maj7")).get("rootless-a")
    assert rootless is not None
    assert 0 not in rootless.intervals_mod_12  # root dropped


def test_shell_is_root_third_seventh():
    shell = suggest_voicings(_chord("maj7")).get("shell")
    assert shell is not None
    assert shell.intervals_mod_12 == [0, 4, 11]


def test_no_duplicate_spacings():
    entries = suggest_voicings(_chord("maj7")).entries
    fingerprints = [tuple(e.semitones_from_root) for e in entries]
    assert len(fingerprints) == len(set(fingerprints))


def test_dim7_skips_rootless_and_shell():
    # dim7's seventh is a diminished 7th (9 semis), not a min/maj 7th (10/11),
    # so the guide-tone voicings correctly do not apply.
    labels = set(suggest_voicings(_chord("dim7")).labels)
    assert "rootless-a" not in labels
    assert "shell" not in labels
