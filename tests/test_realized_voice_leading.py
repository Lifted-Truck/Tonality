"""Gap 6: register-aware voice-leading distance between voiced chords."""

import json
from itertools import permutations, product

import pytest

from mts.analysis import SpecificationError, voice_leading, voice_leading_realized
from mts.core.pitch import Pitch
from mts.core.realization import Realization
from mts.mcp.tools import realized_voice_leading


def _real(midis):
    return Realization(tuple(Pitch.from_midi(m) for m in midis), root_pc=None)


# --- the point of the metric: register matters --------------------------------------

def test_same_pcs_different_register_costs_more():
    """Identity-level says C->F is 3 regardless of octaves; this metric doesn't."""
    close = voice_leading_realized(_real([60, 64, 67]), _real([60, 65, 69]))
    assert close.distance == 3  # agrees with identity-level for compact voicings

    dropped = voice_leading_realized(_real([60, 64, 67]), _real([48, 65, 69]))
    assert dropped.distance == 15  # the bass leap is real motion now
    assert voice_leading([0, 4, 7], [0, 5, 9]).distance == 3  # identity unchanged


def test_octave_transposition_costs_twelve_per_voice():
    result = voice_leading_realized(_real([60, 64, 67]), _real([72, 76, 79]))
    assert result.distance == 36
    assert all(b - a == 12 for a, b in result.mapping)


def test_identity_is_zero():
    result = voice_leading_realized(_real([60, 64, 67]), _real([60, 64, 67]))
    assert result.distance == 0
    assert all(a == b for a, b in result.mapping)


# --- doublings and unequal voice counts ------------------------------------------------

def test_doublings_are_distinct_voices():
    # Doubled C: both copies must move somewhere.
    result = voice_leading_realized(_real([60, 60, 64, 67]), _real([59, 62, 65, 67]))
    sources = [a for a, _ in result.mapping]
    assert sources.count(60) == 2
    assert result.distance == 4  # 60->59 (1), 60->62 (2), 64->65 (1), 67->67 (0)


def test_triad_to_seventh_voicing():
    result = voice_leading_realized(_real([60, 64, 67]), _real([60, 64, 67, 70]))
    assert result.distance == 3  # 67 carries both 67 and 70
    targets = sorted(b for _, b in result.mapping)
    assert targets == [60, 64, 67, 70]


# --- result contract ----------------------------------------------------------------------

def test_result_shape_and_serialization():
    result = voice_leading_realized(_real([64, 60, 67]), _real([65, 60, 69]))
    assert result.policy == "doubling.1"
    assert result.source_midi == [60, 64, 67]  # sorted voices
    assert result.distance == sum(abs(a - b) for a, b in result.mapping)
    json.dumps(result.to_dict())


def test_register_is_required():
    with pytest.raises(SpecificationError):
        voice_leading_realized(None, _real([60, 64, 67]))


def test_unknown_policy_raises():
    with pytest.raises(ValueError, match="Unknown voice-leading policy"):
        voice_leading_realized(_real([60]), _real([62]), policy="omission.99")


# --- exactness: brute force ------------------------------------------------------------------

def _brute_bijection(source, target):
    return min(
        sum(abs(a - b) for a, b in zip(source, perm)) for perm in permutations(target)
    )


def _brute_surjection(larger, smaller):
    best = None
    for assignment in product(range(len(smaller)), repeat=len(larger)):
        if set(assignment) != set(range(len(smaller))):
            continue
        cost = sum(abs(note - smaller[i]) for note, i in zip(larger, assignment))
        best = cost if best is None or cost < best else best
    return best


def test_equal_voices_match_brute_force():
    cases = [
        ([60, 64, 67], [59, 62, 67]),
        ([48, 60, 64, 67, 72], [50, 57, 65, 69, 74]),   # 5 voices, S&C-shaped
        ([45, 57, 60, 64, 64], [47, 55, 62, 62, 67]),   # doublings both sides
        ([60, 61, 62], [70, 71, 72]),
    ]
    for a, b in cases:
        assert voice_leading_realized(_real(a), _real(b)).distance == _brute_bijection(a, b)


def test_unequal_voices_match_brute_force():
    cases = [
        ([60, 64, 67], [60, 64, 67, 70]),
        ([48, 55, 64, 67, 71], [50, 65, 69]),           # 5 -> 3
        ([60], [55, 62, 67, 74]),
        ([43, 47, 50, 55, 59], [45, 52, 57, 60, 64, 69, 72]),  # 5 -> 7, range-clamped style
    ]
    for a, b in cases:
        larger, smaller = (a, b) if len(a) >= len(b) else (b, a)
        expected = _brute_surjection(larger, smaller)
        assert voice_leading_realized(_real(a), _real(b)).distance == expected
        assert voice_leading_realized(_real(b), _real(a)).distance == expected


# --- MCP tool -----------------------------------------------------------------------------------

def test_mcp_tool():
    result = realized_voice_leading([60, 64, 67], [48, 65, 69])
    assert result["distance"] == 15
    json.dumps(result)
