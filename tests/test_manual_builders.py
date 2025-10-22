import pytest

from mts.analysis.builders import (
    ManualScaleBuilder,
    ManualChordBuilder,
    SESSION_SCALES,
    SESSION_CHORDS,
    register_scale,
    register_chord,
    degrees_from_mask,
    mask_from_text,
    match_scale,
    match_chord,
)
from mts.analysis import ChordAnalysisRequest, analyze_chord
from mts.core.chord import Chord
from mts.io.loaders import load_scales, load_chord_qualities


@pytest.fixture(autouse=True)
def _clear_sessions():
    """Ensure session registries do not leak between tests."""

    SESSION_SCALES.clear()
    SESSION_CHORDS.clear()
    yield
    SESSION_SCALES.clear()
    SESSION_CHORDS.clear()


def test_register_scale_matches_catalog():
    catalog = load_scales()
    result = register_scale(
        ManualScaleBuilder(name=None, degrees=[0, 2, 4, 5, 7, 9, 11]),
        catalog=catalog,
    )
    assert result["match"], "Expected Ionian scale to match the catalog"
    scale = result["scale"]
    assert scale.name == "Ionian"
    assert SESSION_SCALES["Ionian"] is scale


def test_register_scale_placeholder_for_unknown():
    catalog = load_scales()
    custom_degrees = [0, 1, 4, 5, 8]
    result = register_scale(
        ManualScaleBuilder(name=None, degrees=custom_degrees),
        catalog=catalog,
    )
    scale = result["scale"]
    assert not result["match"]
    assert scale.name.startswith("ManualScale-")
    assert sorted(scale.degrees) == sorted(custom_degrees)
    assert scale.name in SESSION_SCALES


def test_mask_helpers_round_trip():
    mask = mask_from_text("0b101010101010")
    degrees = degrees_from_mask(mask)
    assert degrees == [1, 3, 5, 7, 9, 11]
    reconstructed = 0
    for pc in degrees:
        reconstructed |= 1 << pc
    assert reconstructed == mask


def test_register_chord_runs_analysis():
    catalog = load_chord_qualities()
    builder = ManualChordBuilder(name=None, intervals=[0, 1, 4])
    result = register_chord(builder, catalog=catalog)
    quality = result["quality"]
    assert not result["match"]
    assert quality.name.startswith("ManualChord-")

    chord = Chord.from_quality(0, quality)
    analysis = analyze_chord(
        ChordAnalysisRequest(
            chord=chord,
            include_inversions=True,
            include_voicings=True,
            include_enharmonics=False,
        )
    )
    assert len(analysis["inversions"]) == len(quality.intervals)
    assert "closed" in analysis["voicings"]
    assert quality.name in SESSION_CHORDS


def test_match_helpers_deduplicate_results():
    catalog = load_scales()
    matches = match_scale([0, 2, 4, 5, 7, 9, 11], catalog)
    names = [scale.name for scale in matches]
    assert names == sorted(set(names)), "Match results should not contain duplicates"
    assert "Ionian" in names

    chord_catalog = load_chord_qualities()
    chord_matches = match_chord([0, 4, 7, 11], chord_catalog)
    chord_names = [quality.name for quality in chord_matches]
    assert chord_names == sorted(set(chord_names))
    assert "maj7" in chord_names


def test_loaders_include_session_objects():
    custom_scale = register_scale(
        ManualScaleBuilder(name="CustomScale", degrees=[0, 2, 5, 6, 9]),
    )["scale"]
    custom_chord = register_chord(
        ManualChordBuilder(name="CustomChord", intervals=[0, 2, 5, 9]),
    )["quality"]

    all_scales = load_scales()
    all_chords = load_chord_qualities()

    assert custom_scale.name in all_scales
    assert custom_chord.name in all_chords
