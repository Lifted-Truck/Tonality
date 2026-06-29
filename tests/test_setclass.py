"""Phase 3.5a: set-class identity, transformations, and DFT spectrum."""

import math

import pytest

from mts.analysis import ChordAnalysisRequest, ScaleAnalysisRequest, analyze_chord, analyze_scale
from mts.analysis.pcset_math import set_class_data
from mts.core.bitmask import (
    complement_mask,
    invert_mask,
    mask_from_pcs,
    multiply_mask,
    pcs_from_mask,
    rotate_mask,
    interval_vector_from_mask,
)
from mts.core.chord import Chord
from mts.core.quality import ChordQuality
from mts.core.scale import Scale
from mts.core.setclass import (
    dft_magnitudes,
    normal_order,
    prime_form,
    prime_form_mask,
    z_partner_mask,
)

MAJOR_TRIAD = mask_from_pcs([0, 4, 7])
MINOR_TRIAD = mask_from_pcs([0, 3, 7])
DOM7 = mask_from_pcs([0, 4, 7, 10])
HALF_DIM = mask_from_pcs([0, 3, 6, 10])
DIM7 = mask_from_pcs([0, 3, 6, 9])
MAJOR_SCALE = mask_from_pcs([0, 2, 4, 5, 7, 9, 11])
WHOLE_TONE = mask_from_pcs([0, 2, 4, 6, 8, 10])
CHROMATIC = 0xFFF


# --- transformations --------------------------------------------------------

def test_invert_mask_about_zero():
    assert invert_mask(MAJOR_TRIAD) == mask_from_pcs([0, 8, 5])


def test_invert_mask_is_involution():
    for mask in (MAJOR_TRIAD, DOM7, MAJOR_SCALE, 0, CHROMATIC):
        assert invert_mask(invert_mask(mask, 3), 3) == mask


def test_complement_mask():
    assert complement_mask(0) == CHROMATIC
    assert complement_mask(MAJOR_SCALE) == mask_from_pcs([1, 3, 6, 8, 10])


def test_multiply_m5_sends_diatonic_to_chromatic_cluster():
    cluster = mask_from_pcs([0, 1, 7, 8, 9, 10, 11])
    assert multiply_mask(MAJOR_SCALE, 5) == cluster
    # M5 and M7 are mutually inverse bijections (5*7 = 35 ≡ 11... actually
    # M5∘M5 = M25 = M1), so M5 twice is the identity.
    assert multiply_mask(multiply_mask(MAJOR_SCALE, 5), 5) == MAJOR_SCALE


# --- normal order / prime form ----------------------------------------------

def test_normal_order_known_values():
    assert normal_order(MAJOR_TRIAD) == (0, 4, 7)
    assert normal_order(mask_from_pcs([0, 3, 8])) == (8, 0, 3)  # Ab major triad
    assert normal_order(0) == ()


def test_prime_form_known_values():
    # Major and minor triads are inversions: one set class, 3-11 (0,3,7).
    assert prime_form(MAJOR_TRIAD) == (0, 3, 7)
    assert prime_form(MINOR_TRIAD) == (0, 3, 7)
    # Dominant 7th and half-diminished are inversions: 4-27 (0,2,5,8).
    assert prime_form(DOM7) == (0, 2, 5, 8)
    assert prime_form(HALF_DIM) == (0, 2, 5, 8)
    # Diatonic collection: 7-35 (0,1,3,5,6,8,10).
    assert prime_form(MAJOR_SCALE) == (0, 1, 3, 5, 6, 8, 10)
    # Transpositionally symmetric sets are their own canonical forms.
    assert prime_form(WHOLE_TONE) == (0, 2, 4, 6, 8, 10)
    assert prime_form(DIM7) == (0, 3, 6, 9)
    assert prime_form(CHROMATIC) == tuple(range(12))
    assert prime_form(0) == ()
    assert prime_form(mask_from_pcs([5])) == (0,)


def test_prime_form_invariant_under_all_transformations_exhaustive():
    """T_n/I-invariance, idempotence, and zero-rooting over all 4096 masks."""
    for mask in range(4096):
        prime = prime_form_mask(mask)
        # Idempotent: the prime form is its own prime form.
        assert prime_form_mask(prime) == prime
        # Invariant under every transposition and under inversion.
        assert prime_form_mask(invert_mask(mask)) == prime
        for n in range(12):
            assert prime_form_mask(rotate_mask(mask, n)) == prime
        # Nonempty prime forms are zero-rooted with the same cardinality.
        if mask:
            assert prime & 1
            assert len(pcs_from_mask(prime)) == len(pcs_from_mask(mask))


def test_prime_form_preserves_interval_vector():
    for mask in (MAJOR_TRIAD, DOM7, MAJOR_SCALE, DIM7):
        assert interval_vector_from_mask(prime_form_mask(mask)) == interval_vector_from_mask(mask)


# --- Z-relation --------------------------------------------------------------

def test_z_relation_known_pair():
    # 4-Z15 (0,1,4,6) and 4-Z29 (0,1,3,7): the all-interval tetrachords,
    # interval vector <111111>.
    z15 = mask_from_pcs([0, 1, 4, 6])
    z29 = mask_from_pcs([0, 1, 3, 7])
    assert interval_vector_from_mask(z15) == (1, 1, 1, 1, 1, 1)
    assert z_partner_mask(z15) == prime_form_mask(z29)
    assert z_partner_mask(z29) == prime_form_mask(z15)


def test_z_partner_none_for_unrelated():
    assert z_partner_mask(MAJOR_TRIAD) is None
    assert z_partner_mask(0) is None
    assert z_partner_mask(CHROMATIC) is None


def test_z_partnership_is_symmetric_and_pairwise():
    """Every Z-partner points back; no set is its own partner (whole space)."""
    for mask in range(4096):
        partner = z_partner_mask(mask)
        if partner is not None:
            assert partner != prime_form_mask(mask)
            assert z_partner_mask(partner) == prime_form_mask(mask)


# --- DFT ----------------------------------------------------------------------

def test_dft_chromatic_is_flat():
    assert dft_magnitudes(CHROMATIC) == pytest.approx((0.0,) * 6, abs=1e-9)


def test_dft_whole_tone_concentrates_in_f6():
    mags = dft_magnitudes(WHOLE_TONE)
    assert mags[:5] == pytest.approx((0.0,) * 5, abs=1e-9)
    assert mags[5] == pytest.approx(6.0)


def test_dft_diatonic_f5_is_maximal_fifthiness():
    # |f5| of the diatonic set is 2 + sqrt(3) (the 7-element Dirichlet peak).
    assert dft_magnitudes(MAJOR_SCALE)[4] == pytest.approx(2 + math.sqrt(3))


def test_documented_evenness_recipe():
    """INTEGRATION.md recipe: evenness = dft_magnitudes[n-1] / n, with anchors."""
    def evenness(pcs):
        return dft_magnitudes(mask_from_pcs(pcs))[len(pcs) - 1] / len(pcs)

    assert evenness([0, 4, 8]) == pytest.approx(1.0)            # augmented
    assert evenness([0, 3, 6, 9]) == pytest.approx(1.0)         # dim7
    assert evenness([0, 2, 4, 6, 8, 10]) == pytest.approx(1.0)  # whole tone
    assert evenness([0, 4, 7]) == pytest.approx(0.7454, abs=1e-4)
    assert evenness([0, 4, 7, 10]) == pytest.approx(0.6614, abs=1e-4)
    assert evenness([0, 1, 2, 3]) == pytest.approx(0.25)        # cluster


def test_dft_magnitudes_invariant_under_tn_and_inversion():
    for mask in (MAJOR_TRIAD, DOM7, MAJOR_SCALE, mask_from_pcs([0, 1, 4, 6])):
        base = dft_magnitudes(mask)
        assert dft_magnitudes(invert_mask(mask)) == pytest.approx(base)
        for n in range(12):
            assert dft_magnitudes(rotate_mask(mask, n)) == pytest.approx(base)


# --- analysis integration ------------------------------------------------------

def _c_major_chord() -> Chord:
    quality = ChordQuality.from_intervals("maj", [0, 4, 7])
    return Chord.from_quality(0, quality)


def test_analyze_chord_includes_set_class():
    result = analyze_chord(ChordAnalysisRequest(chord=_c_major_chord()))
    assert result.set_class is not None
    assert result.set_class.prime_form == [0, 3, 7]
    assert result.set_class.prime_form_mask == mask_from_pcs([0, 3, 7])
    assert result.set_class.normal_order == [0, 4, 7]
    assert result.set_class.z_partner_prime_form is None
    assert len(result.set_class.dft_magnitudes) == 6


def test_analyze_chord_set_class_flag_off():
    request = ChordAnalysisRequest(chord=_c_major_chord(), include_set_class=False)
    assert analyze_chord(request).set_class is None


def test_analyze_scale_includes_set_class_and_serializes():
    scale = Scale.from_degrees("Major", [0, 2, 4, 5, 7, 9, 11])
    result = analyze_scale(ScaleAnalysisRequest(scale=scale))
    assert result.set_class is not None
    assert result.set_class.prime_form == [0, 1, 3, 5, 6, 8, 10]
    payload = result.to_dict()
    assert payload["set_class"]["prime_form_mask"] == prime_form_mask(MAJOR_SCALE)
    import json

    json.dumps(payload)  # must remain JSON-serializable


def test_set_class_data_lists_are_unshared():
    a = set_class_data(MAJOR_TRIAD)
    b = set_class_data(MAJOR_TRIAD)
    assert a.prime_form == b.prime_form
    assert a.prime_form is not b.prime_form


# --- DFT phase + trichord chirality (Audiology brief-15) -------------------------

def test_dft_phases_match_component_args():
    from mts.core.setclass import dft_components, dft_phases
    import cmath
    mask = mask_from_pcs({0, 4, 7})
    comps = dft_components(mask)
    assert dft_phases(mask) == pytest.approx([cmath.phase(comps[k]) for k in range(1, 7)])


def test_dft_phases_rotate_under_transposition_and_negate_under_inversion():
    from mts.core.setclass import dft_phases
    import math
    maj = mask_from_pcs({0, 4, 7})
    # T+2: arg(f_k) shifts by -2*pi*k*n/12 (n=2). Check f3.
    maj_T2 = mask_from_pcs({2, 6, 9})
    expected = (dft_phases(maj)[2] - 2 * math.pi * 3 * 2 / 12) % (2 * math.pi)
    assert dft_phases(maj_T2)[2] % (2 * math.pi) == pytest.approx(expected)
    # inversion about 0 ({0,4,7} -> {0,8,5}) negates every phase.
    inv = mask_from_pcs({0, (-4) % 12, (-7) % 12})
    for a, b in zip(dft_phases(inv), dft_phases(maj)):
        assert a == pytest.approx(-b)


def test_augmented_is_a_pure_3cycle_and_achiral():
    from mts.core.setclass import dft_magnitudes
    from mts.analysis.pcset_math import trichord_chirality
    mask = mask_from_pcs({0, 4, 8})
    mags = dft_magnitudes(mask)
    assert mags[2] == pytest.approx(3.0) and mags[5] == pytest.approx(3.0)
    assert all(mags[k] == pytest.approx(0.0) for k in (0, 1, 3, 4))
    assert trichord_chirality(mask) == 0  # inversionally symmetric


def test_trichord_chirality_separates_major_from_minor():
    from mts.core.setclass import dft_magnitudes
    from mts.analysis.pcset_math import trichord_chirality
    maj, minor = mask_from_pcs({0, 4, 7}), mask_from_pcs({0, 3, 7})
    # magnitudes can't tell them apart (the whole point) ...
    assert dft_magnitudes(maj) == pytest.approx(dft_magnitudes(minor))
    # ... but chirality does: major -2, minor +2 (inversion-odd).
    assert trichord_chirality(maj) == -2
    assert trichord_chirality(minor) == 2
    # transposition-invariant: any major triad reads -2.
    assert trichord_chirality(mask_from_pcs({2, 6, 9})) == -2


def test_trichord_chirality_none_for_non_trichords():
    from mts.analysis.pcset_math import trichord_chirality
    assert trichord_chirality(mask_from_pcs({0, 4})) is None          # dyad
    assert trichord_chirality(mask_from_pcs({0, 4, 7, 10})) is None   # dom7 tetrachord
    assert trichord_chirality(mask_from_pcs({0, 3, 6, 10})) is None   # m7b5 (its mirror)


def test_general_chirality_separates_what_the_trichord_scalar_cannot():
    # Audiology brief-15: Im(f1*f2*conj(f3)) — bispectrum-slice handedness for ANY
    # cardinality, the n-note generalization of trichord_chirality.
    from mts.core.setclass import general_chirality
    maj, minor = mask_from_pcs({0, 4, 7}), mask_from_pcs({0, 3, 7})
    # sign agrees with the trichord convention on triads (major < 0 < minor) ...
    assert general_chirality(maj) < 0 < general_chirality(minor)
    # ... transposition-invariant (unlike phase) ...
    assert general_chirality(mask_from_pcs({2, 6, 9})) == general_chirality(maj)
    # ... 0 for every inversionally-symmetric set ...
    for achiral in ({0, 4, 8}, {0, 3, 6, 9}, {0, 2, 4, 6, 8, 10}, {0, 1, 2}):
        assert general_chirality(mask_from_pcs(achiral)) == 0.0
    # ... and it separates the dom7 / m7b5 mirror pair (trichord_chirality is None
    # for both — they are tetrachords), with opposite signs.
    dom7, m7b5 = mask_from_pcs({0, 4, 7, 10}), mask_from_pcs({0, 3, 6, 10})
    assert general_chirality(dom7) == pytest.approx(-general_chirality(m7b5))
    assert general_chirality(dom7) != 0.0
