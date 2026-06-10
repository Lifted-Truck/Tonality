"""Phase 3.5b: key induction (global-key v1, versioned profiles)."""

import json

import pytest

from mts.analysis import (
    AnalyticalContext,
    KeyCandidate,
    candidate_context,
    infer_key,
)
from mts.core.pitch import Pitch
from mts.io.loaders import load_key_profiles
from mts.temporal import Event, Sequence


def _weights(pairs: dict[int, float]) -> list[float]:
    weights = [0.0] * 12
    for pc, value in pairs.items():
        weights[pc] = value
    return weights

# C major scale, tonic-and-dominant weighted (a clearly tonal profile).
C_MAJOR_WEIGHTED = _weights({0: 4.0, 2: 1.0, 4: 2.0, 5: 1.0, 7: 3.0, 9: 1.0, 11: 1.0})
# C major scale, all degrees equal — the relative-ambiguity case.
DIATONIC_UNIFORM = _weights({pc: 1.0 for pc in (0, 2, 4, 5, 7, 9, 11)})


# --- core behavior -------------------------------------------------------------

def test_profile_itself_scores_perfectly():
    profiles = load_key_profiles()
    result = infer_key(list(profiles.profiles["major"]))
    assert (result.best.tonic_pc, result.best.mode) == (0, "major")
    assert result.best.score == pytest.approx(1.0)


def test_clear_c_major():
    result = infer_key(C_MAJOR_WEIGHTED)
    assert (result.best.tonic_pc, result.best.mode) == (0, "major")
    assert result.margin > 0.05


def test_minor_detection():
    # A natural minor, tonic-weighted.
    weights = _weights({9: 4.0, 11: 1.0, 0: 2.0, 2: 1.0, 4: 2.0, 5: 1.0, 7: 1.0})
    result = infer_key(weights)
    assert (result.best.tonic_pc, result.best.mode) == (9, "minor")


def test_transposition_shifts_tonic():
    base = infer_key(C_MAJOR_WEIGHTED)
    for shift in (3, 7):
        rotated = [C_MAJOR_WEIGHTED[(pc - shift) % 12] for pc in range(12)]
        result = infer_key(rotated)
        assert (result.best.tonic_pc, result.best.mode) == (shift, "major")
        assert result.best.score == pytest.approx(base.best.score)
        assert result.margin == pytest.approx(base.margin)


def test_relative_keys_surface_as_near_tie():
    """Uniform diatonic content is genuinely ambiguous — the result says so."""
    ambiguous = infer_key(DIATONIC_UNIFORM)
    confident = infer_key(C_MAJOR_WEIGHTED)
    top_two = {(c.tonic_pc, c.mode) for c in ambiguous.candidates[:2]}
    assert (0, "major") in top_two
    assert ambiguous.margin < confident.margin
    # The relative minor must rank well above an unrelated key.
    ranking = [(c.tonic_pc, c.mode) for c in ambiguous.candidates]
    assert ranking.index((9, "minor")) < ranking.index((1, "major"))


def test_duration_weighting_changes_the_reading():
    """Same pitch classes, different weights → different best key."""
    a_minor_weighted = _weights({9: 4.0, 0: 2.0, 4: 2.0, 2: 1.0, 5: 1.0, 7: 1.0, 11: 1.0})
    assert (infer_key(C_MAJOR_WEIGHTED).best.tonic_pc, infer_key(C_MAJOR_WEIGHTED).best.mode) == (0, "major")
    result = infer_key(a_minor_weighted)
    assert (result.best.tonic_pc, result.best.mode) == (9, "minor")


def test_result_shape():
    result = infer_key(C_MAJOR_WEIGHTED)
    assert len(result.candidates) == 24  # 12 tonics x {major, minor}
    scores = [c.score for c in result.candidates]
    assert scores == sorted(scores, reverse=True)
    assert result.margin == pytest.approx(scores[0] - scores[1])
    assert result.profile_version == "kk-1982.1"
    assert result.pc_weights == C_MAJOR_WEIGHTED
    json.dumps(result.to_dict())  # JSON-serializable evidence


# --- degenerate input: error, don't guess ---------------------------------------

@pytest.mark.parametrize(
    "bad",
    [
        [0.0] * 12,                 # silence
        [1.0] * 12,                 # perfectly uniform — no tonal information
        [1.0] * 11,                 # wrong length
        _weights({0: 1.0, 4: -1.0}),  # negative weight
    ],
)
def test_uninformative_or_invalid_input_raises(bad):
    with pytest.raises(ValueError):
        infer_key(bad)


# --- versioned priors ------------------------------------------------------------

def test_profiles_are_versioned():
    default = load_key_profiles()
    assert default.version == "kk-1982.1"
    assert load_key_profiles("kk-1982.1") is default
    with pytest.raises(ValueError, match="Unknown key-profile version"):
        load_key_profiles("no-such-version")


# --- temporal integration ---------------------------------------------------------

def _c_major_sequence() -> Sequence:
    notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C major scale up, C doubled
    events = [
        Event(onset=float(i), duration=2.0 if midi % 12 == 0 else 1.0, pitch=Pitch.from_midi(midi))
        for i, midi in enumerate(notes)
    ]
    return Sequence.from_events(events)


def test_sequence_pc_weights_accumulate_doublings():
    weights = _c_major_sequence().pc_weights()
    assert weights[0] == pytest.approx(4.0)  # C4 + C5, 2 beats each
    assert weights[2] == pytest.approx(1.0)
    assert weights[1] == 0.0


def test_infer_key_accepts_sequence_directly():
    sequence = _c_major_sequence()
    via_sequence = infer_key(sequence)
    via_weights = infer_key(list(sequence.pc_weights()))
    assert via_sequence.candidates == via_weights.candidates
    assert (via_sequence.best.tonic_pc, via_sequence.best.mode) == (0, "major")


def test_empty_sequence_has_no_tonal_information():
    silent = Sequence.from_events([])
    with pytest.raises(ValueError, match="no tonal information"):
        infer_key(silent)


# --- AnalyticalContext production --------------------------------------------------

def test_candidate_context_realizes_the_reading():
    context = candidate_context(KeyCandidate(tonic_pc=0, mode="major", score=0.9))
    assert isinstance(context, AnalyticalContext)
    assert context.tonic_pc == 0
    assert context.key.name == "Ionian"
    assert context.in_key(4) is True   # E is diatonic to C major
    assert context.in_key(1) is False  # C# is not

    minor = candidate_context(KeyCandidate(tonic_pc=9, mode="minor", score=0.9))
    # "Natural Minor" is a catalog alias; the canonical scale is Aeolian.
    assert minor.key.name == "Aeolian"
    assert minor.in_key(0) is True     # C is diatonic to A minor


def test_candidate_context_unknown_mode_raises():
    with pytest.raises(ValueError, match="No catalog scale mapping"):
        candidate_context(KeyCandidate(tonic_pc=0, mode="dorian", score=0.5))
