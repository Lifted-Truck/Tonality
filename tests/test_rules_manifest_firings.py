"""Tests for the two wont micro-deliverables (gap 20 sub-items):
the ruleset field manifest and evaluate()'s opt-in firing locations.
"""

import json

import pytest

from mts.rules import (
    FAMILIES,
    FIELD_MANIFEST_VERSION,
    evaluate,
    ruleset_field_manifest,
)
from mts.mcp.tools import _canonical_sequence
from mts.rules.schema import HARMONY_DEPENDENT_FIELDS


# --- field manifest -----------------------------------------------------------

def test_manifest_is_current_with_FAMILIES():
    # The manifest must describe exactly the validator's vocabulary — if this
    # fails, FAMILIES changed and FIELD_MANIFEST_VERSION should be bumped.
    m = ruleset_field_manifest()
    assert m["manifest_version"] == FIELD_MANIFEST_VERSION
    assert set(m["families"]) == set(FAMILIES)
    for family, spec in FAMILIES.items():
        fields = m["families"][family]["fields"]
        assert set(fields) == set(spec)
        for name, fspec in spec.items():
            entry = fields[name]
            assert entry["kind"] == fspec.kind
            assert entry["values"] == (list(fspec.values) if fspec.values is not None else None)
            assert entry["harmony_dependent"] == (
                name in HARMONY_DEPENDENT_FIELDS.get(family, set())
            )


def test_manifest_names_ops_and_polarities():
    m = ruleset_field_manifest()
    assert set(m["condition_ops"]) == {"eq", "in", "gte", "lte"}
    assert m["polarities"] == ["hard", "soft", "budget"]  # budget = the rate gate (gap 23)


def test_manifest_is_json_serializable():
    json.dumps(ruleset_field_manifest())  # must not raise


def test_manifest_flags_harmony_dependent_fields():
    m = ruleset_field_manifest()
    mel = m["families"]["melody"]["fields"]
    assert mel["nht_type"]["harmony_dependent"] is True
    assert mel["is_chord_tone"]["harmony_dependent"] is True
    assert mel["pc"]["harmony_dependent"] is False


def test_manifest_carries_enum_vocabularies():
    m = ruleset_field_manifest()
    motion = m["families"]["voice_motion"]["fields"]["motion"]
    assert motion["kind"] == "str"
    assert set(motion["values"]) == {"parallel", "similar", "contrary", "oblique"}
    # a plain int field has no closed vocabulary
    assert m["families"]["melody"]["fields"]["midi"]["values"] is None


# --- firing locations ---------------------------------------------------------

def _line(midis):
    # single-voice line, one note per beat, via the canonical event form
    return _canonical_sequence([[i, 1, m] for i, m in enumerate(midis)])


_LEAP_RULE = {
    "name": "t", "version": "1",
    "rules": [{"id": "no-leaps", "family": "melody",
               "forbid": {"approach_class": "leap"}, "polarity": "soft"}],
}


def test_firings_absent_by_default():
    seq = _line([60, 62, 64, 65])
    report = evaluate(_LEAP_RULE, seq)
    assert report.results[0].firings is None
    # ...and the key is omitted from the dict (byte-identical contract)
    assert "firings" not in report.to_dict()["results"][0]


def test_firings_present_and_located_when_requested():
    seq = _line([60, 62, 64, 65])  # all steps: every considered note holds
    report = evaluate(_LEAP_RULE, seq, include_firings=True)
    r = report.results[0]
    assert r.firings is not None
    assert len(r.firings) == r.items_considered
    assert all("onset_beats" in f.location for f in r.firings)
    assert all("approach_class" in f.evidence for f in r.firings)
    assert "firings" in report.to_dict()["results"][0]


def test_considered_equals_firings_plus_violations():
    # a line with a genuine leap (64->71 = 7 semitones) and steps: the invariant
    # must hold exactly, with the leap-approached note firing a violation.
    seq = _line([60, 62, 64, 71, 73])
    r = evaluate(_LEAP_RULE, seq, include_firings=True).results[0]
    assert r.items_considered == len(r.firings) + len(r.violations)
    assert r.items_considered > 0
    assert len(r.violations) >= 1  # the leap-approached note fired a violation


def test_firings_empty_list_is_distinct_from_none():
    # a rule whose every considered item violates → firings == [] (computed,
    # none held), which must NOT read the same as None (not computed).
    seq = _line([60, 67, 60, 67])  # all approaches are leaps → all violate
    forbid_all = {
        "name": "t", "version": "1",
        "rules": [{"id": "no-leaps", "family": "melody",
                   "forbid": {"approach_class": "leap"}, "polarity": "soft"}],
    }
    r = evaluate(forbid_all, seq, include_firings=True).results[0]
    assert r.firings == []
    assert r.firings is not None
    assert len(r.violations) == r.items_considered


def test_not_applicable_rule_has_no_firings():
    # a harmony-dependent rule with no harmony → applicable=False, firings None.
    rs = {
        "name": "t", "version": "1",
        "rules": [{"id": "nht", "family": "melody",
                   "forbid": {"nht_type": "escape"}, "polarity": "soft"}],
    }
    r = evaluate(rs, _line([60, 62, 64]), include_firings=True).results[0]
    assert r.applicable is False
    assert r.firings is None


# --- MCP parity ---------------------------------------------------------------

def test_mcp_tools_match_engine():
    from mts.mcp import tools

    assert tools.ruleset_field_manifest() == ruleset_field_manifest()
    assert tools.ruleset_field_manifest in tools.TOOLS

    events = [[0, 1, 60], [1, 1, 62], [2, 1, 64], [3, 1, 67]]
    engine = evaluate(_LEAP_RULE, _line([60, 62, 64, 67]), include_firings=True).to_dict()
    tool = tools.evaluate_ruleset(_LEAP_RULE, events, include_firings=True)
    assert tool == engine
