"""Structural / enharmonic equivalence: how a pitch-class set can be named.

``interpret_chord`` enumerates every structurally-valid ``(root, quality)`` naming
of a pitch-class set, by trying each present tone as a root and matching the
resulting chord-tone set against the catalog. This is **identity-level analysis**
(register-free) and surfaces equivalence that a single name hides:

- symmetric chords name at several roots — Cdim7 = E♭dim7 = G♭dim7 = Adim7;
  C+ = E+ = A♭+ ;
- ambiguous sets name as different qualities — C6 = Am7 ;
- the augmented-sixth family surfaces via its enharmonic dominant interpretation
  (e.g. the German sixth in C is the A♭7 pitch-class set). Full *functional*
  augmented-sixth labelling (It/Fr/Ger + spelling) is a Phase 3 concern; here we
  expose the pitch-class equivalence it rests on.

Roots are restricted to tones present in the set (a chord's root is one of its
tones); rootless interpretations are out of scope. Naming uses canonical catalog
names with aliases attached.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from ..core.bitmask import interval_vector_from_mask, mask_from_pcs, rotate_mask
from ..core.quality import ChordQuality
from ..core.scale import Scale
from ..core.setclass import prime_form, prime_form_mask
from ..core.symmetry import rotational_period
from .results import (
    ChordInterpretation,
    ChordInterpretations,
    ScaleName,
    ScaleNames,
)
from ..io.loaders import chord_qualities_by_mask, load_scales


def interpret_chord(
    pcs: Iterable[int],
    *,
    catalog: Mapping[str, ChordQuality] | None = None,
) -> ChordInterpretations:
    """Enumerate every valid (root, quality) naming of a pitch-class set.

    Identity-level and register-free: returns numeric ``(root_pc, quality)``
    namings. Spell the roots at the display edge with
    ``mts.context.result_format.name_interpretations``.
    """

    pc_set = sorted({int(p) % 12 for p in pcs})
    if not pc_set:
        raise ValueError("interpret_chord needs at least one pitch class.")

    if catalog is None:
        # Default path (per-segment hot loop): the mask index is cached on the
        # catalog, so this rebuilds nothing (RE-5c).

        by_mask: Mapping[int, Sequence[ChordQuality]] = chord_qualities_by_mask()
    else:
        # Custom catalog: build the index inline (dedup aliases by name).
        built: dict[int, list[ChordQuality]] = {}
        seen_names: set[str] = set()
        for quality in catalog.values():
            if quality.name in seen_names:
                continue
            seen_names.add(quality.name)
            built.setdefault(quality.mask, []).append(quality)
        by_mask = built

    mask = mask_from_pcs(pc_set)
    interpretations: list[ChordInterpretation] = []
    for root in pc_set:
        relative_mask = rotate_mask(mask, -root)
        for quality in by_mask.get(relative_mask, ()):
            interpretations.append(
                ChordInterpretation(
                    root_pc=root,
                    quality=quality.name,
                    aliases=list(quality.aliases),
                )
            )

    interpretations.sort(key=lambda i: (i.root_pc, i.quality))
    return ChordInterpretations(
        pcs=pc_set,
        mask=mask,
        cardinality=len(pc_set),
        rotational_period=rotational_period(mask),
        interpretations=interpretations,
    )


def interpret_scale(
    pcs: Iterable[int],
    *,
    catalog: Mapping[str, Scale] | None = None,
) -> ScaleNames:
    """Enumerate every catalog-scale naming of a pitch-class set (brief-20 v1).

    The scale sibling of :func:`interpret_chord`: trying each present tone as the
    tonic, match the set against the scale catalog — so a modal-ambiguous set
    names at several roots (the diatonic set is Ionian, Dorian, … at different
    tonics). Identity-level and register-free; set-class identity (prime form) is
    the boundary, ``forte_number`` is ``None`` (deferred — prime form is the id),
    and names carry the catalog's ``aliases``. Spell roots at the display edge.
    """

    pc_set = sorted({int(p) % 12 for p in pcs})
    if not pc_set:
        raise ValueError("interpret_scale needs at least one pitch class.")

    if catalog is None:
        catalog = load_scales()
    # Mask index, deduped by canonical name (aliases never split a match).
    by_mask: dict[int, list[Scale]] = {}
    seen_names: set[str] = set()
    for scale in catalog.values():
        if scale.name in seen_names:
            continue
        seen_names.add(scale.name)
        by_mask.setdefault(scale.mask, []).append(scale)

    mask = mask_from_pcs(pc_set)
    names: list[ScaleName] = []
    for root in pc_set:
        relative_mask = rotate_mask(mask, -root)
        for scale in by_mask.get(relative_mask, ()):
            names.append(
                ScaleName(root_pc=root, name=scale.name, aliases=list(scale.aliases))
            )
    names.sort(key=lambda n: (n.root_pc, n.name))

    return ScaleNames(
        pcs=pc_set,
        mask=mask,
        cardinality=len(pc_set),
        prime_form=list(prime_form(mask)),
        prime_form_mask=prime_form_mask(mask),
        interval_vector=list(interval_vector_from_mask(mask)),
        forte_number=None,
        is_scale=bool(names),
        rotational_period=rotational_period(mask),
        names=names,
    )


__all__ = ["interpret_chord", "interpret_scale"]
