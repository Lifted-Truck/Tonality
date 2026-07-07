import pytest

from mts.session import (
    ManualScaleBuilder,
    ManualChordBuilder,
    SessionCatalog,
    register_scale,
    register_chord,
    degrees_from_mask,
    mask_from_text,
    match_scale,
    match_chord,
    load_session_catalog,
    save_session_catalog,
)

# Each test owns an explicit session (no library default, RE-6b).
_S = SessionCatalog()
from mts.analysis import ChordAnalysisRequest, analyze_chord, chord_brief
from mts.analysis.voicings import suggest_voicings
from mts.core.chord import Chord
from mts.core.pitch import Pitch
from mts.io.loaders import load_scales, load_chord_qualities


@pytest.fixture(autouse=True)
def _clear_sessions():
    """A fresh session per test (no cross-test leakage)."""
    _S.clear()
    yield
    _S.clear()


def test_register_scale_matches_catalog():
    catalog = load_scales()
    result = register_scale(
        ManualScaleBuilder(name=None, degrees=[0, 2, 4, 5, 7, 9, 11]),
        catalog=catalog,
        session=_S,
    )
    assert result["match"], "Expected Ionian scale to match the catalog"
    scale = result["scale"]
    assert scale.name == "Ionian"
    assert _S.scales["Ionian"] is scale


def test_register_scale_placeholder_for_unknown():
    catalog = load_scales()
    custom_degrees = [0, 1, 4, 5, 8]
    result = register_scale(
        ManualScaleBuilder(name=None, degrees=custom_degrees),
        catalog=catalog,
        session=_S,
    )
    scale = result["scale"]
    assert not result["match"]
    assert scale.name.startswith("ManualScale-")
    assert sorted(scale.degrees) == sorted(custom_degrees)
    assert scale.name in _S.scales
    assert _S.scale_context[scale.name]["scope"] == "abstract"


def test_register_scale_with_note_names():
    catalog = load_scales()
    result = register_scale(
        ManualScaleBuilder(name="NoteScale", degrees=["C", "E", "G"]),
        catalog=catalog,
        session=_S,
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
    result = register_chord(builder, catalog=catalog, session=_S)
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
        )
    )
    assert analysis.inversions is not None
    assert len(analysis.inversions) == len(quality.intervals)
    # analyze_chord is pure-identity: it carries no register and invents none.
    assert not hasattr(analysis, "voicings")
    # Voicings are generative (register is chosen, not analyzed).
    voicings = suggest_voicings(chord)
    assert voicings.get("closed") is not None
    assert quality.name in _S.chords
    assert _S.chord_context[quality.name]["scope"] == "abstract"


def test_register_chord_with_note_names():
    catalog = load_chord_qualities()
    result = register_chord(
        ManualChordBuilder(name="NoteChord", intervals=["C", "Eb", "G"]),
        catalog=catalog,
        session=_S,
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
    result = register_chord(builder, catalog={}, session=_S)
    quality = result["quality"]
    spec = result["spec"]
    context = _S.chord_context[quality.name]
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
        session=_S,
    )["scale"]
    custom_chord = register_chord(
        ManualChordBuilder(name="CustomChord", intervals=[0, 2, 5, 9]),
        session=_S,
    )["quality"]

    # RE-6b: to see session objects you pass the session (no library default).
    all_scales = load_scales(session=_S)
    all_chords = load_chord_qualities(session=_S)

    assert custom_scale.name in all_scales
    assert custom_chord.name in all_chords


def test_session_persistence_round_trip(tmp_path):
    session_path = tmp_path / "session.json"
    register_scale(
        ManualScaleBuilder(name="PersistScale", degrees=[0, 3, 6]),
        session=_S,
        persist=True,
        session_path=session_path,
    )
    register_chord(
        ManualChordBuilder(name="PersistChord", intervals=[0, 2, 7]),
        session=_S,
        persist=True,
        session_path=session_path,
    )
    assert session_path.exists()

    _S.scales.clear()
    _S.chords.clear()
    load_session_catalog(_S, session_path)
    assert "PersistScale" in _S.scales
    assert "PersistChord" in _S.chords
    assert _S.scale_context["PersistScale"]["scope"] == "abstract"
    assert _S.chord_context["PersistChord"]["scope"] == "abstract"


def test_chord_brief_contains_expected_components():
    catalog = load_chord_qualities()
    brief = chord_brief(catalog["maj7"])
    assert "ic" in brief.interval_fingerprint
    assert brief.compatible_scales
    assert isinstance(brief.compatible_scales, list)


# --- RE-3g: loads itemize what they skip; nothing vanishes silently ----------------------


def test_corrupt_session_file_is_reported_not_swallowed(tmp_path):

    path = tmp_path / "corrupt.json"
    path.write_text("{not json", encoding="utf-8")
    report = SessionCatalog().load(path)
    assert report.file_found is True
    assert report.file_error is not None and "unreadable" in report.file_error
    assert report.scales_loaded == report.chords_loaded == 0


def test_bad_entries_are_itemized_and_good_ones_still_load(tmp_path):
    import json as _json


    path = tmp_path / "session.json"
    path.write_text(_json.dumps({
        "scales": [
            {"name": "Good", "degrees": [0, 2, 4]},
            {"name": "Bad", "degrees": ["Zz", 4]},   # unparseable degree token
            {"degrees": [0, 1]},                        # nameless
        ],
        "chords": [{"name": "GoodChord", "intervals": [0, 4, 7]}],
    }), encoding="utf-8")
    catalog = SessionCatalog()
    report = catalog.load(path)
    assert "Good" in catalog.scales and "GoodChord" in catalog.chords
    assert report.scales_loaded == 1 and report.chords_loaded == 1
    assert [(s["kind"], s["name"]) for s in report.skipped] == [
        ("scale", "Bad"), ("scale", None),
    ]
    assert report.file_error is None
    report.to_dict()  # JSON-ready


def test_missing_session_file_is_a_clean_empty_report(tmp_path):

    report = SessionCatalog().load(tmp_path / "absent.json")
    assert report.file_found is False and report.file_error is None
    assert report.skipped == []


def test_function_mappings_carry_role_subtype():
    # RE-3g: the generator emits role_subtype; the loader used to drop it.
    from mts.io.loaders import load_function_mappings

    mappings = load_function_mappings("major")
    assert all(hasattr(m, "role_subtype") for m in mappings)
    subtypes = {m.role_subtype for m in mappings}
    assert None in subtypes  # plain functions carry no subtype
    # the tonic-prolongation variants survive the load
    assert any(s is not None for s in subtypes)
