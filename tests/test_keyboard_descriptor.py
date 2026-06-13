"""Phase 5 slice 1: the keyboard descriptor (projections as data)."""

from __future__ import annotations

import json

import pytest

from mts.io.loaders import load_scales
from mts.representation import keyboard_descriptor


def _dorian():
    return load_scales()["Dorian"]


# --- topology and identity ---------------------------------------------------------------


def test_keys_carry_identity_and_topology():
    result = keyboard_descriptor(60, 72)
    assert len(result.keys) == 13  # inclusive span
    middle_c = result.keys[0]
    assert (middle_c.midi, middle_c.pc, middle_c.octave, middle_c.is_black) == (60, 0, 4, False)
    c_sharp = result.keys[1]
    assert (c_sharp.pc, c_sharp.is_black) == (1, True)
    blacks = [k.pc for k in result.keys if k.is_black]
    assert set(blacks) == {1, 3, 6, 8, 10}


def test_no_context_means_no_membership_claims():
    result = keyboard_descriptor(60, 64)
    assert result.spec_level == "identity_only"
    assert all(
        k.in_scale is None and k.degree_index is None and k.is_tonic is None
        for k in result.keys
    )


# --- scale membership (register-less) -----------------------------------------------------


def test_membership_coloring_in_d_dorian():
    result = keyboard_descriptor(60, 72, tonic_pc=2, scale=_dorian())
    by_midi = {k.midi: k for k in result.keys}
    assert by_midi[62].in_scale and by_midi[62].is_tonic  # D
    assert by_midi[62].degree_index == 0
    assert by_midi[65].in_scale and by_midi[65].degree_index == 2  # F: dorian b3
    assert by_midi[66].in_scale is False  # F# is out of D dorian
    assert by_midi[71].in_scale and by_midi[71].degree_index == 5  # B: dorian 6
    assert by_midi[74].is_tonic if 74 in by_midi else True
    assert result.scale_name == "Dorian"
    assert result.tonic_pc == 2


def test_membership_repeats_across_octaves():
    result = keyboard_descriptor(36, 96, tonic_pc=2, scale=_dorian())
    d_keys = [k for k in result.keys if k.pc == 2]
    assert len(d_keys) >= 5
    assert all(k.is_tonic and k.degree_index == 0 for k in d_keys)


# --- activation and the spec-level declaration --------------------------------------------


def test_exact_activation_lights_exactly_those_keys():
    result = keyboard_descriptor(48, 84, active_midi=[60, 64, 67])
    assert result.spec_level == "registered"
    lit = [k.midi for k in result.keys if k.active == "exact"]
    assert lit == [60, 64, 67]
    assert all(k.active is None for k in result.keys if k.midi not in lit)


def test_pc_activation_lights_every_octave_by_declaration():
    result = keyboard_descriptor(48, 84, active_pcs=[0])
    assert result.spec_level == "pc_projection"
    lit = [k.midi for k in result.keys if k.active == "pc"]
    assert lit == [48, 60, 72, 84]  # every C in range — the declared projection


def test_both_activation_forms_is_an_error():
    with pytest.raises(ValueError, match="not both"):
        keyboard_descriptor(48, 84, active_midi=[60], active_pcs=[0])


def test_context_and_activation_compose():
    result = keyboard_descriptor(
        60, 72, tonic_pc=2, scale=_dorian(), active_midi=[62, 65, 69]
    )
    d = next(k for k in result.keys if k.midi == 62)
    assert (d.active, d.is_tonic, d.in_scale) == ("exact", True, True)


# --- validation ----------------------------------------------------------------------------


def test_range_and_context_validation():
    with pytest.raises(ValueError, match="0 <= low <= high <= 127"):
        keyboard_descriptor(60, 48)
    with pytest.raises(ValueError, match="supply both or neither"):
        keyboard_descriptor(60, 72, tonic_pc=2)
    with pytest.raises(ValueError, match="supply both or neither"):
        keyboard_descriptor(60, 72, scale=_dorian())
    with pytest.raises(ValueError, match="out of range"):
        keyboard_descriptor(60, 72, active_midi=[200])


def test_to_dict_is_json_ready():
    result = keyboard_descriptor(60, 64, tonic_pc=0, scale=load_scales()["Ionian"])
    payload = json.loads(json.dumps(result.to_dict()))
    assert payload["spec_level"] == "identity_only"
    assert payload["keys"][0]["in_scale"] is True
    assert payload["scale_degrees"] == [0, 2, 4, 5, 7, 9, 11]
