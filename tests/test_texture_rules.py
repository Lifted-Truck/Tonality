"""gap E slice 3 — the `texture` rule family (rules over part-relation atoms).

Texture rules are threshold predicates over the pairwise atoms of
temporal.part_relations, evaluated by the generic rules engine (rules are data —
no new evaluator entry point beyond the family's item stream). These tests pin:
the hard/soft evaluation, the honest not-applicable / not-considered behavior on
degenerate or claim-less input, strict validation of the new field vocabulary,
and that the shipped illustrative ruleset loads and fires.
"""

from __future__ import annotations

import pytest

from mts.rules import evaluate, parse_ruleset, validation_errors, load_named_ruleset
from mts.mcp.tools import _canonical_sequence


def _rule(rid, where, check, *, kind="require", polarity="hard", weight=1.0):
    r = {"id": rid, "family": "texture", kind: check, "polarity": polarity}
    if where:  # `where` must be omitted when empty (a non-empty object if present)
        r["where"] = where
    if polarity == "soft":
        r["weight"] = weight
    return {"name": "t", "version": "1", "rules": [r]}


def _locked_texture():
    """bass doubles the kick's onsets; a held C-major pad; a chord-tone topline."""
    ev = []
    for b in range(4):
        ev += [[b, 0.1, 36, "kick"], [b, 0.5, 48, "bass"]]
    ev += [[0, 4, 60, "pad"], [0, 4, 64, "pad"], [0, 4, 67, "pad"]]
    for b, p in enumerate((60, 64, 67, 72)):
        ev.append([b, 0.5, p, "topline"])
    return _canonical_sequence(ev)


def _one(result):
    return result.results[0]


def test_bass_locked_to_kick_holds():
    rs = parse_ruleset(_rule("lock", {"voice_a": "bass", "voice_b": "kick"},
                             {"onset_synchrony": {"gte": 0.8}}))
    res = _one(evaluate(rs, _locked_texture()))
    assert res.applicable and res.items_considered == 1
    assert res.holds is True and res.conformance == 1.0


def test_bass_off_the_kick_violates():
    rs = parse_ruleset(_rule("lock", {"voice_a": "bass", "voice_b": "kick"},
                             {"onset_synchrony": {"gte": 0.8}}))
    ev = []
    for b in range(4):
        ev += [[b, 0.1, 36, "kick"], [b + 0.3, 0.1, 48, "bass"]]
    res = _one(evaluate(rs, _canonical_sequence(ev)))
    assert res.holds is False and res.conformance == 0.0
    assert res.violations[0].evidence["onset_synchrony"] == 0.0


def test_directional_chord_tone_support_soft_rule():
    # a=pad, b=topline (sorted): b_vs_a = topline tones over the pad = 1.0 ≥ 0.6.
    rs = parse_ruleset(_rule("ct", {"voice_a": "pad", "voice_b": "topline"},
                             {"chord_tone_support_b_vs_a": {"gte": 0.6}},
                             polarity="soft", weight=2.0))
    res = _one(evaluate(rs, _locked_texture()))
    assert res.polarity == "soft" and res.conformance == 1.0


def test_register_rule_reads_the_signed_gap():
    # a=bass(48), b=topline(60+): gap = topline − bass ≥ 7 semitones.
    rs = parse_ruleset(_rule("reg", {"voice_a": "bass", "voice_b": "topline"},
                             {"register_gap_mean": {"gte": 7}}))
    assert _one(evaluate(rs, _locked_texture())).holds is True


def test_fewer_than_two_parts_is_not_applicable():
    rs = parse_ruleset(_rule("lock", {"voice_a": "bass", "voice_b": "kick"},
                             {"onset_synchrony": {"gte": 0.8}}))
    res = _one(evaluate(rs, _canonical_sequence([[0, 1, 60, "solo"], [1, 1, 62, "solo"]])))
    assert res.applicable is False
    assert "two parts" in res.reason


def test_none_atom_excludes_the_pair_from_consideration():
    # Two parts that never sound together → register_gap_mean is None; a rule
    # checking it considers zero items (absence of evidence is not a violation).
    rs = parse_ruleset(_rule("reg", {}, {"register_gap_mean": {"gte": 0}}))
    ev = [[0, 0.4, 60, "a"], [1, 0.4, 62, "a"], [2, 0.4, 48, "b"], [3, 0.4, 50, "b"]]
    res = _one(evaluate(rs, _canonical_sequence(ev)))
    assert res.applicable is True and res.items_considered == 0
    assert res.conformance is None  # nothing considered → no claim, not a 1.0 or 0.0


def test_where_must_use_the_sorted_pair_order():
    # PartRelation orders voice_a < voice_b; a where naming them reversed matches
    # nothing (so the rule silently considers zero — the caller must sort).
    rs = parse_ruleset(_rule("lock", {"voice_a": "kick", "voice_b": "bass"},
                             {"onset_synchrony": {"gte": 0.8}}))
    res = _one(evaluate(rs, _locked_texture()))
    assert res.items_considered == 0


def test_validation_accepts_texture_and_rejects_unknown_field():
    assert validation_errors(_rule("ok", {}, {"onset_synchrony": {"gte": 0.5}})) == []
    errs = validation_errors(_rule("bad", {}, {"tightness": {"gte": 0.5}}))
    assert errs and any("tightness" in e for e in errs)


def test_shipped_illustrative_ruleset_loads_and_fires():
    rs = load_named_ruleset("layered-arrangement-texture")
    assert len(rs.rules) == 3 and all(r.family == "texture" for r in rs.rules)
    report = evaluate(rs, _locked_texture())
    # every rule finds its named pair on the relabelled texture and holds
    considered = {r.rule_id: r.items_considered for r in report.results}
    assert all(c == 1 for c in considered.values()), considered
    assert report.soft_score == 1.0


def test_mcp_evaluate_ruleset_handles_texture():
    from mts.mcp import tools

    events = [[0, 0.1, 36, "kick"], [1, 0.1, 36, "kick"],
              [0, 0.5, 48, "bass"], [1, 0.5, 48, "bass"]]
    payload = {"name": "t", "version": "1", "rules": [
        {"id": "lock", "family": "texture", "where": {"voice_a": "bass", "voice_b": "kick"},
         "require": {"onset_synchrony": {"gte": 0.8}}, "polarity": "hard"}]}
    out = tools.evaluate_ruleset(ruleset=payload, events=events)
    assert out["hard_rules_hold"] is True
