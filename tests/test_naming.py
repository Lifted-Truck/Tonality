"""Phase 3 final slice: context-sensitive naming / disambiguation."""

import json

import pytest

from mts.analysis import (
    AnalyticalContext,
    infer_key,
    name_chord,
    name_chord_across_keys,
)
from mts.core.chord import Chord
from mts.core.pitch import Pitch
from mts.core.quality import ChordQuality
from mts.core.realization import Realization
from mts.dataset.builders import record_from_chord
from mts.io.loaders import load_naming_weights, load_scales

C6_AM7 = [0, 4, 7, 9]  # the canonical ambiguous set


@pytest.fixture(scope="module")
def contexts():
    scales = load_scales()
    return {
        "c_major": AnalyticalContext(tonic_pc=0, key=scales["Ionian"]),
        "a_minor": AnalyticalContext(tonic_pc=9, key=scales["Aeolian"]),
    }


def _readings(naming):
    rows = ([naming.chosen] if naming.chosen else []) + naming.alternatives
    return [(r.interpretation.root_pc, r.interpretation.quality) for r in rows]


def _bass(midi_notes):
    return Realization(tuple(Pitch.from_midi(m) for m in midi_notes), root_pc=None)


# --- the C6 = Am7 case across frames -----------------------------------------------

def test_ambiguous_without_bass_in_c_major(contexts):
    naming = name_chord(C6_AM7, contexts["c_major"])
    assert naming.is_ambiguous  # both readings are diatonic tonic-function: a real tie
    assert set(_readings(naming)[:2]) == {(0, "maj6"), (9, "min7")}
    assert naming.chosen.score == naming.alternatives[0].score


def test_bass_note_disambiguates(contexts):
    with_c = name_chord(C6_AM7, contexts["c_major"], realization=_bass([48, 64, 67, 69]))
    assert not with_c.is_ambiguous
    assert (with_c.chosen.interpretation.root_pc, with_c.chosen.interpretation.quality) == (0, "maj6")
    assert any(e.signal == "bass_is_root" for e in with_c.chosen.evidence)

    with_a = name_chord(C6_AM7, contexts["a_minor"], realization=_bass([45, 60, 64, 67]))
    assert not with_a.is_ambiguous
    assert (with_a.chosen.interpretation.root_pc, with_a.chosen.interpretation.quality) == (9, "min7")
    assert with_a.chosen.functional_role == "tonic"


def test_no_context_is_intrinsic_only_and_honest():
    naming = name_chord(C6_AM7, None)
    assert naming.context is None
    assert naming.is_ambiguous
    # No key was fabricated: no key-relative evidence anywhere.
    for reading in [naming.chosen] + naming.alternatives:
        assert all(
            e.signal in ("bass_is_root", "quality_canonicality") for e in reading.evidence
        )


def test_result_is_conditional_on_context(contexts):
    naming = name_chord(C6_AM7, contexts["c_major"])
    assert naming.context.tonic_pc == 0
    assert naming.context.key_name == "Ionian"
    assert naming.weights_version == "naming-rules.1"
    json.dumps(naming.to_dict())


# --- special-function seam -----------------------------------------------------------

def test_german_sixth_detected(contexts):
    naming = name_chord([8, 0, 3, 6], contexts["c_major"])
    assert naming.chosen.function_category == "augmented_sixth_german"
    assert any(e.signal == "special_function" for e in naming.chosen.evidence)


def test_secondary_dominant_detected(contexts):
    naming = name_chord([2, 6, 9, 0], contexts["c_major"])  # D7 in C major
    assert naming.chosen.interpretation.root_pc == 2
    assert naming.chosen.function_category == "secondary_dominant"


def test_neapolitan_detected(contexts):
    naming = name_chord([1, 5, 8], contexts["c_major"])  # Db major in C
    assert naming.chosen.function_category == "neapolitan"


def test_primary_dominant_is_not_flagged_secondary(contexts):
    naming = name_chord([7, 11, 2, 5], contexts["c_major"])  # G7: the real V7
    assert naming.chosen.interpretation.root_pc == 7
    assert naming.chosen.function_category is None
    assert naming.chosen.functional_role == "dominant"


# --- symmetric sets stay honest -------------------------------------------------------

def test_dim7_is_ambiguous_without_resolution_context(contexts):
    naming = name_chord([11, 2, 5, 8], contexts["c_major"])
    assert naming.is_ambiguous  # three diatonic roots tie; tier (c) is the follow-up
    top_scores = [r.score for r in [naming.chosen] + naming.alternatives]
    assert top_scores[0] == top_scores[1] == top_scores[2]
    # The non-diatonic root (Ab) ranks below the tied diatonic three.
    assert top_scores[3] < top_scores[0]


# --- degenerate input -------------------------------------------------------------------

def test_unmatched_set_yields_no_chosen(contexts):
    naming = name_chord([0, 1], contexts["c_major"])  # no catalog quality matches
    assert naming.chosen is None
    assert naming.alternatives == []
    assert not naming.is_ambiguous


def test_empty_input_raises(contexts):
    with pytest.raises(ValueError):
        name_chord([], contexts["c_major"])


# --- versioned weights ---------------------------------------------------------------------

def test_weights_are_versioned():
    table = load_naming_weights()
    assert table.version == "naming-rules.1"
    assert load_naming_weights("naming-rules.1") is table
    with pytest.raises(ValueError, match="Unknown naming-weights version"):
        load_naming_weights("no-such-version")


# --- ranked-key wrapper -----------------------------------------------------------------------

def test_across_keys_keeps_per_key_conditional_readings():
    # Duration-weighted C-major material; the chord is the ambiguous C6/Am7 set.
    weights = [0.0] * 12
    for pc, v in {0: 4.0, 2: 1.0, 4: 2.0, 5: 1.0, 7: 3.0, 9: 1.0, 11: 1.0}.items():
        weights[pc] = v
    keys = infer_key(weights)
    result = name_chord_across_keys(C6_AM7, keys)

    assert result.weights_version == "naming-rules.1"
    assert 1 <= len(result.per_key) <= 3
    total_weight = sum(entry.key_weight for entry in result.per_key)
    assert total_weight == pytest.approx(1.0)
    for entry in result.per_key:
        # Every reading is labeled with the context it is conditional on.
        assert entry.naming.context.tonic_pc == entry.candidate.tonic_pc
    # Combined view ranks the same two readings on top, with key-weighted evidence.
    top = {(r.interpretation.root_pc, r.interpretation.quality) for r in result.combined[:2]}
    assert top == {(0, "maj6"), (9, "min7")}
    assert all(e.signal == "key_weighted_score" for e in result.combined[0].evidence)
    json.dumps(result.to_dict())


# --- dataset record integration ------------------------------------------------------------------

def test_record_carries_naming(contexts):
    chord = Chord.from_quality(0, ChordQuality.from_intervals("maj6", [0, 4, 7, 9]))
    record = record_from_chord(chord, analytical_context=contexts["c_major"])
    assert record.analysis.naming is not None
    assert record.analysis.naming.context.tonic_pc == 0
    json.dumps(record.to_dict())
