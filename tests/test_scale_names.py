"""Scale naming (Audiology brief-20 v1): `interpret_scale` / MCP `scale_names`.

The scale sibling of `interpret_chord` — name a pc-set as scales, plural + honest
(a modal-ambiguous set names at several tonics). Set-class identity is the
boundary; forte_number is a recorded deferral (None).
"""

import pytest

from mts.analysis import interpret_scale

DIATONIC = [0, 2, 4, 5, 7, 9, 11]  # C-major collection


def test_diatonic_names_as_all_seven_modes():
    r = interpret_scale(DIATONIC)
    by_root = {n.root_pc: n.name for n in r.names}
    assert by_root == {0: "Ionian", 2: "Dorian", 4: "Phrygian", 5: "Lydian",
                       7: "Mixolydian", 9: "Aeolian", 11: "Locrian"}
    # aliases ride along from the catalog
    ionian = next(n for n in r.names if n.name == "Ionian")
    assert "Major" in ionian.aliases


def test_set_class_identity_is_the_boundary():
    r = interpret_scale(DIATONIC)
    assert r.prime_form == [0, 1, 3, 5, 6, 8, 10]  # diatonic set-class
    assert r.cardinality == 7 and r.is_scale is True
    assert r.forte_number is None            # deferred — prime form is the id
    assert len(r.interval_vector) == 6


def test_transposition_covariant():
    # D-major collection: same modes, all roots shifted +2.
    d_major = [(p + 2) % 12 for p in DIATONIC]
    r = interpret_scale(d_major)
    assert {n.root_pc: n.name for n in r.names}[2] == "Ionian"  # D is the tonic of D Ionian
    assert r.prime_form == interpret_scale(DIATONIC).prime_form  # set-class invariant


def test_symmetric_scale_repeats_at_period():
    wt = interpret_scale([0, 2, 4, 6, 8, 10])  # whole-tone
    assert wt.is_scale is True and wt.rotational_period == 2
    assert all(n.name == "Whole Tone" for n in wt.names)


def test_non_scale_set_is_honest():
    r = interpret_scale([0, 1])  # a dyad — no catalog scale
    assert r.is_scale is False and r.names == []
    assert r.prime_form == [0, 1]  # set-class still reported


def test_determinism_and_round_trip():
    from mts.analysis import ScaleNames
    r = interpret_scale(DIATONIC)
    assert r.to_dict() == interpret_scale(DIATONIC).to_dict()
    assert ScaleNames(**{**r.__dict__, "names": r.names})  # constructs

def test_empty_raises():
    with pytest.raises(ValueError, match="at least one pitch class"):
        interpret_scale([])


# --- MCP parity ---------------------------------------------------------------

def test_mcp_scale_names_matches_engine_pcs():
    from mts.mcp import tools
    assert tools.scale_names(pcs=DIATONIC) == interpret_scale(DIATONIC).to_dict()


def test_mcp_scale_names_accepts_prime_form_and_note_names():
    from mts.mcp import tools
    # note-name pcs resolve via _pc
    assert tools.scale_names(pcs=["C", "D", "E", "F", "G", "A", "B"]) == \
        interpret_scale(DIATONIC).to_dict()
    # prime_form path
    assert tools.scale_names(prime_form=[0, 1, 3, 5, 6, 8, 10])["is_scale"] is True


def test_mcp_scale_names_needs_an_argument():
    from mts.mcp import tools
    with pytest.raises(ValueError, match="pcs.*or.*prime_form|prime_form"):
        tools.scale_names()
