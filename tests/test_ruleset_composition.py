"""Phase 4.6 slice 2: ruleset composition (combine/specialize) + comparison."""

from __future__ import annotations

import json

import pytest

from mts.rules import (
    RulesetConflictError,
    combine,
    compare,
    evaluate,
    parse_ruleset,
    ruleset_to_payload,
    specialize,
)
from mts.core.pitch import Pitch
from mts.temporal import Event, Sequence


NO_PARALLEL_PERFECTS = {
    "id": "no-parallel-perfects", "family": "voice_motion",
    "where": {"motion": "parallel"},
    "forbid": {"interval_class_to": {"in": [0, 7]}}, "polarity": "hard",
}
PREFER_STEPS = {
    "id": "prefer-steps", "family": "melody",
    "require": {"departure_class": {"in": ["step", "unison"]}},
    "polarity": "soft", "weight": 2.0,
}
NO_SYNCOPATION = {
    "id": "no-syncopation", "family": "rhythm",
    "forbid": {"is_syncopated": True}, "polarity": "hard",
}


def _ruleset(*rules, name="rs", version="1"):
    return {"name": name, "version": version, "rules": list(rules)}


# --- serializer round-trip (the composition substrate) -----------------------------------


def test_ruleset_payload_round_trips():
    doc = _ruleset(NO_PARALLEL_PERFECTS, PREFER_STEPS, NO_SYNCOPATION)
    parsed = parse_ruleset(doc)
    reserialized = ruleset_to_payload(parsed)
    assert parse_ruleset(reserialized) == parsed  # structural round-trip
    # soft rule keeps its weight; the forbid/where survive
    rule = next(r for r in reserialized["rules"] if r["id"] == "prefer-steps")
    assert rule["weight"] == 2.0 and rule["polarity"] == "soft"


# --- combine -----------------------------------------------------------------------------


def test_combine_unions_distinct_rules():
    a = _ruleset(NO_PARALLEL_PERFECTS)
    b = _ruleset(PREFER_STEPS, NO_SYNCOPATION)
    combined = combine([a, b], name="counterpoint", version="1")
    assert {r.id for r in combined.rules} == {
        "no-parallel-perfects", "prefer-steps", "no-syncopation"
    }
    assert combined.name == "counterpoint"


def test_combine_dedups_identical_same_id_rules():
    # condition order differs but the rule is structurally identical
    reordered = dict(NO_PARALLEL_PERFECTS)
    combined = combine([_ruleset(NO_PARALLEL_PERFECTS), _ruleset(reordered)],
                       name="x", version="1")
    assert len(combined.rules) == 1


def test_combine_conflicting_same_id_raises():
    variant = dict(NO_PARALLEL_PERFECTS, forbid={"interval_class_to": {"in": [7]}})
    with pytest.raises(RulesetConflictError) as exc:
        combine([_ruleset(NO_PARALLEL_PERFECTS), _ruleset(variant)],
                name="x", version="1")
    assert exc.value.conflicts == ["no-parallel-perfects"]


# --- specialize --------------------------------------------------------------------------


def test_specialize_overrides_and_adds():
    base = _ruleset(NO_PARALLEL_PERFECTS, PREFER_STEPS)
    # overlay: replace prefer-steps (stricter), add no-syncopation
    stricter = dict(PREFER_STEPS, weight=5.0)
    overlay = _ruleset(stricter, NO_SYNCOPATION)
    result = specialize(base, overlay, name="strict", version="1")
    assert result.overridden == ["prefer-steps"]
    assert result.added == ["no-syncopation"]
    rules = {r["id"]: r for r in result.ruleset_payload["rules"]}
    assert rules["prefer-steps"]["weight"] == 5.0  # the override took
    # base order preserved, additions appended
    assert [r["id"] for r in result.ruleset_payload["rules"]] == [
        "no-parallel-perfects", "prefer-steps", "no-syncopation"
    ]


def test_specialize_identical_overlay_rule_is_not_an_override():
    base = _ruleset(NO_PARALLEL_PERFECTS)
    result = specialize(base, _ruleset(NO_PARALLEL_PERFECTS), name="x", version="1")
    assert result.overridden == [] and result.added == []


# --- compare -----------------------------------------------------------------------------


def test_compare_classifies_shared_conflicting_and_unique():
    a = _ruleset(NO_PARALLEL_PERFECTS, PREFER_STEPS)
    variant_prefer = dict(PREFER_STEPS, weight=9.0)
    b = _ruleset(NO_PARALLEL_PERFECTS, variant_prefer, NO_SYNCOPATION)
    result = compare(a, b)
    assert result.shared_ids == ["no-parallel-perfects"]
    assert result.conflicting_ids == ["prefer-steps"]  # same id, different weight
    assert result.only_in_a == []
    assert result.only_in_b == ["no-syncopation"]


def test_compare_detects_direct_contradiction():
    forbids = {"id": "no-parallel", "family": "voice_motion",
               "forbid": {"motion": "parallel"}, "polarity": "hard"}
    requires = {"id": "must-parallel", "family": "voice_motion",
                "require": {"motion": "parallel"}, "polarity": "hard"}
    result = compare(_ruleset(forbids), _ruleset(requires))
    assert len(result.contradictions) == 1
    c = result.contradictions[0]
    assert (c.a_id, c.b_id, c.family) == ("no-parallel", "must-parallel", "voice_motion")
    assert "forbids what" in c.detail


def test_compare_no_false_contradiction_on_different_checks():
    forbids_fifths = {"id": "a", "family": "voice_motion",
                      "forbid": {"interval_class_to": {"in": [7]}}, "polarity": "hard"}
    requires_steps = {"id": "b", "family": "melody",
                      "require": {"departure_class": "step"}, "polarity": "hard"}
    assert compare(_ruleset(forbids_fifths), _ruleset(requires_steps)).contradictions == []


# --- composition results stay evaluable --------------------------------------------------


def test_combined_ruleset_evaluates():
    combined = combine([_ruleset(NO_PARALLEL_PERFECTS), _ruleset(NO_SYNCOPATION)],
                       name="cp", version="1")
    seq = Sequence.from_events([
        Event(0, 2, Pitch.from_midi(48), voice="bass"),
        Event(2, 2, Pitch.from_midi(50), voice="bass"),
        Event(0, 2, Pitch.from_midi(55), voice="tenor"),
        Event(2, 2, Pitch.from_midi(57), voice="tenor"),
    ])
    report = evaluate(combined, seq)
    # the combined ruleset still runs and finds the planted parallel fifths
    assert report.hard_violation_count == 1


def test_results_are_json_ready():
    payload = json.loads(json.dumps(
        specialize(_ruleset(NO_PARALLEL_PERFECTS), _ruleset(NO_SYNCOPATION),
                   name="x", version="1").to_dict()
    ))
    assert payload["added"] == ["no-syncopation"]
    cmp_payload = json.loads(json.dumps(
        compare(_ruleset(NO_PARALLEL_PERFECTS), _ruleset(PREFER_STEPS)).to_dict()
    ))
    assert cmp_payload["only_in_a"] == ["no-parallel-perfects"]
