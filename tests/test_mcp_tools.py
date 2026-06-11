"""Phase 4: MCP tool surface (pure functions — no SDK required)."""

import json

import pytest

from mts.mcp import tools


def _json_safe(payload):
    json.dumps(payload)
    return payload


# --- catalog discovery -----------------------------------------------------------

def test_catalog_discovery_lists_canonical_entries_once():
    scales = _json_safe(tools.list_scales())
    names = [s["name"] for s in scales]
    assert "Ionian" in names
    assert len(names) == len(set(names))  # aliases don't duplicate entries
    qualities = _json_safe(tools.list_chord_qualities())
    assert any(q["name"] == "maj7" for q in qualities)


# --- identity tools ----------------------------------------------------------------

def test_chord_analysis_accepts_note_names():
    result = _json_safe(tools.chord_analysis("C", "maj7"))
    assert result["mask"] == sum(1 << pc for pc in (0, 4, 7, 11))
    assert result["set_class"]["prime_form"] == [0, 1, 5, 8]


def test_parse_chord_round_trips_notation():
    result = _json_safe(tools.parse_chord("C3[0,4,7]"))
    assert result["root_pc"] == 0
    # asdict preserves tuples; they serialize to JSON arrays on the wire.
    assert tuple(result["spec"]["intervals"]) == (0, 4, 7)


def test_scale_analysis_by_name_or_degrees():
    by_name = tools.scale_analysis(scale_name="Ionian")
    by_degrees = tools.scale_analysis(degrees=[0, 2, 4, 5, 7, 9, 11])
    assert by_name["mask"] == by_degrees["mask"]
    with pytest.raises(ValueError, match="exactly one"):
        tools.scale_analysis(scale_name="Ionian", degrees=[0, 2, 4])
    with pytest.raises(ValueError, match="list_scales"):
        tools.scale_analysis(scale_name="Nope")


def test_set_class_info():
    info = _json_safe(tools.set_class_info([0, 4, 7, 10]))
    assert info["prime_form"] == [0, 2, 5, 8]
    assert len(info["dft_magnitudes"]) == 6


def test_interpretations_surface_equivalence():
    result = _json_safe(tools.interpretations([0, 4, 7, 9]))
    namings = {(i["root_pc"], i["quality"]) for i in result["interpretations"]}
    assert {(0, "maj6"), (9, "min7")} <= namings


# --- contextual tools -----------------------------------------------------------------

def test_name_pcs_with_and_without_context():
    in_key = _json_safe(tools.name_pcs([0, 4, 7, 9], tonic="A", key_name="Aeolian",
                                       realization_midi=[45, 60, 64, 67]))
    assert in_key["chosen"]["interpretation"]["root_pc"] == 9
    assert in_key["is_ambiguous"] is False
    bare = tools.name_pcs([0, 4, 7, 9])
    assert bare["context"] is None
    assert bare["is_ambiguous"] is True


def test_key_name_requires_tonic():
    with pytest.raises(ValueError, match="needs a tonic"):
        tools.name_pcs([0, 4, 7], key_name="Ionian")


def test_key_induction_and_combined_naming():
    weights = [0.0] * 12
    for pc, v in {0: 4.0, 2: 1.0, 4: 2.0, 5: 1.0, 7: 3.0, 9: 1.0, 11: 1.0}.items():
        weights[pc] = v
    keys = _json_safe(tools.key_induction(weights))
    assert (keys["candidates"][0]["tonic_pc"], keys["candidates"][0]["mode"]) == (0, "major")
    combined = _json_safe(tools.name_pcs_in_inferred_keys([0, 4, 7, 9], weights))
    assert combined["per_key"][0]["naming"]["context"]["tonic_pc"] == 0


def test_chord_in_key_and_voice_leading():
    placed = _json_safe(tools.chord_in_key("D", "min7", tonic="C", key_name="Ionian"))
    assert placed["root_degree"] == 1
    vl = _json_safe(tools.voice_leading_distance([0, 4, 7], [5, 9, 0]))
    assert vl["distance"] == 3


# --- register & generative -----------------------------------------------------------------

def test_voicing_analysis_requires_notes():
    result = _json_safe(tools.voicing_analysis([48, 64, 67, 72], root="C"))
    assert result["bass_midi"] == 48
    with pytest.raises(ValueError, match="MIDI note"):
        tools.voicing_analysis([])


def test_voicing_suggestions_marked_generative():
    result = _json_safe(tools.voicing_suggestions("C", "maj7"))
    assert any(entry["label"] == "closed" for entry in result["entries"])
    assert "GENERATIVE" in tools.voicing_suggestions.__doc__


def test_quality_comparison_and_brief():
    _json_safe(tools.quality_comparison("maj7", "min7"))
    brief = _json_safe(tools.quality_brief("maj7"))
    assert brief["interval_fingerprint"]


# --- the A1 pipeline tool ----------------------------------------------------------------------

def test_midi_file_analysis_end_to_end(tmp_path):
    import mido

    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
    for chord in ([60, 64, 67], [65, 69, 72], [67, 71, 74], [60, 64, 67]):
        for i, note in enumerate(chord):
            track.append(mido.Message("note_on", note=note, velocity=80, time=0))
        for i, note in enumerate(chord):
            track.append(mido.Message("note_off", note=note, velocity=0, time=480 if i == 0 else 0))
    path = tmp_path / "progression.mid"
    mid.save(path)

    result = _json_safe(tools.midi_file_analysis(str(path)))
    assert (result["key"]["candidates"][0]["tonic_pc"], result["key"]["candidates"][0]["mode"]) == (0, "major")
    records = result["dataset"]["records"]
    assert len(records) == 4
    # Every segment's naming is conditional on the inferred C-major context.
    assert all(r["analysis"]["naming"]["context"]["tonic_pc"] == 0 for r in records)
    first = records[0]["analysis"]["naming"]["chosen"]["interpretation"]
    assert (first["root_pc"], first["quality"]) == (0, "maj")


# --- server wiring (only when the optional SDK is installed) ------------------------------------

def test_build_server_registers_all_tools():
    pytest.importorskip("mcp")
    from mts.mcp.server import build_server

    server = build_server()
    assert server is not None


def test_tools_have_docstrings_for_schema_derivation():
    for tool in tools.TOOLS:
        assert tool.__doc__, f"{tool.__name__} needs a docstring (it becomes the tool description)"
