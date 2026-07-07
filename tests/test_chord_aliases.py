"""Tests for chord-quality aliases (parity with scale aliases)."""

from mts.notation import parse_chord_spec
from mts.core.quality import ChordQuality
from mts.io.loaders import load_chord_qualities


def test_from_intervals_normalizes_aliases():
    q = ChordQuality.from_intervals("x", [0, 4, 7], aliases=["foo", " foo ", "", "bar"])
    assert q.aliases == ("foo", "bar")  # de-duped, stripped, blanks dropped


def test_catalog_registers_alias_keys_to_same_object():
    cat = load_chord_qualities()
    assert cat["major"] is cat["maj"]
    assert cat["m"] is cat["min"]
    assert cat["dom7"] is cat["7"]
    assert cat["maj"].aliases == ("major", "M")


def test_parse_resolves_via_alias():
    assert parse_chord_spec("C:major").spec.quality_name == "maj"
    assert parse_chord_spec("A:m7").spec.quality_name == "min7"
    assert parse_chord_spec("G:dom7").spec.quality_name == "7"


def test_classification_reports_canonical_names_not_aliases():
    # Alias keys must not show up as duplicate matches.
    matches = parse_chord_spec("[0,4,7]").spec.quality_matches
    assert "maj" in matches
    assert "major" not in matches
    assert "M" not in matches


def test_aliases_do_not_collide_with_names_or_each_other():
    # The loader raises on duplicates; a clean load proves the seed data is sane.
    cat = load_chord_qualities()
    # Every alias resolves to a quality whose aliases include it.
    for key, quality in cat.items():
        if key != quality.name:
            assert key in quality.aliases
