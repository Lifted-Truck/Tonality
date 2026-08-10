"""gap 26 slice 1 — remap_by_degree (interscalar transposition) + retonicize.

Pins the primitive's contracts: degree-preservation (never proximity), the
equal-cardinality precondition, tonic anchoring, chromatic attachment with
rhetoric preserved, the tied-attachment flag, markedness absorption reported,
and retonicize as a zero-edit renaming.
"""

from __future__ import annotations

import pytest

from mts.generate import InterscalarMap, remap_by_degree, retonicize
from mts.mcp.tools import _canonical_sequence

MAJOR, MINOR = "Ionian", "Natural Minor"


def _seq(events):
    return _canonical_sequence(events)


# --- the core: degrees, not proximity -------------------------------------------

def test_major_to_minor_moves_exactly_the_three_degrees():
    scale_run = [[i, 1, m, 90, "m"] for i, m in
                 enumerate([60, 62, 64, 65, 67, 69, 71, 72])]
    r = remap_by_degree(_seq(scale_run), MAJOR, 0, MINOR, 0)
    got = [e[2] for e in r.events]
    assert got == [60, 62, 63, 65, 67, 68, 70, 72]      # E->Eb, A->Ab, B->Bb
    assert r.notes_chromatic == 0
    assert all(e.alteration == 0 for e in r.edits)


def test_remap_is_by_degree_not_proximity():
    """The design line in one assertion: degree 3 goes to degree 3 even when a
    nearer target pc exists. Lydian's #4 (F#) must map to Locrian's b4... use a
    clean case: major degree 7 (B, pc 11) -> phrygian degree 7 (Bb? no —
    Phrygian degrees [0,1,3,5,7,8,10]: index 6 = 10). B(71) sits 1 from C(72)
    but must go to Bb(70) — the degree image, not the near neighbour."""
    r = remap_by_degree(_seq([[0, 1, 71]]), MAJOR, 0, "Phrygian", 0)
    assert r.events[0][2] == 70


def test_bijective_on_in_scale_material_round_trip():
    scale_run = [[i, 1, m] for i, m in enumerate([60, 62, 64, 65, 67, 69, 71])]
    there = remap_by_degree(_seq(scale_run), MAJOR, 0, MINOR, 0)
    back = remap_by_degree(_seq(there.events), MINOR, 0, MAJOR, 0)
    assert [e[2] for e in back.events] == [e[2] for e in scale_run]


def test_transposition_of_root_composes():
    # C major -> A natural minor: degree map + root move
    r = remap_by_degree(_seq([[0, 1, 60], [1, 1, 64]]), MAJOR, 0, MINOR, 9)
    assert r.events[0][2] % 12 == 9                     # tonic -> tonic (A)
    assert r.events[1][2] % 12 == 0                     # degree 2 (E) -> C


# --- preconditions: error, not guess --------------------------------------------

def test_unequal_cardinality_errors():
    with pytest.raises(ValueError, match="equal cardinality"):
        remap_by_degree(_seq([[0, 1, 60]]), MAJOR, 0, "Major Pentatonic", 0)


def test_tonic_anchoring_requires_degree_zero():
    with pytest.raises(ValueError, match="tonic-anchored"):
        remap_by_degree(_seq([[0, 1, 60]]), [2, 4, 7], 0, [1, 3, 5], 0)


def test_empty_sequence_and_unknown_scale_error():
    with pytest.raises(ValueError, match="non-empty"):
        remap_by_degree(_seq([]), MAJOR, 0, MINOR, 0)
    with pytest.raises(ValueError, match="Unknown scale"):
        remap_by_degree(_seq([[0, 1, 60]]), "Klingon", 0, MINOR, 0)


# --- chromatic tones: rhetoric preserved, decisions inspectable -----------------

def test_chromatic_alteration_is_carried_not_snapped():
    # F#4 in C major: attaches to F (degree 3) as +1. Target C minor:
    # degree 3 is F, so image F#+0... F# stays F#. In a target where degree 3
    # moves, the alteration rides along: C major -> C phrygian, degree 3 = F,
    # F# -> F#. Use a moving degree: A major shape? Keep the assertion tight:
    r = remap_by_degree(_seq([[0, 1, 66]]), MAJOR, 0, MINOR, 0)
    e = r.edits[0]
    assert (e.degree, e.alteration) == (3, 1)           # F#4 = raised degree 4
    assert r.events[0][2] == 66                          # F is static: F# survives
    assert r.notes_chromatic == 1


def test_tied_attachment_is_flagged_and_attaches_below():
    # C#: equidistant between C (#1) and D (b2) in C major — attaches below.
    r = remap_by_degree(_seq([[0, 1, 61]]), MAJOR, 0, MINOR, 0)
    e = r.edits[0]
    assert e.tied_attachment and e.degree == 0 and e.alteration == 1
    assert r.tied_attachments == 1 and e.attachment_note


def test_markedness_absorption_is_reported():
    """Eb in C major (chromatic, attaches as #2) maps to Eb in C minor — which
    is DIATONIC there. Chromatic identity lost; must be reported, not silent."""
    r = remap_by_degree(_seq([[0, 1, 63]]), MAJOR, 0, MINOR, 0)
    assert len(r.absorbed_alterations) == 1
    a = r.absorbed_alterations[0]
    assert a.from_midi == 63 and a.to_midi == 63


def test_zero_pitch_change_chromatic_decisions_are_still_recorded():
    # C# maps to C# (pitch unchanged) but the degree attachment was a real
    # decision — it must appear in edits so the plan is inspectable.
    r = remap_by_degree(_seq([[0, 1, 61]]), MAJOR, 0, MINOR, 0)
    assert len(r.edits) == 1 and r.edits[0].delta == 0


# --- preservation contract ------------------------------------------------------

def test_everything_but_pitch_is_preserved():
    events = [[0.0, 1.5, 64, 99, "v1"], [2.0, 0.25, 71, 40, "v2"]]
    r = remap_by_degree(_seq(events), MAJOR, 0, MINOR, 0)
    assert r.notes_total == 2
    for src, out in zip(events, r.events):
        assert out[0] == src[0] and out[1] == src[1]
        assert out[3] == src[3] and out[4] == src[4]


def test_register_preserved_moves_bounded():
    events = [[i, 1, 36 + i * 5] for i in range(15)]
    r = remap_by_degree(_seq(events), MAJOR, 0, "Lydian", 3)
    for src, out in zip(events, r.events):
        assert abs(out[2] - src[2]) <= 6


def test_degree_table_is_inspectable():
    imap = InterscalarMap(
        source_name=None, source_degrees=(0, 4, 7), source_root=0,
        target_name=None, target_degrees=(0, 3, 7), target_root=0,
    )
    table = imap.degree_table()
    assert table[1] == {"degree": 1, "source_pc": 4, "target_pc": 3}


def test_deterministic():
    events = [[i * 0.5, 0.5, 48 + (i * 5) % 30, 70, "m"] for i in range(24)]
    a = remap_by_degree(_seq(events), MAJOR, 2, "Dorian", 7).to_dict()
    b = remap_by_degree(_seq(events), MAJOR, 2, "Dorian", 7).to_dict()
    assert a == b


# --- retonicize: the folk operation, zero edits ---------------------------------

def test_retonicize_c_ionian_at_a_is_aeolian():
    r = retonicize(MAJOR, 0, 9)
    assert r.new_root == 9 and "Aeolian" in r.new_names
    assert r.notes_changed == 0
    assert r.collection_pcs == [0, 2, 4, 5, 7, 9, 11]


def test_retonicize_rejects_a_tonic_outside_the_collection():
    with pytest.raises(ValueError, match="not in the collection"):
        retonicize(MAJOR, 0, 1)


def test_retonicize_unmatched_rotation_returns_empty_names_not_error():
    r = retonicize([0, 1, 2, 3], 0, 1)                  # chromatic cluster
    assert r.new_names == [] and r.new_degrees == [0, 1, 2, 11]


def test_mcp_parity():
    from mts.mcp import tools

    out = tools.remap_by_degree(
        events=[[0, 1, 64, 90, "m"]], source_scale=MAJOR, source_root=0,
        target_scale=MINOR, target_root=0,
    )
    assert out["events"][0][2] == 63
    assert "degree_table" in out["map"] and "absorbed_alterations" in out
    ret = tools.retonicize(scale=MAJOR, root_pc=0, new_tonic_pc=9)
    assert ret["notes_changed"] == 0 and "Aeolian" in ret["new_names"]
