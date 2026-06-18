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


def test_catalog_containment_finds_scales_and_qualities_with_roots():
    result = _json_safe(tools.catalog_containment([0, 4, 7]))
    ionian_roots = {s["root_pc"] for s in result["scales"] if s["name"] == "Ionian"}
    assert ionian_roots == {0, 5, 7}
    assert any(
        q["name"] == "maj" and q["root_pc"] == 0 and q["is_exact"]
        for q in result["qualities"]
    )
    with pytest.raises(ValueError):
        tools.catalog_containment([])


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


def test_key_induction_profile_version_selector():
    # D911-24-shaped vector: the default (now tkp-cbms.1) recovers A minor; pinning
    # the legacy kk-1982.1 reproduces the old A-major miss. Result cites the profile.
    w = [51.26562, 0, 14.62708, 0.14062, 265.62917, 4.8125, 0, 0,
         39.17083, 270.78125, 0, 55.02187]
    default = _json_safe(tools.key_induction(w))
    kk = _json_safe(tools.key_induction(w, profile_version="kk-1982.1"))
    assert default["profile_version"] == "tkp-cbms.1"
    assert (default["candidates"][0]["tonic_pc"], default["candidates"][0]["mode"]) == (9, "minor")
    assert kk["profile_version"] == "kk-1982.1"
    assert (kk["candidates"][0]["tonic_pc"], kk["candidates"][0]["mode"]) == (9, "major")
    with pytest.raises(ValueError, match="Unknown key-profile version"):
        tools.key_induction(w, profile_version="no-such-version")


def test_key_tracking_over_event_triples():
    events = []
    for base, tonic in ((0, 60), (16, 66)):  # C major, then F# major
        for cycle in (0, 8):
            for offset, chord_root in ((0, 0), (2, 5), (4, 7), (6, 0)):
                onset = base + cycle + offset
                events += [[onset, 2, tonic + chord_root + iv] for iv in (0, 4, 7)]
    result = _json_safe(tools.key_tracking(events))
    regions = result["regions"]
    assert (regions[0]["tonic_pc"], regions[0]["mode"]) == (0, "major")
    assert (regions[-1]["tonic_pc"], regions[-1]["mode"]) == (6, "major")
    assert result["profile_version"]
    with pytest.raises(ValueError, match="onset_beats"):
        tools.key_tracking([[0, 1]])  # malformed triple


def test_voice_pair_motion_over_event_quadruples():
    events = [
        [0, 1, 60, "bass"], [1, 1, 62, "bass"],
        [0, 1, 67, "tenor"], [1, 1, 69, "tenor"],
    ]
    result = _json_safe(tools.voice_pair_motion(events))
    assert result["voices"] == ["bass", "tenor"]
    transition = result["transitions"][0]
    assert (transition["motion"], transition["interval_class_to"]) == ("parallel", 7)
    with pytest.raises(ValueError, match="voice_label"):
        tools.voice_pair_motion([[0, 1, 60]])  # missing the voice


def test_melodic_analysis_with_and_without_harmony():
    events = [[0, 1, 60], [1, 1, 62], [2, 1, 64]]
    bare = _json_safe(tools.melodic_analysis(events))
    assert bare["parsons_code"] == "*uu"
    assert bare["notes"][1]["nht_type"] is None  # no harmony, no claim
    typed = _json_safe(
        tools.melodic_analysis(events, harmony=[[0, 4, [0, 4, 7]]])
    )
    assert typed["notes"][1]["nht_type"] == "passing"
    with pytest.raises(ValueError, match="onset_beats"):
        tools.melodic_analysis([[0, 1]])
    with pytest.raises(ValueError, match="harmony span"):
        tools.melodic_analysis(events, harmony=[[0, 4]])


def test_rhythmic_analysis_with_meter():
    events = [[0, 1.5, 60], [1.5, 2.5, 62]]  # Charleston figure in 4/4
    result = _json_safe(tools.rhythmic_analysis(events))
    assert result["placements"] == ["downbeat", "offbeat"]
    assert result["syncopation_count"] == 1
    compound = _json_safe(
        tools.rhythmic_analysis([[1.5, 0.5, 60]], numerator=6, denominator=8)
    )
    assert compound["placements"] == ["beat"]  # the second dotted-quarter beat
    with pytest.raises(ValueError, match="onset_beats"):
        tools.rhythmic_analysis([[0, 1]])


def test_swing_analysis_estimates_feel():
    swung = []
    for b in range(4):  # triplet-position eighths, 2:1
        swung += [[b, 2 / 3, 60], [b + 2 / 3, 1 / 3, 62]]
    result = _json_safe(tools.swing_analysis(swung))
    assert result["feel"] == "swung"
    assert result["swing_ratio"] == pytest.approx(2.0)
    assert result["prior_version"] == "swing-feel.1"
    with pytest.raises(ValueError, match="too little evidence"):
        tools.swing_analysis([[0, 1, 60], [1, 1, 62]])  # no divisions at all


def test_coalesce_events_repairs_humanized_timing():
    humanized = [[0, 2, 60], [0.013, 1.99, 64], [0.021, 1.98, 67]]
    result = _json_safe(tools.coalesce_events(humanized, onset_window_beats=0.05))
    assert [e[0] for e in result["events"]] == [0.0, 0.0, 0.0]
    assert result["moved_events"] == 2
    assert result["dropped"] == []
    voiced = _json_safe(tools.coalesce_events([[0.01, 1, 60, "lead"]],
                                              onset_window_beats=0,
                                              snap_grid_beats=0.25))
    assert voiced["events"] == [[0.0, 1.0, 60, "lead"]]  # both ends snapped
    with pytest.raises(ValueError, match="Nothing to do"):
        tools.coalesce_events([[0, 1, 60]], onset_window_beats=0)


def test_ruleset_validation_and_evaluation():
    ruleset = {
        "name": "counterpoint-smoke", "version": "t.1",
        "rules": [{
            "id": "no-parallel-perfects", "family": "voice_motion",
            "where": {"motion": "parallel"},
            "forbid": {"interval_class_to": {"in": [0, 7]}},
            "polarity": "hard",
        }],
    }
    check = _json_safe(tools.validate_ruleset(ruleset))
    assert check == {"valid": True, "errors": []}
    bad = _json_safe(tools.validate_ruleset({"name": "x", "version": "1",
                                             "rules": [{"id": "r", "family": "nope"}]}))
    assert bad["valid"] is False and bad["errors"]

    events = [
        [0, 2, 48, "bass"], [2, 2, 50, "bass"],
        [0, 2, 55, "tenor"], [2, 2, 57, "tenor"],
    ]
    report = _json_safe(tools.evaluate_ruleset(ruleset, events))
    assert report["hard_rules_hold"] is False
    assert report["results"][0]["violations"][0]["location"]["voices"] == ["bass", "tenor"]
    with pytest.raises(ValueError, match="onset_beats"):
        tools.evaluate_ruleset(ruleset, [[0, 1]])


def test_ruleset_composition_tools():
    rule_a = {"id": "no-parallel", "family": "voice_motion",
              "forbid": {"motion": "parallel"}, "polarity": "hard"}
    rule_b = {"id": "no-syncopation", "family": "rhythm",
              "forbid": {"is_syncopated": True}, "polarity": "hard"}
    a = {"name": "a", "version": "1", "rules": [rule_a]}
    b = {"name": "b", "version": "1", "rules": [rule_b]}

    combined = _json_safe(tools.combine_rulesets([a, b], name="cp", version="1"))
    assert {r["id"] for r in combined["rules"]} == {"no-parallel", "no-syncopation"}

    spec = _json_safe(tools.specialize_ruleset(a, b, name="strict", version="1"))
    assert spec["added"] == ["no-syncopation"]

    requires = {"id": "must-parallel", "family": "voice_motion",
                "require": {"motion": "parallel"}, "polarity": "hard"}
    cmp = _json_safe(tools.compare_rulesets(a, {"name": "c", "version": "1",
                                                "rules": [requires]}))
    assert len(cmp["contradictions"]) == 1


def test_cadences_detects_formulas():
    # ii - V - I in C major
    result = _json_safe(tools.cadences([["D", "min"], ["G", "maj"], ["C", "maj"]],
                                       tonic="C", mode="major"))
    assert result["mode_supported"] is True
    cad = next(c for c in result["cadences"] if c["type"] == "authentic")
    assert (cad["approach"]["roman"], cad["arrival"]["roman"]) == ("V", "I")
    assert cad["is_final"] is True and cad["evidence"]
    modal = tools.cadences([["G", "maj"], ["C", "maj"]], tonic="C", mode="dorian")
    assert modal["mode_supported"] is False and modal["cadences"] == []
    with pytest.raises(ValueError, match="root, quality"):
        tools.cadences([["C"]], tonic="C")


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


def test_keyboard_view_descriptor():
    result = _json_safe(tools.keyboard_view(60, 72, tonic="D", scale_name="Dorian",
                                            active_pcs=[2, 5, 9]))
    assert result["spec_level"] == "pc_projection"
    d_key = next(k for k in result["keys"] if k["midi"] == 62)
    assert (d_key["is_tonic"], d_key["active"], d_key["degree_index"]) == (True, "pc", 0)
    f_sharp = next(k for k in result["keys"] if k["midi"] == 66)
    assert (f_sharp["in_scale"], f_sharp["is_black"]) == (False, True)
    with pytest.raises(ValueError, match="both or neither"):
        tools.keyboard_view(60, 72, tonic="D")


def test_bracelet_view_descriptor():
    result = _json_safe(tools.bracelet_view([0, 4, 7], tonic="C", scale_name="Ionian"))
    assert result["spec_level"] == "identity_only"
    assert result["active_pcs"] == [0, 4, 7]
    assert result["interval_vector"] == [0, 0, 1, 1, 1, 0]
    by_pc = {p["pc"]: p for p in result["positions"]}
    assert by_pc[2]["in_scale"] and not by_pc[2]["is_active"]
    with pytest.raises(ValueError, match="both or neither"):
        tools.bracelet_view([0, 4, 7], tonic="C")


def test_tonnetz_view_descriptor():
    result = _json_safe(tools.tonnetz_view([0, 4, 7]))
    assert len(result["nodes"]) == 12
    edges = {(e["pc_a"], e["pc_b"], e["axis"]) for e in result["edges"]}
    assert edges == {(0, 7, "P5"), (0, 4, "M3"), (4, 7, "m3")}
    with pytest.raises(ValueError, match="at least one"):
        tools.tonnetz_view([])


def test_chord_network_voice_leading_graph():
    result = _json_safe(tools.chord_network(
        [["C", "maj"], ["C", "aug"], ["E", "min"]], max_distance=1))
    assert result["spec_level"] == "identity_only"
    aug = next(n for n in result["nodes"] if n["quality"] == "aug")
    assert aug["symmetry_order"] == 4  # the hub signal
    # C major connects to both at distance 1
    assert len(result["edges"]) == 2
    assert all(e["distance"] == 1 for e in result["edges"])
    with pytest.raises(ValueError, match="root, quality"):
        tools.chord_network([["C"]])


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
    # local key tracking ships with the pipeline (additive field)
    regions = result["key_regions"]["regions"]
    assert (regions[0]["tonic_pc"], regions[0]["mode"]) == (0, "major")
    without = tools.midi_file_analysis(str(path), include_key_regions=False)
    assert "key_regions" not in without


def test_midi_file_analysis_with_coalescing(tmp_path):
    import mido

    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    # one C-major chord, humanized: onsets spread across ~10 ticks
    track.append(mido.Message("note_on", note=60, velocity=80, time=0))
    track.append(mido.Message("note_on", note=64, velocity=80, time=6))
    track.append(mido.Message("note_on", note=67, velocity=80, time=4))
    track.append(mido.Message("note_off", note=60, velocity=0, time=950))
    track.append(mido.Message("note_off", note=64, velocity=0, time=5))
    track.append(mido.Message("note_off", note=67, velocity=0, time=3))
    path = tmp_path / "humanized.mid"
    mid.save(path)

    raw = tools.midi_file_analysis(str(path), include_key_regions=False)
    assert len(raw["dataset"]["records"]) > 1  # micro-segment fragmentation
    cleaned = _json_safe(tools.midi_file_analysis(
        str(path), include_key_regions=False, coalesce_window_beats=0.05))
    assert len(cleaned["dataset"]["records"]) == 1
    assert cleaned["coalesce"]["onset_window_beats"] == 0.05
    assert cleaned["coalesce"]["moved_events"] >= 2
    assert "coalesce" not in raw


def test_midi_file_analysis_per_region_context(tmp_path):
    import mido

    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    # 16 beats of C major (tonic pedal + I-IV-V-I twice), then the same in F#
    for tonic in (60, 66):
        for _cycle in range(2):
            for root in (0, 5, 7, 0):
                for i, iv in enumerate((0, 4, 7)):
                    track.append(mido.Message("note_on", note=tonic + root + iv,
                                              velocity=80, time=0))
                for i, iv in enumerate((0, 4, 7)):
                    track.append(mido.Message("note_off", note=tonic + root + iv,
                                              velocity=0, time=960 if i == 0 else 0))
    path = tmp_path / "modulating.mid"
    mid.save(path)

    result = _json_safe(tools.midi_file_analysis(str(path)))
    records = result["dataset"]["records"]
    early = [r for r in records if r["placement"]["onset_beats"] < 12]
    late = [r for r in records if r["placement"]["onset_beats"] >= 20]
    assert {r["analytical_context"]["tonic_pc"] for r in early} == {0}
    assert {r["analytical_context"]["tonic_pc"] for r in late} == {6}
    assert all(r["analytical_context"]["margin"] is not None for r in early + late)

    global_only = tools.midi_file_analysis(str(path), per_region_context=False)
    tonics = {r["analytical_context"]["tonic_pc"]
              for r in global_only["dataset"]["records"]}
    assert len(tonics) == 1  # the old single-global-key conditioning


def test_piano_roll_view_end_to_end(tmp_path):
    import mido

    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))  # 120 bpm
    for chord in ([60, 64, 67], [65, 69, 72], [67, 71, 74], [60, 64, 67]):
        for note in chord:
            track.append(mido.Message("note_on", note=note, velocity=80, time=0))
        for i, note in enumerate(chord):
            track.append(mido.Message("note_off", note=note, velocity=0, time=480 if i == 0 else 0))
    path = tmp_path / "progression.mid"
    mid.save(path)

    result = _json_safe(tools.piano_roll_view(str(path)))
    assert result["spec_level"] == "registered_time"
    assert len(result["notes"]) == 12  # 4 triads
    note = result["notes"][0]
    assert note["velocity"] == 80 and note["onset_seconds"] is not None
    assert len(result["chord_regions"]) == 4
    assert result["chord_regions"][0]["root_pc"] == 0  # C major
    assert result["key_bands"]  # local key tracking on by default
    bare = tools.piano_roll_view(str(path), chord_overlays=False, track_local_keys=False)
    assert bare["chord_regions"] == [] and bare["key_bands"] == []


# --- server wiring (only when the optional SDK is installed) ------------------------------------

def test_build_server_registers_all_tools():
    pytest.importorskip("mcp")
    from mts.mcp.server import build_server

    server = build_server()
    assert server is not None


def test_tools_have_docstrings_for_schema_derivation():
    for tool in tools.TOOLS:
        assert tool.__doc__, f"{tool.__name__} needs a docstring (it becomes the tool description)"
