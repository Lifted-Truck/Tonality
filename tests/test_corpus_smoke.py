"""Corpus smoke — Layer-0 invariants over REAL open-source MIDI (vendored SWD).

Runs the ruleset + pattern stack over the committed SWD smoke set (5 Schubert
Winterreise score-MIDI files, CC BY — `validation/corpus/swd/ATTRIBUTION.md`)
and asserts **invariants, not aesthetics** (the audit-charter discipline): the
pipeline ingests real scores, refusals are honest and itemized, occurrences obey
the pattern contract, induced output validates, splits and results are
deterministic. The measured (Layer-E) report lives in
`validation/exercise_rules_patterns.py`; this file is only what CI can *gate*.
"""

from pathlib import Path

import pytest

from mts.io.midi import sequence_from_midi_file
from mts.patterns import find_pattern, list_named_patterns, load_named_pattern
from mts.rules import (
    build_transition_matrix,
    evaluate,
    induce_ruleset,
    list_named_rulesets,
    load_named_ruleset,
    ruleset_to_payload,
    validation_errors,
)
from mts.temporal import segment_to_chords

CORPUS = (
    Path(__file__).resolve().parents[1]
    / "validation" / "corpus" / "swd" / "01_RawData" / "score_midi"
)
pytestmark = pytest.mark.skipif(
    not CORPUS.is_dir(), reason="vendored SWD smoke corpus not present"
)


@pytest.fixture(scope="module")
def corpus():
    """Ingested + segmented once per module (keeps the suite fast)."""
    pieces = []
    for path in sorted(CORPUS.glob("*.mid")):
        seq = sequence_from_midi_file(str(path))
        pieces.append((path.name, seq, segment_to_chords(seq)))
    assert len(pieces) == 5, "the vendored SWD smoke set is 5 songs"
    return pieces


def test_real_scores_ingest_and_segment(corpus):
    for name, seq, seg in corpus:
        assert seq.events and seq.voices(), name
        assert seg.key_inferred and seg.mode in ("major", "minor"), name
        assert 0 <= seg.tonic_pc <= 11 and seg.chords, name
        # honesty: unnameable spans are surfaced, and every one carries a reason
        for span in seg.spans:
            if span.root_pc is None:
                assert span.reason, f"{name}: unnameable span without a reason"


def test_named_rulesets_evaluate_with_honest_refusals(corpus):
    for rs_name in list_named_rulesets():
        rs = load_named_ruleset(rs_name)
        needs_chords = any(r.family == "harmony" for r in rs.rules)
        for name, seq, seg in corpus:
            report = evaluate(
                rs, seq,
                chords=seg.chords if needs_chords else None,
                key=seg.key if needs_chords else None,
            )
            assert report.hard_rules_hold in (True, False, None), (rs_name, name)
            for result in report.results:
                if not result.applicable:
                    assert result.reason, (
                        f"{rs_name}/{result.rule_id} on {name}: refusal without a reason"
                    )


def test_named_patterns_obey_the_occurrence_contract(corpus):
    for pat_name in list_named_patterns():
        pattern = load_named_pattern(pat_name)
        for name, seq, seg in corpus:
            m = find_pattern(
                seq, pattern,
                key=seg.key if pattern.pitch_level == "degree" else None,
            )
            assert m.count == len(m.occurrences)
            for occ in m.occurrences:
                assert len(occ.midis) == pattern.n_notes, (pat_name, name)
                assert len(occ.iois) == pattern.n_notes - 1
                assert occ.onsets == sorted(occ.onsets)
                if pattern.pitch_level == "degree":
                    assert tuple(occ.degrees) == pattern.elements
                if pattern.pitch_level == "contour":
                    assert tuple(occ.moves) == pattern.elements


def test_harmony_induction_over_segmented_real_corpus(corpus):
    chord_corpus = [(seg.chords, seg.key) for _, _, seg in corpus]
    result = induce_ruleset(family="harmony", chord_corpus=chord_corpus)
    assert result.pieces == 5
    assert result.exploratory is True  # 5 pieces is below the confirmatory floor
    if result.ruleset.rules:
        assert not validation_errors(ruleset_to_payload(result.ruleset))


def test_transition_matrix_heldout_split_is_by_piece(corpus):
    chord_corpus = [(seg.chords, seg.key) for _, _, seg in corpus]
    train, held = chord_corpus[:-1], chord_corpus[-1:]
    matrix = build_transition_matrix(train, state="degree", source="swd-smoke")
    assert matrix.n_pieces == 4 and matrix.prior_version == "distribution.1"
    ce = matrix.cross_entropy(held)
    assert ce.n_pieces == 1 and ce.scored_transitions + ce.oov_transitions > 0
    # laplace smoothing: an in-vocabulary transition can never be infinite surprise
    if ce.scored_transitions and not ce.has_zero_probability:
        assert ce.cross_entropy_bits is not None and ce.perplexity >= 1.0


def test_full_stack_is_deterministic_on_real_music(corpus):
    name, seq, _ = corpus[0]
    a = segment_to_chords(seq)
    b = segment_to_chords(seq)
    assert a.to_dict() == b.to_dict(), name
    rs = load_named_ruleset("first-species-counterpoint")
    assert evaluate(rs, seq).to_dict() == evaluate(rs, seq).to_dict()
    arch = load_named_pattern("arch-contour")
    assert find_pattern(seq, arch).to_dict() == find_pattern(seq, arch).to_dict()
