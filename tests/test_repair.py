"""Conformance repair, slice 1 (voice-motion, re-pitch edits).

Oracle: hand-built two-voice fragments with parallel perfects, repaired under an
inline no-parallels ruleset and the shipped first-species-counterpoint library
ruleset. Covers: minimal repair found + verified by the evaluator, lexicographic
ranking (iterative deepening ⇒ exact minimal edit count), edit provenance, the
soft-must-not-worsen gate, honest refusals (already conformant / unsupported
family / no repair in budget), determinism, and MCP parity.
"""

import pytest

from mts.mcp.tools import _canonical_sequence
from mts.rules import evaluate, load_named_ruleset
from mts.search import repair_sequence

NO_PARALLELS = {
    "name": "no-parallels", "version": "1",
    "rules": [{
        "id": "no-parallel-perfects", "family": "voice_motion",
        "where": {"motion": "parallel"},
        "forbid": {"interval_class_to": {"in": [0, 7]}},
        "polarity": "hard",
    }],
}
WHITE = [0, 2, 4, 5, 7, 9, 11]  # C-major pcs

# upper C5→D5 over lower F4→G4: parallel fifths.
PARALLEL_FIFTHS = [[0, 1, 72, "upper"], [1, 1, 74, "upper"],
                   [0, 1, 65, "lower"], [1, 1, 67, "lower"]]


def _seq(events):
    return _canonical_sequence(events)


# --- the repair loop ------------------------------------------------------------

def test_parallel_fifths_repaired_with_one_edit():
    r = repair_sequence(_seq(PARALLEL_FIFTHS), NO_PARALLELS, allowed_pcs=WHITE)
    assert not r.already_conformant and r.before_hard_violations == 1
    assert r.repairs and len(r.repairs[0].edits) == 1  # minimal: a single note


def test_repairs_actually_pass_the_oracle():
    # trust nothing: re-evaluate every returned repair's events independently.
    r = repair_sequence(_seq(PARALLEL_FIFTHS), NO_PARALLELS, allowed_pcs=WHITE)
    for rep in r.repairs:
        report = evaluate(NO_PARALLELS, _seq(rep.events))
        assert report.hard_rules_hold is True


def test_lexicographic_ranking():
    r = repair_sequence(_seq(PARALLEL_FIFTHS), NO_PARALLELS, allowed_pcs=WHITE)
    costs = [(len(rep.edits), rep.total_displacement) for rep in r.repairs]
    assert costs == sorted(costs)
    assert costs[0][1] == 1  # a one-semitone fix exists (e.g. F4→E4)


def test_edit_carries_provenance_and_preserves_the_rest():
    r = repair_sequence(_seq(PARALLEL_FIFTHS), NO_PARALLELS, allowed_pcs=WHITE)
    best = r.repairs[0]
    assert best.edits[0].fixes_rules == ["no-parallel-perfects"]
    # exactly one event differs from the input; durations/onsets/voices intact.
    original = {(v, o): m for o, d, m, v in
                [(e[0], e[1], e[2], e[3]) for e in PARALLEL_FIFTHS]}
    changed = [
        (voice, onset) for onset, dur, midi, voice in best.events
        if original[(voice, onset)] != midi
    ]
    assert len(changed) == 1
    assert len(best.events) == len(PARALLEL_FIFTHS)


def test_allowed_pcs_respected():
    r = repair_sequence(_seq(PARALLEL_FIFTHS), NO_PARALLELS, allowed_pcs=WHITE)
    for rep in r.repairs:
        for e in rep.edits:
            assert e.midi_to % 12 in WHITE


# --- honest refusals --------------------------------------------------------------

def test_already_conformant():
    contrary = [[0, 1, 72, "upper"], [1, 1, 71, "upper"],
                [0, 1, 65, "lower"], [1, 1, 67, "lower"]]
    r = repair_sequence(_seq(contrary), NO_PARALLELS)
    assert r.already_conformant is True and r.repairs == [] and r.reason is None


def test_unsupported_family_is_refused_not_guessed():
    melody_rule = {"name": "m", "version": "1", "rules": [{
        "id": "no-melodic-tritone", "family": "melody",
        "forbid": {"approach_interval": {"in": [6, -6]}}, "polarity": "hard"}]}
    tritone = [[0, 1, 60, "v"], [1, 1, 66, "v"]]
    r = repair_sequence(_seq(tritone), melody_rule)
    assert r.repairs == [] and "slice 1" in r.reason and "no-melodic-tritone" in r.reason


def test_unrepairable_within_budget_is_honest():
    r = repair_sequence(_seq(PARALLEL_FIFTHS), NO_PARALLELS,
                        pitch_window=1, allowed_pcs=[0, 5], max_edits=1)
    assert r.repairs == [] and "no repair within" in r.reason


def test_parameter_validation():
    seq = _seq(PARALLEL_FIFTHS)
    with pytest.raises(ValueError, match="max_edits"):
        repair_sequence(seq, NO_PARALLELS, max_edits=0)
    with pytest.raises(ValueError, match="max_edits"):
        repair_sequence(seq, NO_PARALLELS, max_edits=99)
    with pytest.raises(ValueError, match="pitch_window"):
        repair_sequence(seq, NO_PARALLELS, pitch_window=0)


# --- the whole-ruleset oracle + the species demo -----------------------------------

def test_species_counterpoint_end_to_end():
    species = load_named_ruleset("first-species-counterpoint")
    r = repair_sequence(_seq(PARALLEL_FIFTHS), species, allowed_pcs=WHITE)
    assert r.repairs, r.reason
    for rep in r.repairs:
        report = evaluate(species, _seq(rep.events))
        assert report.hard_rules_hold is True          # whole ruleset, incl. melody
        assert rep.soft_score_after is None or rep.soft_score_after >= 0.0


def test_soft_score_never_worsens():
    species = load_named_ruleset("first-species-counterpoint")
    seq = _seq(PARALLEL_FIFTHS)
    before = evaluate(species, seq).soft_score
    r = repair_sequence(seq, species, allowed_pcs=WHITE)
    for rep in r.repairs:
        if before is not None and rep.soft_score_after is not None:
            assert rep.soft_score_after >= before - 1e-9


def test_deterministic():
    a = repair_sequence(_seq(PARALLEL_FIFTHS), NO_PARALLELS, allowed_pcs=WHITE)
    b = repair_sequence(_seq(PARALLEL_FIFTHS), NO_PARALLELS, allowed_pcs=WHITE)
    assert a.to_dict() == b.to_dict()


# --- MCP parity ---------------------------------------------------------------------

def test_mcp_repair_ruleset_matches_engine():
    from mts.mcp import tools

    engine = repair_sequence(
        _seq(PARALLEL_FIFTHS), NO_PARALLELS, allowed_pcs=WHITE
    ).to_dict()
    tool = tools.repair_ruleset(NO_PARALLELS, PARALLEL_FIFTHS,
                                allowed_pcs=["C", "D", "E", "F", "G", "A", "B"])
    assert tool == engine
