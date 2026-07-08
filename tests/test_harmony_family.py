"""Tests for the harmony/progression rule family (gap B slice 1).

Oracles are hand-verifiable functional harmony in C major / A minor. The
family builds per-chord items from an explicit chord stream + key; each field
is checked against a known progression.
"""

import pytest

from mts.mcp.tools import _canonical_sequence
from mts.rules import evaluate, load_named_ruleset, ruleset_field_manifest
from mts.rules.harmony_stream import build_harmony_stream

EMPTY = _canonical_sequence([])          # harmony rules read chords, not notes
CMAJ = (0, "major")

# I - IV - V - I in C major
I_IV_V_I = [(0, "maj"), (5, "maj"), (7, "maj"), (0, "maj")]


def _rule(**kw):
    return {"name": "t", "version": "1", "rules": [{"id": "r", "family": "harmony", **kw}]}


# --- the item builder ----------------------------------------------------------

def test_item_fields_on_a_textbook_progression():
    items = [it for it, _loc in build_harmony_stream(I_IV_V_I, 0, "major")[0]]
    romans = [it.roman for it in items]
    roles = [it.role for it in items]
    assert romans == ["I", "IV", "V", "I"]
    assert roles == ["tonic", "predominant", "dominant", "tonic"]
    assert [it.degree for it in items] == [1, 4, 5, 1]
    assert all(it.is_diatonic for it in items)
    # transition fields chain, and are None on the last chord (a line edge)
    assert items[2].next_role == "tonic"
    assert items[-1].next_role is None and items[-1].root_motion is None
    # the V->I is an authentic cadence, attached to its arrival chord
    assert items[3].cadence == "authentic"


def test_root_motion_is_directed_mod12():
    items = [it for it, _ in build_harmony_stream([(0, "maj"), (7, "maj")], 0, "major")[0]]
    assert items[0].root_motion == 7   # C -> G, up a fifth
    items2 = [it for it, _ in build_harmony_stream([(7, "maj"), (0, "maj")], 0, "major")[0]]
    assert items2[0].root_motion == 5  # G -> C, up a fourth (down a fifth)


def test_borrowed_chord_is_not_diatonic():
    # bVII (B-flat major) in C major: outside the diatonic collection.
    items = [it for it, _ in build_harmony_stream([(0, "maj"), (10, "maj")], 0, "major")[0]]
    assert items[0].is_diatonic is True
    assert items[1].is_diatonic is False


# --- rules enforce functional harmony ------------------------------------------

def test_dominant_resolves_to_tonic_holds():
    rs = _rule(where={"role": "dominant"}, require={"next_role": "tonic"}, polarity="hard")
    report = evaluate(rs, EMPTY, chords=I_IV_V_I, key=CMAJ)
    assert report.hard_rules_hold is True
    assert report.results[0].items_considered == 1  # only the V is considered


def test_retrogression_is_caught():
    # V -> IV is a retrogression (dominant falling back to predominant).
    retro = [(0, "maj"), (7, "maj"), (5, "maj"), (0, "maj")]
    rs = _rule(where={"role": "dominant"}, forbid={"next_role": "predominant"}, polarity="hard")
    report = evaluate(rs, EMPTY, chords=retro, key=CMAJ)
    assert report.hard_violation_count == 1


def test_forbid_a_roman_label():
    rs = _rule(forbid={"roman": "IV"}, polarity="hard")
    report = evaluate(rs, EMPTY, chords=I_IV_V_I, key=CMAJ)
    assert report.hard_violation_count == 1  # the single IV


def test_deceptive_cadence_field():
    # V -> vi in C major is a deceptive cadence on the vi.
    deceptive = [(0, "maj"), (7, "maj"), (9, "min")]
    items = [it for it, _ in build_harmony_stream(deceptive, 0, "major")[0]]
    assert items[-1].cadence == "deceptive"
    rs = _rule(where={"cadence": "deceptive"}, forbid={"cadence": "deceptive"}, polarity="hard")
    # where cadence=deceptive is considered; forbidding it fires on that chord
    assert evaluate(rs, EMPTY, chords=deceptive, key=CMAJ).hard_violation_count == 1


def test_soft_diatonic_tendency_scores():
    # a progression with one borrowed chord scores below 1.0 on "stay diatonic".
    rs = _rule(require={"is_diatonic": True}, polarity="soft", weight=1.0)
    mostly = [(0, "maj"), (5, "maj"), (10, "maj"), (0, "maj")]  # bVII is borrowed
    report = evaluate(rs, EMPTY, chords=mostly, key=CMAJ)
    assert 0.0 < report.soft_score < 1.0


# --- applicability (no chords / key, unsupported mode) -------------------------

def test_not_applicable_without_chords_or_key():
    rs = _rule(forbid={"roman": "IV"}, polarity="hard")
    r_no_chords = evaluate(rs, EMPTY, key=CMAJ).results[0]
    assert r_no_chords.applicable is False and "chords" in r_no_chords.reason
    r_no_key = evaluate(rs, EMPTY, chords=I_IV_V_I).results[0]
    assert r_no_key.applicable is False and "key" in r_no_key.reason


def test_modal_key_is_not_applicable_not_guessed():
    rs = _rule(forbid={"roman": "IV"}, polarity="hard")
    r = evaluate(rs, EMPTY, chords=I_IV_V_I, key=(2, "dorian")).results[0]
    assert r.applicable is False
    assert "major/minor only" in r.reason


# --- manifest + library + MCP -------------------------------------------------

def test_manifest_includes_harmony_family():
    m = ruleset_field_manifest()
    assert m["manifest_version"] == "ruleset-fields.2"
    assert "harmony" in m["families"]
    fields = m["families"]["harmony"]["fields"]
    assert fields["role"]["values"] == ["tonic", "predominant", "dominant"]
    assert fields["cadence"]["values"] == ["authentic", "plagal", "deceptive", "half", "none"]


def test_edm_minor_loop_ruleset_ships_and_evaluates():
    rs = load_named_ruleset("edm-minor-loop")
    assert all(r.polarity == "soft" for r in rs.rules)  # a style is tendencies
    # i - VI - III - VII in A minor (a classic loop): all diatonic, smooth.
    loop = [(9, "min"), (5, "maj"), (0, "maj"), (7, "maj")]
    report = evaluate(rs, EMPTY, chords=loop, key=(9, "minor"))
    assert report.soft_score == 1.0  # fully idiomatic to the sketch


def test_mcp_evaluate_ruleset_with_chords_matches_engine():
    from mts.mcp import tools

    rs = _rule(where={"role": "dominant"}, require={"next_role": "tonic"}, polarity="hard")
    engine = evaluate(rs, EMPTY, chords=I_IV_V_I, key=CMAJ).to_dict()
    tool = tools.evaluate_ruleset(
        rs, [], chords=[["C", "maj"], ["F", "maj"], ["G", "maj"], ["C", "maj"]],
        key=["C", "major"],
    )
    assert tool == engine
