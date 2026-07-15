"""Phase 4.6 slice 1: ruleset schema validation + the conformance evaluator."""

from __future__ import annotations

import json

import pytest

from mts.core.pitch import Pitch
from mts.rules import RulesetValidationError, evaluate, parse_ruleset, validation_errors
from mts.temporal import Event, Sequence


def _seq(events):
    return Sequence.from_events(
        [Event(o, d, Pitch.from_midi(m), voice=v) for o, d, m, v in events]
    )


def _satb_with_fifths():
    """I -> ii with planted bass/tenor parallel fifths at beats 0->2."""
    return _seq([
        (0, 2, 48, "bass"), (2, 2, 50, "bass"),
        (0, 2, 55, "tenor"), (2, 2, 57, "tenor"),
        (0, 2, 64, "alto"), (2, 2, 62, "alto"),
        (0, 2, 72, "soprano"), (2, 2, 69, "soprano"),
    ])


NO_PARALLEL_PERFECTS = {
    "id": "no-parallel-perfects",
    "family": "voice_motion",
    "where": {"motion": "parallel"},
    "forbid": {"interval_class_to": {"in": [0, 7]}},
    "polarity": "hard",
}

LEAPS_RESOLVE_BY_STEP = {
    "id": "leaps-resolve-by-step",
    "family": "melody",
    "where": {"approach_class": "leap"},
    "require": {"departure_class": {"in": ["step", "unison"]}},
    "polarity": "soft",
    "weight": 2.0,
}


def _ruleset(*rules, name="test", version="t.1"):
    return {"name": name, "version": version, "rules": list(rules)}


# --- schema validation -------------------------------------------------------------------


def test_valid_ruleset_parses():
    ruleset = parse_ruleset(_ruleset(NO_PARALLEL_PERFECTS, LEAPS_RESOLVE_BY_STEP))
    assert ruleset.name == "test"
    assert [r.id for r in ruleset.rules] == ["no-parallel-perfects", "leaps-resolve-by-step"]
    assert ruleset.rules[0].check_kind == "forbid"
    assert ruleset.rules[1].weight == 2.0


def test_validation_collects_every_error_not_just_the_first():
    bad = _ruleset(
        {"id": "a", "family": "nope", "forbid": {"x": 1}},
        {"id": "a", "family": "melody", "forbid": {"motion": "parallel"},
         "polarity": "maybe", "bogus_key": True},
    )
    errors = validation_errors(bad)
    text = "\n".join(errors)
    assert "family: must be one of" in text
    assert "duplicate id 'a'" in text
    assert "unknown field for family 'melody'" in text
    assert "polarity: must be 'hard', 'soft' or 'budget'" in text
    assert "unknown keys ['bogus_key']" in text
    assert len(errors) >= 5


def test_enum_typos_are_caught_with_the_allowed_list():
    bad = _ruleset({"id": "r", "family": "voice_motion",
                    "forbid": {"motion": "paralel"}})
    [error] = validation_errors(bad)
    assert "'paralel' is not one of" in error and "parallel" in error


def test_structural_rules_enforced():
    assert "exactly one of 'forbid' or 'require'" in "\n".join(
        validation_errors(_ruleset({"id": "r", "family": "melody"}))
    )
    both = _ruleset({"id": "r", "family": "melody",
                     "forbid": {"pc": 0}, "require": {"pc": 1}})
    assert "exactly one of" in "\n".join(validation_errors(both))
    assert "rules: required, a non-empty list" in "\n".join(
        validation_errors({"name": "x", "version": "1", "rules": []})
    )


def test_operator_and_type_validation():
    errors = "\n".join(validation_errors(_ruleset(
        {"id": "a", "family": "voice_motion", "forbid": {"motion": {"gte": 3}}},
        {"id": "b", "family": "voice_motion", "forbid": {"interval_to": {"in": []}}},
        {"id": "c", "family": "rhythm", "forbid": {"is_syncopated": "yes"}},
        {"id": "d", "family": "melody", "require": {"pc": 0}, "weight": 1.5},
    )))
    assert "field is str, not numeric" in errors
    assert "must be a non-empty list" in errors
    assert "expected bool" in errors
    assert "only soft rules take a weight" in errors  # hard AND budget take none (gap 23)


def test_parse_raises_with_the_full_error_list():
    with pytest.raises(RulesetValidationError) as exc_info:
        parse_ruleset({"name": "", "version": "", "rules": [{}]})
    assert len(exc_info.value.errors) >= 3


# --- evaluation --------------------------------------------------------------------------


def test_parallel_fifths_violation_with_location_and_evidence():
    report = evaluate(_ruleset(NO_PARALLEL_PERFECTS), _satb_with_fifths())
    assert report.hard_rules_hold is False
    assert report.hard_violation_count == 1
    [result] = report.results
    assert result.items_considered >= 1  # the where-filter saw parallel motion
    [violation] = result.violations
    assert violation.location["voices"] == ["bass", "tenor"]
    assert violation.location["from_beat"] == 0.0
    assert violation.evidence["motion"] == "parallel"
    assert violation.evidence["interval_class_to"] == 7


def test_clean_material_holds():
    clean = _seq([
        (0, 2, 48, "bass"), (2, 2, 52, "bass"),
        (0, 2, 64, "soprano"), (2, 2, 62, "soprano"),
    ])
    report = evaluate(_ruleset(NO_PARALLEL_PERFECTS), clean)
    assert report.hard_rules_hold is True
    assert report.results[0].holds is True


def test_soft_rule_conformance_frequency():
    # two leaps: one resolves by step (down), one leaps onward
    line = _seq([
        (0, 1, 60, "m"), (1, 1, 67, "m"), (2, 1, 65, "m"),  # leap, resolved by step
        (3, 1, 72, "m"), (4, 1, 79, "m"),                    # leap, left by leap...
    ])
    report = evaluate(_ruleset(LEAPS_RESOLVE_BY_STEP), line)
    [result] = report.results
    assert result.polarity == "soft"
    assert result.holds is None
    assert result.items_considered == 2
    assert len(result.violations) == 1
    assert result.conformance == pytest.approx(0.5)
    assert report.soft_score == pytest.approx(0.5)
    # RE-3d: no applicable hard rules → None ("never tested"), not a vacuous True
    assert report.hard_rules_hold is None


def test_nht_rules_need_harmony_no_harmony_no_claim():
    rule = {"id": "no-free-dissonance", "family": "melody",
            "forbid": {"nht_type": "free"}, "polarity": "hard"}
    line = _seq([(0, 1, 60, "m"), (1, 1, 62, "m"), (2, 1, 64, "m")])
    without = evaluate(_ruleset(rule), line)
    assert without.results[0].applicable is False
    assert "no harmony, no claim" in without.results[0].reason
    # RE-3d: the one hard rule was not applicable — True would conflate
    # "tested and clean" with "never tested"; the report says None.
    assert without.hard_rules_hold is None
    with_harmony = evaluate(_ruleset(rule), line, harmony=[(0.0, 4.0, (0, 4, 7))])
    assert with_harmony.results[0].applicable is True
    assert with_harmony.results[0].holds is True  # D is a passing tone, not free


def test_voice_motion_rule_on_monophonic_material_is_not_applicable():
    mono = _seq([(0, 1, 60, "m"), (1, 1, 62, "m")])
    report = evaluate(_ruleset(NO_PARALLEL_PERFECTS), mono)
    assert report.results[0].applicable is False
    assert "two voiced parts" in report.results[0].reason


def test_unanalyzable_voice_is_reported_not_silently_skipped():
    events = _seq([
        (0, 1, 60, "m"), (1, 1, 67, "m"), (2, 1, 65, "m"),
        (3, 1, 72, "m"), (4, 1, 79, "m"),
        (0, 2, 40, "pad"), (1, 2, 47, "pad"),  # overlapping: not a line
    ])
    report = evaluate(_ruleset(LEAPS_RESOLVE_BY_STEP), events)
    [result] = report.results
    assert result.applicable is True  # voice "m" still evaluated
    assert result.skipped_voices == ["pad"]
    assert result.items_considered == 2


def test_rhythm_family_rule():
    rule = {"id": "no-syncopation", "family": "rhythm",
            "forbid": {"is_syncopated": True}, "polarity": "hard"}
    charleston = _seq([(0, 1.5, 60, "m"), (1.5, 2.5, 62, "m")])
    report = evaluate(_ruleset(rule), charleston)
    assert report.hard_violation_count == 1
    assert report.results[0].violations[0].evidence["is_syncopated"] is True


def test_malformed_harmony_raises_to_the_caller_not_into_applicability():
    rule = {"id": "no-free-dissonance", "family": "melody",
            "forbid": {"nht_type": "free"}, "polarity": "hard"}
    line = _seq([(0, 1, 60, "m"), (1, 1, 62, "m")])
    with pytest.raises(ValueError, match="no extent"):
        evaluate(_ruleset(rule), line, harmony=[(2.0, 2.0, (0, 4, 7))])


def test_evaluate_rejects_invalid_ruleset_with_full_errors():
    with pytest.raises(RulesetValidationError):
        evaluate({"name": "x", "version": "1", "rules": [{"id": "r"}]},
                 _satb_with_fifths())


def test_report_is_json_ready():
    report = evaluate(
        _ruleset(NO_PARALLEL_PERFECTS, LEAPS_RESOLVE_BY_STEP), _satb_with_fifths()
    )
    payload = json.loads(json.dumps(report.to_dict()))
    assert payload["ruleset_name"] == "test"
    assert payload["results"][0]["violations"][0]["evidence"]["interval_class_to"] == 7


# --- RE-3d: description is validated, never coerced --------------------------------------


def test_null_description_is_a_validation_error_not_the_string_none():
    payload = _ruleset(NO_PARALLEL_PERFECTS)
    payload["description"] = None  # used to round-trip as the string "None"
    assert any("description" in e for e in validation_errors(payload))
    with pytest.raises(RulesetValidationError):
        parse_ruleset(payload)


def test_absent_description_defaults_to_empty_and_string_passes():
    assert parse_ruleset(_ruleset(NO_PARALLEL_PERFECTS)).description == ""
    payload = _ruleset(NO_PARALLEL_PERFECTS)
    payload["description"] = "species counterpoint, first pass"
    assert parse_ruleset(payload).description == "species counterpoint, first pass"
