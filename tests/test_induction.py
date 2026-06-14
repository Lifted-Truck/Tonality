"""Phase 4.6 ruleset induction (slice 1): Apriori + Fisher + BH-FDR.

Version-space mining, not learning — exact and deterministic. Tests cover the
statistical core (Fisher's exact, BH-FDR), the mining (anti-monotonic / closed /
arity / None-semantics), determinism + DSL round-trip, and the headline contract:
a planted rule is recovered as significant; the corpus the rules came from
conforms to them.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from fractions import Fraction

import pytest

from mts.core.pitch import Pitch
from mts.rules import evaluate, induce_ruleset, parse_ruleset, validation_errors
from mts.rules.induction import _bh_qvalues, _fisher_one_sided
from mts.temporal import Event, Sequence


# --- Fisher's exact -----------------------------------------------------------------------


def test_fisher_matches_hand_computed_tail():
    # Table a=10,b=0,c=2,d=8; right tail (i>=10) is just P(10) = C(10,10)C(10,2)/C(20,12).
    expected = math.comb(10, 10) * math.comb(10, 2) / math.comb(20, 12)
    assert _fisher_one_sided(10, 0, 2, 8, right_tail=True) == pytest.approx(expected)


def test_fisher_recurrence_equals_direct_comb_form():
    a, b, c, d = 7, 3, 2, 9
    n, row1, col1 = a + b + c + d, a + b, a + c
    lo, hi = max(0, col1 - (c + d)), min(row1, col1)
    direct = sum(
        Fraction(math.comb(row1, i) * math.comb(c + d, col1 - i), math.comb(n, col1))
        for i in range(a, hi + 1)
    )
    assert _fisher_one_sided(a, b, c, d, right_tail=True) == pytest.approx(float(direct))


def test_fisher_independent_table_is_unsurprising():
    assert _fisher_one_sided(5, 5, 5, 5, right_tail=True) > 0.5


def test_fisher_bounds():
    for tbl in ((10, 0, 2, 8), (5, 5, 5, 5), (1, 9, 8, 2)):
        for rt in (True, False):
            p = _fisher_one_sided(*tbl, right_tail=rt)
            assert 0.0 < p <= 1.0


# --- BH-FDR -------------------------------------------------------------------------------


def test_bh_qvalues_match_textbook_stepup():
    # m=3, p=[0.001,0.04,0.5] → q=[0.003, 0.06, 0.5]
    assert _bh_qvalues([0.001, 0.04, 0.5]) == pytest.approx([0.003, 0.06, 0.5])


def test_bh_correction_is_load_bearing():
    # raw p=0.04 < 0.05 but its q exceeds 0.05 once corrected — FDR demotes it.
    q = _bh_qvalues([0.001, 0.04, 0.5])
    assert 0.04 < 0.05 and q[1] > 0.05


def test_bh_monotone_and_bounded():
    q = _bh_qvalues([0.2, 0.01, 0.3, 0.001, 0.05])
    assert all(0.0 <= v <= 1.0 for v in q)
    order = sorted(range(5), key=lambda i: [0.2, 0.01, 0.3, 0.001, 0.05][i])
    sorted_q = [q[i] for i in order]
    assert sorted_q == sorted(sorted_q)  # non-decreasing in p order


# --- corpus generators --------------------------------------------------------------------


def _two_voice(moments) -> Sequence:
    events = []
    for i, (a, b) in enumerate(moments):
        events.append(Event(float(i), 1.0, Pitch.from_midi(a), voice="v0"))
        events.append(Event(float(i), 1.0, Pitch.from_midi(b), voice="v1"))
    return Sequence.from_events(events)


def _planted_corpus(n_pieces=40, seed=13):
    """Parallel motion (interval-preserving) stays a third; fifths are reached
    only by non-parallel motion — with a rare 12% parallel-at-a-fifth exception
    so the forbid rule is recoverable (not absorbed by closed condensation)."""
    rng = random.Random(seed)
    corpus = []
    for _ in range(n_pieces):
        a, b = 60, 64
        moments = [(a, b)]
        for _ in range(12):
            interval = (b - a) % 12
            if interval == 7:
                if rng.random() < 0.12:
                    s = rng.choice([-2, 2]); a += s; b += s  # rare parallel-at-fifth
                else:
                    a += 2; b = a + 4
            elif rng.random() < 0.6:
                s = rng.choice([-2, 2]); a += s; b += s      # parallel third
            else:
                a -= 2; b = a + 7                            # third -> fifth
            moments.append((a, b))
        corpus.append(_two_voice(moments))
    return corpus


# --- planted recovery (the headline) ------------------------------------------------------


def test_recovers_the_planted_rule_as_significant():
    result = induce_ruleset(_planted_corpus(), family="voice_motion")
    hits = [
        (r, e)
        for r, e in zip(result.ruleset.rules, result.evidence)
        if e.where == {"motion": "parallel"}
        and r.check_kind == "forbid"
        and e.check == {"interval_class_to": 7}
    ]
    assert hits, "planted 'parallel forbid perfect-fifth' rule not recovered"
    rule, ev = hits[0]
    assert ev.leverage < 0 and ev.significant and ev.q_value <= 0.05
    assert rule.polarity == "soft" and rule.weight >= 1.0


def test_corpus_conforms_to_its_own_induced_rules():
    corpus = _planted_corpus()
    result = induce_ruleset(corpus, family="voice_motion")
    # The forbid rule's violations on a source piece are exactly its a-cell-type
    # counterexamples; conformance over the corpus should be high.
    report = evaluate(result.ruleset, corpus[0])
    soft = [r for r in report.results if r.applicable and r.conformance is not None]
    assert soft and sum(r.conformance for r in soft) / len(soft) > 0.5


# --- structural invariants ----------------------------------------------------------------


def test_emitted_rules_are_well_formed():
    result = induce_ruleset(_planted_corpus(), family="voice_motion")
    assert result.ruleset.rules
    for rule, ev in zip(result.ruleset.rules, result.evidence):
        assert len(rule.where) <= 3                       # arity cap
        assert len({c.field for c in rule.where}) == len(rule.where)  # no same-field
        assert rule.polarity == "soft" and rule.weight >= 1.0
        assert (rule.check_kind == "forbid") == (ev.leverage < 0)
        assert (rule.check_kind == "require") == (ev.leverage > 0)


def test_output_round_trips_through_the_validator():
    result = induce_ruleset(_planted_corpus(), family="voice_motion")
    payload = result.to_dict()["ruleset"]
    assert validation_errors(payload) == []
    parse_ruleset(payload)  # does not raise


def test_deterministic_under_reordering():
    corpus = _planted_corpus()
    a = induce_ruleset(corpus, family="voice_motion").to_dict()
    shuffled = list(corpus)
    random.Random(99).shuffle(shuffled)
    b = induce_ruleset(shuffled, family="voice_motion").to_dict()
    # piece-presence support + canonical ordering ⇒ order-invariant output
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_result_cites_the_versioned_prior():
    result = induce_ruleset(_planted_corpus(), family="voice_motion")
    assert result.scoring_prior["version"] == "induction.fisher-bh.1"
    assert result.tests_performed >= len(result.ruleset.rules)


# --- None semantics + small-corpus honesty ------------------------------------------------


def test_melody_without_harmony_emits_no_harmony_dependent_rules():
    rng = random.Random(5)
    corpus = []
    for _ in range(40):
        midis = [60 + rng.choice([0, 2, 4, 5, 7]) for _ in range(8)]
        corpus.append(Sequence.from_events(
            [Event(float(i), 1.0, Pitch.from_midi(m)) for i, m in enumerate(midis)]
        ))
    result = induce_ruleset(corpus, family="melody")  # no harmony
    for rule in result.ruleset.rules:
        fields = {c.field for c in rule.where} | {c.field for c in rule.check}
        assert "nht_type" not in fields and "is_chord_tone" not in fields


def test_small_corpus_is_flagged_exploratory():
    result = induce_ruleset(_planted_corpus(n_pieces=5), family="voice_motion")
    assert result.exploratory is True and result.caveat is not None


def test_tiny_corpus_below_support_floor_emits_nothing():
    result = induce_ruleset(_planted_corpus(n_pieces=2), family="voice_motion")
    assert result.ruleset.rules == ()
    assert result.exploratory is True


def test_unknown_family_raises():
    with pytest.raises(ValueError, match="Unknown family"):
        induce_ruleset([], family="harmony")


# --- disjunction (`in`) merge pass --------------------------------------------------------


def _both_perfect_corpus(n_pieces=45, seed=21):
    """Parallel motion avoids BOTH the octave (ic 0) and the fifth (ic 7);
    both are reached only by non-parallel motion (rare parallel exceptions)."""
    rng = random.Random(seed)
    corpus = []
    for _ in range(n_pieces):
        a, b = 60, 64
        moments = [(a, b)]
        for _ in range(14):
            iv = (b - a) % 12
            if iv in (0, 7):
                if rng.random() < 0.1:
                    s = rng.choice([-2, 2]); a += s; b += s
                else:
                    a += 2; b = a + 4
            elif rng.random() < 0.55:
                s = rng.choice([-2, 2]); a += s; b += s
            else:
                a -= 2; b = a + rng.choice([0, 7])
            moments.append((a, b))
        corpus.append(_two_voice(moments))
    return corpus


def _parallel_forbid(result):
    """The (rule, evidence) whose where is {motion: parallel} forbidding ic_to."""
    return [
        (r, e)
        for r, e in zip(result.ruleset.rules, result.evidence)
        if e.where == {"motion": "parallel"} and r.check_kind == "forbid"
        and "interval_class_to" in e.check
    ]


def test_disjunction_merges_into_one_in_rule():
    result = induce_ruleset(_both_perfect_corpus(), family="voice_motion")
    hits = [(r, e) for r, e in _parallel_forbid(result) if e.merged]
    assert len(hits) == 1, "expected exactly one merged parallel-forbid rule"
    rule, ev = hits[0]
    assert ev.check == {"interval_class_to": {"in": [0, 7]}}
    assert ev.leverage < 0 and ev.significant
    # the DSL `in` consequent is built with the in-operator
    assert rule.check[0].op == "in" and set(rule.check[0].value) == {0, 7}


def test_flag_off_keeps_the_singletons():
    result = induce_ruleset(_both_perfect_corpus(), family="voice_motion",
                            merge_disjunctions=False)
    values = {
        e.check["interval_class_to"]
        for r, e in _parallel_forbid(result) if not e.merged
    }
    assert {0, 7} <= values  # both forbids present, unmerged
    assert all(not e.merged for _, e in zip(result.ruleset.rules, result.evidence))


def test_merge_pools_evidence_and_preserves_rigor():
    raw = induce_ruleset(_both_perfect_corpus(), family="voice_motion",
                         merge_disjunctions=False)
    singles = {
        e.check["interval_class_to"]: e
        for r, e in _parallel_forbid(raw) if not e.merged
    }
    merged = induce_ruleset(_both_perfect_corpus(), family="voice_motion")
    m_ev = next(e for r, e in _parallel_forbid(merged) if e.merged)
    # pooled a = sum of the singletons' a (same context + field, disjoint values)
    assert m_ev.contingency["a"] == sum(singles[v].contingency["a"] for v in (0, 7))
    # pooling strengthens: the merged p is no worse than either constituent's
    assert m_ev.p_value <= min(singles[v].p_value for v in (0, 7)) + 1e-12


def test_singleton_consequent_is_not_merged():
    # The slice-1 corpus forbids only ic 7 under parallel — a group of size 1
    # stays a single-value rule (nothing to merge).
    result = induce_ruleset(_planted_corpus(), family="voice_motion")
    hits = _parallel_forbid(result)
    assert hits and all(not e.merged for _, e in hits)


def test_merged_rule_round_trips_through_the_validator():
    result = induce_ruleset(_both_perfect_corpus(), family="voice_motion")
    payload = result.to_dict()["ruleset"]
    assert validation_errors(payload) == []
    parse_ruleset(payload)
    assert any(  # an in-consequent survives serialization
        isinstance(cond, dict) and "in" in cond
        for rule in payload["rules"] for k in ("forbid", "require")
        for cond in rule.get(k, {}).values()
    )
