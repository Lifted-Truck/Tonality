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

from collections.abc import Iterable, Mapping

from ..core.bitmask import mask_from_pcs
from ..core.enharmonics import SpellingPref, name_for_pc
from ..core.quality import ChordQuality
from ..core.symmetry import mask_symmetry_order
from .results import ChordInterpretation, ChordInterpretations


def interpret_chord(
    pcs: Iterable[int],
    *,
    catalog: Mapping[str, ChordQuality] | None = None,
    spelling: SpellingPref = "auto",
    key_signature: int | None = None,
) -> ChordInterpretations:
    """Enumerate every valid (root, quality) naming of a pitch-class set."""

    pc_set = sorted({int(p) % 12 for p in pcs})
    if not pc_set:
        raise ValueError("interpret_chord needs at least one pitch class.")

    if catalog is None:
        from ..io.loaders import load_chord_qualities

        catalog = load_chord_qualities()

    # De-duplicate alias keys down to one quality per canonical name.
    qualities: dict[str, ChordQuality] = {}
    for quality in catalog.values():
        qualities.setdefault(quality.name, quality)

    mask = mask_from_pcs(pc_set)
    interpretations: list[ChordInterpretation] = []
    for root in pc_set:
        relative_mask = mask_from_pcs((pc - root) % 12 for pc in pc_set)
        for quality in qualities.values():
            if quality.mask == relative_mask:
                interpretations.append(
                    ChordInterpretation(
                        root_pc=root,
                        root_name=name_for_pc(root, prefer=spelling, key_signature=key_signature),
                        quality=quality.name,
                        aliases=list(quality.aliases),
                    )
                )

    interpretations.sort(key=lambda i: (i.root_pc, i.quality))
    return ChordInterpretations(
        pcs=pc_set,
        mask=mask,
        cardinality=len(pc_set),
        rotational_symmetry=mask_symmetry_order(mask),
        interpretations=interpretations,
    )


__all__ = ["interpret_chord"]
