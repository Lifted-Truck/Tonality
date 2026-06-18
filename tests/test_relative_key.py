"""Relative-major/minor tie-breaker (3.5a refinement).

An additive, evidenced refinement on top of `infer_key` (whose scores/margin are
a pinned stability contract — see `test_infer_key_unchanged`). Engages only on a
genuine relative near-tie; tonal-hierarchy signals (leading-tone, tonic-triad,
tonic salience) decide, and report honest ambiguity when inconclusive.
"""

from __future__ import annotations

import json

import pytest

from mts.analysis import disambiguate_relative_key, infer_key
from mts.io.loaders import load_key_profiles, load_relative_key_weights

# The relative-key tie-breaker prior (rel-key.1) was derived for the KK profile's
# correlation behaviour, and its fixtures are deliberate KK near-ties. Pin KK for
# the engagement tests so they test the tie-break logic, not the default profile
# (the default is now tkp-cbms.1, which resolves several relative near-ties at the
# profile level — so the tie-breaker simply fires less under it).
_KK = load_key_profiles("kk-1982.1")


def _w(pairs: dict[int, float]) -> list[float]:
    w = [0.0] * 12
    for pc, value in pairs.items():
        w[pc] = value
    return w


# Eb major guitar-solo shape (the Audiology brief-3 case): Eb-G-Bb triad heavy,
# scalar C/D, no B-natural. infer_key leans Eb major but only by a near-tie gap.
EB_MAJOR_SOLO = _w({3: 4, 7: 3, 10: 3, 0: 2, 2: 2, 5: 1, 8: 1})
# A near-tie that the raised 7th (G#) confirms as A minor.
A_MINOR_LEADING_TONE = _w({9: 2, 0: 2, 4: 2, 2: 1, 5: 1, 7: 1, 11: 1, 8: 1.2})
# Uniform diatonic content — genuinely ambiguous.
DIATONIC_UNIFORM = _w({pc: 1.0 for pc in (0, 2, 4, 5, 7, 9, 11)})
# Clearly C major: tonic+dominant weighted, relative partner far behind.
CLEAR_C_MAJOR = _w({0: 4, 2: 1, 4: 2, 5: 1, 7: 3, 9: 1, 11: 1})


# --- decisive tie-breaks ----------------------------------------------------------------


def test_engages_and_backs_the_major_reading():
    d = disambiguate_relative_key(infer_key(EB_MAJOR_SOLO, profiles=_KK))
    assert d.applied is True
    assert (d.chosen.tonic_pc, d.chosen.mode) == (3, "major")
    assert (d.relative.tonic_pc, d.relative.mode) == (0, "minor")
    assert d.is_ambiguous is False
    assert d.tiebreak_score < 0  # negative favors major
    # the tonic-triad signal carries it (Eb-G-Bb over C-Eb-G), not a coin flip
    triad = next(e for e in d.evidence if e.signal == "tonic_triad_salience")
    assert triad.value < 0


def test_leading_tone_confirms_minor():
    d = disambiguate_relative_key(A_MINOR_LEADING_TONE)
    assert d.applied is True
    assert (d.chosen.tonic_pc, d.chosen.mode) == (9, "minor")
    assert d.tiebreak_score > 0  # positive favors minor
    lt = next(e for e in d.evidence if e.signal == "leading_tone")
    assert lt.value > 0  # G# (raised 7th, outside the shared collection) is present


# --- honest ambiguity + passthrough -----------------------------------------------------


def test_uniform_diatonic_is_honestly_ambiguous():
    d = disambiguate_relative_key(DIATONIC_UNIFORM)
    assert d.applied is True            # the top pair IS a near-tie
    assert d.is_ambiguous is True       # but the signals don't decide
    assert d.tiebreak_score == pytest.approx(0.0, abs=1e-9)
    # chosen stays the correlation winner rather than a fabricated pick
    assert d.chosen is not None


def test_confident_call_passes_through_untouched():
    d = disambiguate_relative_key(CLEAR_C_MAJOR)
    assert d.applied is False
    assert d.chosen is None and d.relative is None
    assert d.evidence == []
    # the full induction is still carried for the consumer
    assert (d.induction.best.tonic_pc, d.induction.best.mode) == (0, "major")


# --- the stability contract -------------------------------------------------------------


def test_infer_key_unchanged():
    """The refinement must not perturb infer_key (A5/A7 pin its scores/margin)."""
    for material in (EB_MAJOR_SOLO, A_MINOR_LEADING_TONE, CLEAR_C_MAJOR):
        result = infer_key(material)
        # disambiguation carries the *same* induction it was given, verbatim
        carried = disambiguate_relative_key(material).induction
        assert [(c.tonic_pc, c.mode, c.score) for c in carried.candidates] == [
            (c.tonic_pc, c.mode, c.score) for c in result.candidates
        ]
        assert carried.margin == result.margin
        assert carried.profile_version == "tkp-cbms.1"  # the default profile


# --- shape, versioning, determinism -----------------------------------------------------


def test_accepts_a_precomputed_induction():
    induction = infer_key(EB_MAJOR_SOLO, profiles=_KK)
    d = disambiguate_relative_key(induction)
    assert d.induction is induction
    assert (d.chosen.tonic_pc, d.chosen.mode) == (3, "major")


def test_result_shape_and_version():
    d = disambiguate_relative_key(infer_key(EB_MAJOR_SOLO, profiles=_KK))
    assert d.weights_version == load_relative_key_weights().version == "rel-key.1"
    assert {e.signal for e in d.evidence} == {
        "tonic_salience", "tonic_triad_salience", "leading_tone"
    }
    json.dumps(d.to_dict())  # JSON-serializable


def test_deterministic():
    a = disambiguate_relative_key(A_MINOR_LEADING_TONE).to_dict()
    b = disambiguate_relative_key(A_MINOR_LEADING_TONE).to_dict()
    assert a == b


def test_weights_are_versioned():
    assert load_relative_key_weights("rel-key.1").version == "rel-key.1"
    with pytest.raises(ValueError, match="Unknown relative-key version"):
        load_relative_key_weights("no-such-version")
