"""Tests for the named ruleset library (gap D) — the first-species counterpoint
ruleset, and empirical proof that its documented expressiveness gaps are real
DSL limitations (not authoring oversights).
"""

import pytest

from mts.mcp.tools import _canonical_sequence
from mts.rules import (
    RulesetValidationError,
    evaluate,
    list_named_rulesets,
    load_named_ruleset,
)
from mts.rules.schema import FAMILIES, parse_ruleset, ruleset_to_payload

FIRST_SPECIES = "first-species-counterpoint"


def _two_voice(cf, cp):
    """Two whole-note voices (cf below, cp above) as a canonical Sequence."""
    events = [[i, 1, m, "cf"] for i, m in enumerate(cf)]
    events += [[i, 1, m, "cp"] for i, m in enumerate(cp)]
    return _canonical_sequence(events)


# --- library plumbing ---------------------------------------------------------

def test_first_species_is_shipped_and_valid():
    assert FIRST_SPECIES in list_named_rulesets()
    rs = load_named_ruleset(FIRST_SPECIES)
    assert rs.version == "fux-first-species.1"
    assert {r.id for r in rs.rules} == {
        "no-parallel-perfects", "no-direct-perfects", "consonant-verticals-only",
        "no-melodic-tritone", "recover-leap-by-step",
    }


def test_shipped_ruleset_round_trips_through_the_parser():
    rs = load_named_ruleset(FIRST_SPECIES)
    assert parse_ruleset(ruleset_to_payload(rs)) == rs


def test_unknown_ruleset_raises_with_the_known_list():
    with pytest.raises(ValueError, match="Unknown ruleset"):
        load_named_ruleset("no-such-ruleset")


def test_shipped_rulesets_all_validate():
    # Every ruleset in the library is held to the strict DSL contract.
    for name in list_named_rulesets():
        load_named_ruleset(name)  # raises RulesetValidationError if it drifted


# --- the rules actually enforce first-species counterpoint --------------------

def test_clean_first_species_holds():
    # Parallel/similar thirds and tenths, stepwise lines, no perfect-consonance
    # arrivals by similar motion: a textbook-clean note-against-note fragment.
    seq = _two_voice(cf=[60, 62, 64, 62, 60], cp=[76, 77, 79, 77, 76])
    report = evaluate(load_named_ruleset(FIRST_SPECIES), seq)
    assert report.hard_rules_hold is True
    assert report.hard_violation_count == 0


def test_parallel_fifths_are_caught():
    seq = _two_voice(cf=[60, 62], cp=[67, 69])  # both +2, vertical P5 → P5
    report = evaluate(load_named_ruleset(FIRST_SPECIES), seq)
    fired = {r.rule_id for r in report.results if r.violations}
    assert "no-parallel-perfects" in fired
    assert report.hard_rules_hold is False


def test_parallel_octaves_are_caught():
    seq = _two_voice(cf=[60, 62], cp=[72, 74])  # vertical octave → octave
    fired = {r.rule_id for r in evaluate(load_named_ruleset(FIRST_SPECIES), seq).results
             if r.violations}
    assert "no-parallel-perfects" in fired


def test_dissonant_vertical_is_caught():
    seq = _two_voice(cf=[60, 62], cp=[61, 64])  # first vertical m2 (ic 1) — dissonant
    fired = {r.rule_id for r in evaluate(load_named_ruleset(FIRST_SPECIES), seq).results
             if r.violations}
    assert "consonant-verticals-only" in fired


def test_hidden_fifths_by_similar_motion_are_caught():
    # both voices ascend (similar) INTO a perfect fifth → direct/hidden fifths.
    seq = _two_voice(cf=[60, 62], cp=[64, 69])  # cf +2, cp +5 (similar), arrive P5
    fired = {r.rule_id for r in evaluate(load_named_ruleset(FIRST_SPECIES), seq).results
             if r.violations}
    assert "no-direct-perfects" in fired


def test_melodic_tritone_leap_is_caught():
    # a lone line with an F->B tritone leap (65 -> 71 = +6).
    seq = _canonical_sequence([[0, 1, 65], [1, 1, 71], [2, 1, 72]])
    fired = {r.rule_id for r in evaluate(load_named_ruleset(FIRST_SPECIES), seq).results
             if r.violations}
    assert "no-melodic-tritone" in fired


# --- the expressiveness gaps are REAL (the deliverable's other half) ----------

def test_dsl_cannot_compare_two_fields_directly():
    # "counterpoint stays above the cantus firmus" needs a_to_midi > b_to_midi —
    # a cross-field comparison. The DSL's condition value is always a literal
    # (or a literal list / bound), never another field: proven here by trying to
    # author it and getting a strict-validation rejection.
    crossing_rule = {
        "name": "x", "version": "1",
        "rules": [{"id": "no-crossing", "family": "voice_motion",
                   "forbid": {"a_to_midi": {"lte": "b_to_midi"}}, "polarity": "hard"}],
    }
    with pytest.raises(RulesetValidationError):
        parse_ruleset(crossing_rule)


def test_dsl_has_no_phrase_or_global_scope_field():
    # "begin/end on a perfect consonance" and "a single melodic climax" need a
    # first/last/global position the vocabulary does not carry — no family
    # exposes a phrase-position or is-first/is-last field.
    all_fields = {f for fields in FAMILIES.values() for f in fields}
    for absent in ("is_first", "is_last", "position_in_phrase", "is_climax"):
        assert absent not in all_fields


def test_dsl_has_no_run_length_field():
    # "no more than three consecutive parallel thirds" needs a run-length /
    # consecutive-count the flat per-item vocabulary cannot express.
    all_fields = {f for fields in FAMILIES.values() for f in fields}
    for absent in ("run_length", "consecutive_count", "streak"):
        assert absent not in all_fields


# --- MCP parity ---------------------------------------------------------------

def test_mcp_tools_match_engine():
    from mts.mcp import tools

    assert tools.list_named_rulesets() == list_named_rulesets()
    assert tools.load_named_ruleset(FIRST_SPECIES) == ruleset_to_payload(
        load_named_ruleset(FIRST_SPECIES)
    )
    assert tools.list_named_rulesets in tools.TOOLS
    assert tools.load_named_ruleset in tools.TOOLS
