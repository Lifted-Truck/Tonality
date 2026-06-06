"""Tests for the transpositional × registral identity lattice."""

import pytest

from mts.analysis.specs import from_scope, to_scope
from mts.core.spec_level import (
    INTERVAL_SHAPE,
    NAMED_CHORD,
    VOICING,
    VOICING_TEMPLATE,
    Registral,
    SpecLevel,
    Transpositional,
)


def test_four_corners_are_distinct():
    corners = {VOICING, NAMED_CHORD, INTERVAL_SHAPE, VOICING_TEMPLATE}
    assert len(corners) == 4


def test_classify_matches_named_corners():
    assert SpecLevel.classify(rooted=True, registered=True) == VOICING
    assert SpecLevel.classify(rooted=True, registered=False) == NAMED_CHORD
    assert SpecLevel.classify(rooted=False, registered=False) == INTERVAL_SHAPE
    assert SpecLevel.classify(rooted=False, registered=True) == VOICING_TEMPLATE


def test_axis_predicates():
    assert VOICING.is_rooted and VOICING.is_registered
    assert NAMED_CHORD.is_rooted and not NAMED_CHORD.is_registered
    assert not INTERVAL_SHAPE.is_rooted and not INTERVAL_SHAPE.is_registered
    assert not VOICING_TEMPLATE.is_rooted and VOICING_TEMPLATE.is_registered


def test_class_attribute_access():
    assert SpecLevel.VOICING == VOICING
    assert SpecLevel.VOICING_TEMPLATE == VOICING_TEMPLATE


def test_frozen_and_hashable():
    # Usable as a dict key; equal-by-value instances collide.
    mapping = {VOICING: "v"}
    assert mapping[SpecLevel(Transpositional.ROOTED, Registral.REGISTERED)] == "v"


def test_labels():
    assert str(VOICING_TEMPLATE) == "voicing template"
    assert INTERVAL_SHAPE.label == "interval shape"


def test_scope_bridge_round_trips_for_the_three_legacy_corners():
    for scope in ("abstract", "note", "absolute"):
        assert to_scope(from_scope(scope)) == scope


def test_scope_maps_along_the_diagonal():
    assert from_scope("abstract") == INTERVAL_SHAPE
    assert from_scope("note") == NAMED_CHORD
    assert from_scope("absolute") == VOICING


def test_voicing_template_has_no_legacy_scope():
    # scope walks a diagonal and can never reach the registered+rootless corner.
    with pytest.raises(ValueError):
        to_scope(VOICING_TEMPLATE)
