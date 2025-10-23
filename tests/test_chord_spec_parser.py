from mts.analysis.specs import parse_chord_spec


def test_parse_intervals_abstract():
    result = parse_chord_spec("[0,3,7]")
    assert result.spec.scope == "abstract"
    assert result.spec.intervals == (0, 3, 7)
    assert result.root_pc is None
    assert result.spec.quality_name == "min"
    assert "min" in result.spec.quality_matches
    assert result.spec.voicing == (0, 3, 7)


def test_parse_interval_names():
    result = parse_chord_spec("[P1,m3,P5]")
    assert result.spec.scope == "abstract"
    assert result.spec.intervals == (0, 3, 7)
    assert result.spec.quality_name == "min"
    assert result.spec.voicing == (0, 3, 7)


def test_parse_scale_degree_tokens():
    result = parse_chord_spec("(1,b3,5)")
    assert result.spec.intervals == (0, 3, 7)
    assert result.spec.quality_name == "min"
    assert result.spec.voicing == (0, 3, 7)


def test_parse_note_tokens():
    result = parse_chord_spec("[C,E,G]")
    assert result.spec.scope == "note"
    assert result.spec.intervals == (0, 4, 7)
    assert result.root_pc == 0
    assert result.spec.tokens == ("C", "E", "G")
    assert result.spec.quality_name == "maj"
    assert result.spec.voicing == ()


def test_parse_absolute_tokens():
    result = parse_chord_spec("[C3,E3,G3]")
    assert result.spec.scope == "absolute"
    assert result.spec.absolute_midi == (48, 52, 55)
    assert result.root_pitch and result.root_pitch.midi == 48
    assert result.spec.quality_name == "maj"
    assert result.spec.voicing == (0, 4, 7)


def test_parse_midi_sequence():
    result = parse_chord_spec("{60,63,67}")
    assert result.spec.scope == "absolute"
    assert result.spec.absolute_midi == (60, 63, 67)
    assert result.root_pitch and result.root_pitch.midi == 60
    assert result.spec.quality_name == "min"
    assert result.spec.voicing == (0, 3, 7)


def test_parse_root_with_intervals():
    result = parse_chord_spec("C3[0,3,7]")
    assert result.spec.scope == "absolute"
    assert result.spec.absolute_midi == (48, 51, 55)
    assert result.root_pitch and result.root_pitch.midi == 48
    assert result.spec.quality_name == "min"
    assert result.spec.voicing == (0, 3, 7)


def test_parse_intervals_with_extended_voicing():
    result = parse_chord_spec("[0,3,15,11]")
    assert result.spec.scope == "abstract"
    assert result.spec.intervals == (0, 3, 11)
    assert result.spec.voicing == (0, 3, 15, 11)
    assert result.spec.quality_name is None


def test_parse_named_quality():
    result = parse_chord_spec("min")
    assert result.spec.quality_name == "min"
    assert result.spec.scope == "abstract"
    assert result.spec.intervals == (0, 3, 7)
    assert result.spec.voicing == (0, 3, 7)


def test_parse_root_named_quality():
    result = parse_chord_spec("C:min")
    assert result.spec.scope == "note"
    assert result.root_pc == 0
    assert result.spec.tokens[0] == "C"
    assert result.spec.quality_name == "min"
    assert result.spec.voicing == (0, 3, 7)


def test_parse_absolute_named_quality():
    result = parse_chord_spec("C3:min")
    assert result.spec.scope == "absolute"
    assert result.spec.absolute_midi[0] == 48
    assert result.spec.quality_name == "min"
    assert result.spec.voicing == (0, 3, 7)


def test_parse_root_with_degrees():
    result = parse_chord_spec("C3(1,b3,5)")
    assert result.spec.scope == "absolute"
    assert result.spec.absolute_midi == (48, 51, 55)
    assert result.spec.voicing == (0, 3, 7)


def test_quality_subsets():
    result = parse_chord_spec("[0,4]")
    subset_names = {variant.name for variant in result.spec.quality_subsets}
    assert "maj" in subset_names
    variant = next(v for v in result.spec.quality_subsets if v.name == "maj")
    assert variant.missing == (7,)
    assert variant.extra == ()


def test_quality_supersets():
    result = parse_chord_spec("[0,3,7,10]")
    superset_names = {variant.name for variant in result.spec.quality_supersets}
    assert "min" in superset_names
    variant = next(v for v in result.spec.quality_supersets if v.name == "min")
    assert variant.extra == (10,)
    assert variant.missing == ()


def test_quality_cousins():
    result = parse_chord_spec("[0,4,5]")
    cousin_names = {variant.name for variant in result.spec.quality_cousins}
    assert "maj" in cousin_names
    variant = next(v for v in result.spec.quality_cousins if v.name == "maj")
    assert variant.missing == (7,)
    assert variant.extra == (5,)
