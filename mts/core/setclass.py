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
