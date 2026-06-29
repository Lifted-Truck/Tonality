"""Set-class identity: normal order, prime form (Rahn), Z-relations, DFT spectrum.

Everything here is a pure function of the 12-bit identity mask, cached over the
4096-mask space. Prime form follows **Rahn's** convention (the modern standard,
also used by music21); Forte's convention differs for a handful of set classes.
Forte *names* are deliberately not provided yet — deriving ordinals
algorithmically would mislabel exactly those discrepancy sets, so they wait for
a vetted reference table (see ROADMAP Phase 3.5a). The prime form itself is the
unambiguous set-class name.

Implementation note: for zero-rooted sorted pc tuples, Rahn's comparison
(minimize the largest interval from the bottom, then the next-largest, ...)
is exactly lexicographic comparison of ``(a_n, a_{n-1}, ..., a_1)``, which is
exactly integer comparison of the masks. So the prime form is simply the
minimum mask over the 24 zero-rooted images (12 rotations of the set, 12 of
its inversion) — verified against the standard known forms in the test suite.
"""

from __future__ import annotations

import cmath
import math
from functools import lru_cache

from .bitmask import invert_mask, pcs_from_mask, rotate_mask

_FULL_MASK = 0xFFF


@lru_cache(maxsize=4096)
def normal_order(mask: int) -> tuple[int, ...]:
    """The set's actual pitch classes in Rahn normal order.

    Ties between equally compact rotations resolve to the lowest starting pc.
    """
    if mask == 0:
        return ()
    best = min(
        (rotate_mask(mask, -pc), pc) for pc in pcs_from_mask(mask)
    )
    relative, start = best
    return tuple((start + iv) % 12 for iv in pcs_from_mask(relative))


@lru_cache(maxsize=4096)
def prime_form_mask(mask: int) -> int:
    """The Rahn prime form as a mask — the canonical set-class identifier.

    Same integer convention as Ian Ring's scale numbers (bit *n* = pc *n*),
    so this value links directly to ianring.com/musictheory/scales/<n>.
    """
    if mask == 0:
        return 0
    candidates = []
    for image in (mask, invert_mask(mask)):
        for pc in pcs_from_mask(image):
            candidates.append(rotate_mask(image, -pc))
    return min(candidates)


def prime_form(mask: int) -> tuple[int, ...]:
    """The Rahn prime form as a zero-based pc tuple."""
    return tuple(pcs_from_mask(prime_form_mask(mask)))


@lru_cache(maxsize=4096)
def dft_components(mask: int) -> tuple[complex, ...]:
    """Fourier coefficients f_0..f_6 of the PC-set characteristic function.

    The magnitudes are T_n- and T_nI-invariant (a set-class fingerprint); the
    phases distinguish transposition/inversion and feed DFT-based key finding.
    """
    pcs = pcs_from_mask(mask)
    return tuple(
        sum(cmath.exp(-2j * cmath.pi * k * pc / 12) for pc in pcs)
        for k in range(7)
    )


@lru_cache(maxsize=4096)
def dft_magnitudes(mask: int) -> tuple[float, float, float, float, float, float]:
    """|f_1|..|f_6| — the interval-content spectrum.

    Interpretive shorthand: |f_5| tracks diatonicity/fifthiness, |f_6|
    whole-tone-ness, |f_4| octatonicity, |f_3| hexatonicity, |f_2|
    quartal-cluster balance, |f_1| chromatic clustering.
    """
    components = dft_components(mask)
    return tuple(abs(components[k]) for k in range(1, 7))


@lru_cache(maxsize=4096)
def dft_phases(mask: int) -> tuple[float, float, float, float, float, float]:
    """arg(f_1)..arg(f_6) in radians (−π, π] — the DFT phases.

    Unlike the magnitudes, phase is **not** a set-class invariant: it rotates
    under transposition (by −2πk·n/12 for f_k under T_n) and **negates** under
    inversion. That is exactly what makes it useful — it carries the
    absolute-position / handedness information the magnitudes discard (colour hue,
    major/minor chirality). Reported for the literal mask, not a canonical form.
    """
    components = dft_components(mask)
    return tuple(cmath.phase(components[k]) for k in range(1, 7))


@lru_cache(maxsize=4096)
def general_chirality(mask: int) -> float:
    """``Im(f_1 · f_2 · conj(f_3))`` — a bispectrum-slice handedness scalar
    (Audiology brief-15) defined for **any** cardinality.

    The bispectrum ``B(a,b) = f_a · f_b · conj(f_{a+b})`` is the canonical
    shift-invariant phase descriptor; ``Im(B)`` is transposition-invariant and
    **inversion-odd**. The full symmetric sum vanishes identically (each term
    cancels its conjugate partner), so this reports the single slice ``Im(B(1,2))``:
    ``0`` for every inversionally-symmetric set, opposite-signed for mirror pairs,
    **major < 0 / minor > 0** (agreeing with :func:`trichord_chirality`'s sign on
    triads), and — unlike the trichord step-gap product — it **separates dom7 from
    m7♭5**. It is *not* identical to the step-gap chirality (they diverge in sign on
    ~29% of trichords); both are valid, this is the n-note generalization. This is
    the **smooth** handedness scalar: it carries a magnitude but is a single slice,
    so it false-zeros on a few exotic chiral set classes. For a *complete*
    classification (zero **iff** achiral) use :func:`chirality_sign`. Near-zero dust
    is snapped to ``0.0`` so the achiral test is exact.
    """
    components = dft_components(mask)
    value = (components[1] * components[2] * components[3].conjugate()).imag
    return round(value, 10) + 0.0  # +0.0 normalizes -0.0 → 0.0


# Canonical inversion-odd slice family for chirality_sign, ORDERED. Each slice is a
# bispectrum coefficient B(a,b)=f_a·f_b·conj(f_{a+b}) whose Im part is transposition-
# invariant and inversion-odd. ``(1, 2)`` is first so the sign agrees with
# ``general_chirality`` (= Im B(1,2)) wherever that is nonzero; the rest are the one
# representative of each ±mirror pair (a,b)~(12−a,12−b), lexicographically. A single
# trispectrum term f_1³·conj(f_3) is the final fallback — it is the *only* invariant
# needed beyond the bispectrum, covering the lone bispectrum-blind chiral hexachord
# [0,1,3,4,5,8] (which has f_2 = f_4 = 0). Verified complete over all 4096 masks.
def _chirality_slices() -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for a in range(1, 12):
        for b in range(a, 12):
            mirror = (min((12 - a) % 12, (12 - b) % 12), max((12 - a) % 12, (12 - b) % 12))
            if (a, b) <= mirror:
                pairs.append((a, b))
    pairs.sort(key=lambda ab: (ab != (1, 2), ab))  # (1,2) first, then lexicographic
    return pairs


_CHIRALITY_SLICES = tuple(_chirality_slices())
_CHIRALITY_EPS = 1e-7


@lru_cache(maxsize=4096)
def chirality_sign(mask: int) -> int:
    """Complete handedness of a pitch-class set: ``-1`` / ``0`` / ``+1`` —
    ``0`` **iff** the set is achiral (inversionally symmetric), ``−1`` for the
    major-triad handedness and ``+1`` for its mirror.

    The *complete signed chirality* posed as the open problem in Audiology brief-15.
    :func:`general_chirality` (one bispectrum slice) carries a magnitude but
    false-zeros on a few exotic chiral classes; this is its complete, sign-only
    companion. Construction: take the sign of the first nonzero member, in a fixed
    canonical order, of the inversion-odd slice family (:data:`_CHIRALITY_SLICES`
    bispectrum slices + the ``f_1³·conj(f_3)`` trispectrum fallback). Every slice is
    transposition-invariant and inversion-odd, so the result is transposition-
    invariant, flips sign under inversion, and — verified exhaustively over all 4096
    masks — is nonzero for **every** chiral set class (the trispectrum term supplies
    the lone hexachord the bispectrum cannot see) and zero for every achiral one.
    ``(1, 2)`` leads the order so the sign agrees with ``general_chirality`` wherever
    that is nonzero. Major = ``−1`` by convention (matching the chirality scalars).
    """

    comp = dft_components(mask)  # f0..f6
    f = list(comp) + [comp[12 - k].conjugate() for k in range(7, 12)]  # f7..f11
    for a, b in _CHIRALITY_SLICES:
        value = (f[a] * f[b] * f[(a + b) % 12].conjugate()).imag
        if abs(value) > _CHIRALITY_EPS:
            return -1 if value < 0 else 1
    value = (f[1] ** 3 * f[3].conjugate()).imag  # trispectrum fallback (lone hexachord)
    if abs(value) > _CHIRALITY_EPS:
        return -1 if value < 0 else 1
    return 0


# Reflection-residual minimizer geometry (Audiology brief-16). R(θ) is π-periodic
# (its highest harmonic is e^{2i·6θ}); a 360-point bracket resolves every basin
# (>50 samples per period), then golden-section refines to convergence so the value
# is the true minimum — reproducible by any correct minimizer (C++-port parity).
_REFLECTION_GRID = 360
_GOLDEN_RATIO = (5 ** 0.5 - 1) / 2


@lru_cache(maxsize=4096)
def reflection_residual(mask: int) -> float:
    """Best-fit reflection-axis asymmetry ``R = min_θ Σ_{k=1..6} |f_k|²·sin²(φ_k+kθ)``
    (Audiology brief-16) — ``0`` **iff** the set is achiral.

    A set is achiral iff some reflection axis makes every ``f_k`` real, so this
    residual (the squared asymmetry under the best-fit axis) vanishes exactly for
    achiral sets and is bounded away from 0 for chiral ones (min ≈ 1.35 over all
    chiral set classes — a wide clean gap). It uses only the already-exposed DFT
    magnitudes + phases (``f1..f6``); it is :func:`chirality`'s squared magnitude.
    Closed form: ``R(θ) = ½Σ|f_k|² − ½·Re[Σ_{k=1..6} f_k²·e^{2ikθ}]``, minimized by a
    grid bracket + golden-section refine.
    """

    comp = dft_components(mask)
    squares = [comp[k] ** 2 for k in range(7)]  # f_k² = |f_k|²·e^{2iφ_k}
    const = sum(abs(comp[k]) ** 2 for k in range(1, 7)) / 2.0

    def residual(theta: float) -> float:
        spectrum = sum((squares[k] * cmath.exp(2j * k * theta)).real for k in range(1, 7))
        return const - 0.5 * spectrum

    step = cmath.pi / _REFLECTION_GRID
    centre = min(range(_REFLECTION_GRID), key=lambda i: residual(i * step)) * step
    lo, hi = centre - step, centre + step
    c = hi - _GOLDEN_RATIO * (hi - lo)
    d = lo + _GOLDEN_RATIO * (hi - lo)
    for _ in range(60):
        if residual(c) < residual(d):
            hi, d = d, c
            c = hi - _GOLDEN_RATIO * (hi - lo)
        else:
            lo, c = c, d
            d = lo + _GOLDEN_RATIO * (hi - lo)
    return max(round(residual((lo + hi) / 2.0), 10), 0.0)


def chirality(mask: int) -> float:
    """Complete **signed, continuous** chirality (Audiology brief-16):
    ``chirality_sign · √R`` — sign from :func:`chirality_sign`, magnitude from
    :func:`reflection_residual`.

    The synthesis that closes brief-16: ``0`` **iff** achiral (no false zeros),
    transposition-invariant, inversion-odd (``χ(I·S) = −χ(S)``), with ``major < 0 <
    minor`` and ``dom7 = −m7♭5`` — and a genuine magnitude (unlike the ±1 sign), so
    sets are ordered by *how* chiral they are. ``|chirality|`` is ``√R``, A6's
    complete chirality magnitude. Verified against A6's acceptance harness.
    """

    sign = chirality_sign(mask)
    if sign == 0:  # achiral — exact zero from the algebraic sign, no float threshold
        return 0.0
    return round(sign * math.sqrt(reflection_residual(mask)), 10) + 0.0


@lru_cache(maxsize=1)
def _z_table() -> dict[int, int]:
    """Map each Z-related prime-form mask to its partner's prime-form mask.

    Built by one pass over the 4096-mask space; in 12-TET the Z-relation is
    strictly pairwise, so a plain partner map suffices.
    """
    from .bitmask import interval_vector_from_mask

    # Key by (cardinality, vector): the empty set and a singleton share the
    # all-zero vector but are not Z-related (vector sum n(n-1)/2 pins
    # cardinality for every other size).
    by_vector: dict[tuple[int, tuple[int, ...]], list[int]] = {}
    seen: set[int] = set()
    for mask in range(_FULL_MASK + 1):
        prime = prime_form_mask(mask)
        if prime in seen:
            continue
        seen.add(prime)
        cardinality = len(pcs_from_mask(prime))
        by_vector.setdefault((cardinality, interval_vector_from_mask(prime)), []).append(prime)
    table: dict[int, int] = {}
    for group in by_vector.values():
        if len(group) == 2:
            a, b = group
            table[a] = b
            table[b] = a
    return table


def z_partner_mask(mask: int) -> int | None:
    """Prime-form mask of the Z-partner (same interval vector, different
    set class), or None if the set class is not Z-related."""
    return _z_table().get(prime_form_mask(mask))
