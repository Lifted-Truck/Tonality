"""Tests for the edge formatter layer (spelling/labels driven by DisplayContext)."""

from mts.analysis import (
    ChordAnalysisRequest,
    ScaleAnalysisRequest,
    analyze_chord,
    analyze_scale,
    analyze_voicing,
    interpret_chord,
)
from mts.context import DisplayContext
from mts.context.result_format import (
    format_chord_analysis,
    format_scale_analysis,
    name_interpretations,
    spell_voicing,
)
from mts.core.chord import Chord
from mts.core.realization import Realization
from mts.io.loaders import load_chord_qualities, load_scales


def _ctx(spelling="auto", **kw):
    ctx = DisplayContext()
    ctx.set("spelling", spelling, layer="cli")
    for key, value in kw.items():
        ctx.set(key, value, layer="cli")
    return ctx


def _c7():
    return analyze_chord(ChordAnalysisRequest(chord=Chord.from_quality(0, load_chord_qualities()["7"])))


def test_spelling_follows_context():
    res = _c7()  # C7 -> pcs {0,4,7,10}
    assert format_chord_analysis(res, _ctx("flats")).note_names == ["C", "E", "G", "Bb"]
    assert format_chord_analysis(res, _ctx("sharps")).note_names == ["C", "E", "G", "A#"]


def test_root_name_and_interval_labels():
    disp = format_chord_analysis(_c7(), _ctx("flats"))
    assert disp.root_name == "C"
    assert disp.interval_labels == ["P1", "M3", "P5", "m7"]  # classical default


def test_interval_label_style_is_a_context_setting():
    disp = format_chord_analysis(_c7(), _ctx("flats", interval_label_style="numeric"))
    assert disp.interval_labels == ["0", "4", "7", "10"]


def test_enharmonics_offer_alternates():
    disp = format_chord_analysis(_c7(), _ctx("flats"))
    bb = disp.enharmonics[3]  # pc 10
    assert bb.pc == 10
    assert bb.preferred == "Bb"
    assert "A#" in bb.alternates


def test_scale_notes_are_spelled():
    sres = analyze_scale(ScaleAnalysisRequest(scale=load_scales()["Ionian"], tonic_pc=0))
    assert format_scale_analysis(sres, _ctx("flats")).note_names == [
        "C", "D", "E", "F", "G", "A", "B",
    ]


def test_interpretation_naming():
    names = name_interpretations(interpret_chord([0, 3, 6, 9]).interpretations, _ctx("flats"))
    assert names == ["C dim7", "Eb dim7", "Gb dim7", "A dim7"]


def test_voicing_spelled_with_octaves():
    va = analyze_voicing(Realization.from_midi([48, 52, 55], root_pc=0))
    assert spell_voicing(va, _ctx("flats")) == ["C3", "E3", "G3"]


def test_display_view_to_dict():
    d = format_chord_analysis(_c7(), _ctx("flats")).to_dict()
    assert d["root_name"] == "C"
    assert d["note_names"] == ["C", "E", "G", "Bb"]
    assert isinstance(d["enharmonics"], list)
