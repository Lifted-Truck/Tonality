import pytest

from mts.analysis.builders import (
    ManualScaleBuilder,
    ManualChordBuilder,
    SESSION_SCALES,
    SESSION_CHORDS,
    SESSION_SCALE_CONTEXT,
    SESSION_CHORD_CONTEXT,
    SESSION_CHORD_SPECS,
    register_scale,
    register_chord,
    degrees_from_mask,
    mask_from_text,
    match_scale,
    match_chord,
    load_session_catalog,
    save_session_catalog,
)
from mts.analysis import ChordAnalysisRequest, analyze_chord, chord_brief
from mts.core.chord import Chord
from mts.core.pitch import Pitch
from mts.io.loaders import load_scales, load_chord_qualities


@pytest.fixture(autouse=True)
def _clear_sessions():
    """Ensure session registries do not leak between tests."""

    SESSION_SCALES.clear()
    SESSION_CHORDS.clear()
    SESSION_SCALE_CONTEXT.clear()
    SESSION_CHORD_CONTEXT.clear()
    SESSION_CHORD_SPECS.clear()
    yield
    SESSION_SCALES.clear()
    SESSION_CHORDS.clear()
    SESSION_SCALE_CONTEXT.clear()
    SESSION_CHORD_CONTEXT.clear()
    SESSION_CHORD_SPECS.clear()


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
    assert SESSION_SCALE_CONTEXT[scale.name]["scope"] == "abstract"


def test_register_scale_with_note_names():
    catalog = load_scales()
    result = register_scale(
        ManualScaleBuilder(name="NoteScale", degrees=["C", "E", "G"]),
        catalog=catalog,
    )
    scale = result["scale"]
    assert list(scale.degrees) == [0, 4, 7]


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
    spec = result["spec"]
    assert not result["match"]
    assert quality.name.startswith("ManualChord-")
    assert spec.quality_name == quality.name
    assert spec.scope == "abstract"
    assert spec.intervals == tuple(sorted({0, 1, 4}))

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
    assert SESSION_CHORD_CONTEXT[quality.name]["scope"] == "abstract"


def test_register_chord_with_note_names():
    catalog = load_chord_qualities()
    result = register_chord(
        ManualChordBuilder(name="NoteChord", intervals=["C", "Eb", "G"]),
        catalog=catalog,
    )
    quality = result["quality"]
    spec = result["spec"]
    assert list(quality.intervals) == [0, 3, 7]
    assert spec.tokens == ("C", "Eb", "G")
    assert spec.scope == "note"


def test_register_chord_with_absolute_tokens_updates_context():
    builder = ManualChordBuilder(
        name="AbsChord",
        intervals=[0, 1, 4],
        context="absolute",
        tokens=("C3", "Db3", "E3"),
        absolute=(
            Pitch.from_components(pc=0, octave=3),
            Pitch.from_components(pc=1, octave=3),
            Pitch.from_components(pc=4, octave=3),
        ),
    )
    result = register_chord(builder, catalog={})
    quality = result["quality"]
    spec = result["spec"]
    context = SESSION_CHORD_CONTEXT[quality.name]
    assert context["scope"] == "absolute"
    assert context["tokens"] == ["C3", "Db3", "E3"]
    assert context["absolute_midi"] == [48, 49, 52]
    assert spec.scope == "absolute"
    assert spec.absolute_midi == (48, 49, 52)
    assert spec.tokens == ("C3", "Db3", "E3")


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


def test_session_persistence_round_trip(tmp_path):
    session_path = tmp_path / "session.json"
    register_scale(
        ManualScaleBuilder(name="PersistScale", degrees=[0, 3, 6]),
        persist=True,
        session_path=session_path,
    )
    register_chord(
        ManualChordBuilder(name="PersistChord", intervals=[0, 2, 7]),
        persist=True,
        session_path=session_path,
    )
    assert session_path.exists()

    SESSION_SCALES.clear()
    SESSION_CHORDS.clear()
    load_session_catalog(session_path)
    assert "PersistScale" in SESSION_SCALES
    assert "PersistChord" in SESSION_CHORDS
    assert SESSION_SCALE_CONTEXT["PersistScale"]["scope"] == "abstract"
    assert SESSION_CHORD_CONTEXT["PersistChord"]["scope"] == "abstract"


def test_chord_brief_contains_expected_components():
    catalog = load_chord_qualities()
    brief = chord_brief(catalog["maj7"])
    assert "ic" in brief.interval_fingerprint
    assert brief.compatible_scales
    assert isinstance(brief.compatible_scales, list)
