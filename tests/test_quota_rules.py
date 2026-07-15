"""gap 23 — quota (budget) rules: a rule gated on its violation RATE.

"Parallel fifths no greater than 5% of the time" (Julian). A budget rule holds
iff violations / items_considered <= max_rate — a threshold on a MEASURED rate,
deterministic, no learning (ROADMAP Decision 15: the engine counts, it does not
model). These tests pin the gate, its boundary, the aggregate, the unchanged
hard_rules_hold contract, and the total validation.
"""

from __future__ import annotations

import pytest

from mts.rules import evaluate, parse_ruleset, validation_errors, ruleset_to_payload
from mts.mcp.tools import _canonical_sequence

# 5 moments → 4 voice-pair transitions, exactly ONE of them a parallel fifth.
# (0→1 both up, ic 7→7 = parallel P5 ✗ · 1→2 contrary · 2→3 contrary ·
#  3→4 both up but ic 7→5 = similar, not parallel.)
_MOMENTS = [(72, 65), (74, 67), (72, 69), (74, 67), (76, 71)]
_ONE_IN_FOUR = 0.25


def _seq():
    ev = []
    for b, (u, l) in enumerate(_MOMENTS):
        ev += [[b, 1, u, 90, "u"], [b, 1, l, 90, "l"]]
    return _canonical_sequence(ev)


def _budget(max_rate):
    # No `where`: every transition is CONSIDERED, so the rate reads "of all
    # motion" — the musically meaningful denominator. The forbid ANDs instead.
    return parse_ruleset({"name": "q", "version": "1", "rules": [{
        "id": "parallel-perfects-budget", "family": "voice_motion",
        "forbid": {"motion": "parallel", "interval_class_to": {"in": [0, 7]}},
        "polarity": "budget", "max_rate": max_rate}]})


def test_the_fixture_really_is_one_in_four():
    r = evaluate(_budget(1.0), _seq()).results[0]
    assert r.items_considered == 4 and len(r.violations) == 1
    assert r.conformance == pytest.approx(1 - _ONE_IN_FOUR)


def test_budget_exceeded_fails():
    r = evaluate(_budget(0.05), _seq())          # 25% > 5%
    assert r.results[0].holds is False
    assert r.budgets_hold is False


def test_exactly_at_budget_holds():
    r = evaluate(_budget(_ONE_IN_FOUR), _seq())  # 25% <= 25%, inclusive
    assert r.results[0].holds is True and r.budgets_hold is True


def test_under_budget_holds():
    assert evaluate(_budget(0.5), _seq()).budgets_hold is True


def test_budget_does_not_touch_the_hard_contract():
    # No hard rule → hard_rules_hold stays None (its contract is unchanged);
    # a budget failure is reported on budgets_hold, not smuggled into hard.
    r = evaluate(_budget(0.05), _seq())
    assert r.hard_rules_hold is None and r.hard_violation_count == 0
    assert r.budgets_hold is False


def test_budgets_hold_is_none_without_budget_rules():
    rs = parse_ruleset({"name": "h", "version": "1", "rules": [{
        "id": "no-parallels", "family": "voice_motion", "where": {"motion": "parallel"},
        "forbid": {"interval_class_to": {"in": [0, 7]}}, "polarity": "hard"}]})
    r = evaluate(rs, _seq())
    assert r.budgets_hold is None          # no signal, not a vacuous True
    assert r.hard_rules_hold is False      # the hard rule still fires as before


def test_budget_with_nothing_considered_holds_vacuously():
    # A rule whose stream yields no considered items: no violations occurred, so
    # the budget is not exceeded — same convention as a vacuous hard rule.
    rs = parse_ruleset({"name": "q", "version": "1", "rules": [{
        "id": "never", "family": "voice_motion", "where": {"motion": "parallel"},
        "forbid": {"interval_class_to": {"in": [3]}}, "polarity": "budget",
        "max_rate": 0.0}]})
    r = evaluate(rs, _canonical_sequence([[0, 1, 60, 90, "a"], [0, 1, 64, 90, "b"]]))
    res = r.results[0]
    assert res.items_considered == 0 and res.conformance is None
    assert res.holds is True and r.budgets_hold is True


def test_zero_budget_is_exactly_a_hard_rule():
    strict = evaluate(_budget(0.0), _seq()).results[0]
    assert strict.holds is False            # 25% > 0%
    assert len(strict.violations) == 1      # same evidence a hard rule reports


def test_soft_score_ignores_budget_rules():
    # budgets gate; they are not preferences and must not enter the soft score.
    assert evaluate(_budget(0.05), _seq()).soft_score is None


def test_validation_is_total_and_strict():
    def errs(rule):
        return validation_errors({"name": "x", "version": "1", "rules": [rule]})
    base = {"id": "a", "family": "melody", "forbid": {"pc": 1}}
    assert errs({**base, "polarity": "budget", "max_rate": 0.05}) == []
    assert any("max_rate: required" in e for e in errs({**base, "polarity": "budget"}))
    assert any("only budget rules" in e for e in errs({**base, "polarity": "soft", "max_rate": 0.1}))
    assert any("0..1" in e for e in errs({**base, "polarity": "budget", "max_rate": 1.5}))
    assert any("only soft rules take a weight" in e
               for e in errs({**base, "polarity": "budget", "max_rate": 0.1, "weight": 2}))
    assert any("'hard', 'soft' or 'budget'" in e for e in errs({**base, "polarity": "nope"}))


def test_payload_round_trips():
    rs = _budget(0.05)
    payload = ruleset_to_payload(rs)
    assert payload["rules"][0]["max_rate"] == 0.05
    assert payload["rules"][0]["polarity"] == "budget"
    assert parse_ruleset(payload) == rs


def test_mcp_reports_budgets_hold():
    from mts.mcp import tools

    ev = [[b, 1, m, 90, v] for b, (u, l) in enumerate(_MOMENTS)
          for m, v in ((u, "u"), (l, "l"))]
    out = tools.evaluate_ruleset(ruleset=ruleset_to_payload(_budget(0.05)), events=ev)
    assert out["budgets_hold"] is False and out["hard_rules_hold"] is None
