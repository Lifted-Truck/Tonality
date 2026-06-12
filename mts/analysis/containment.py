"""Catalog containment query: which catalog identities contain a pc set.

The reverse of compatibility ("which chords fit inside this scale"): given a
pc set, find every catalog scale and chord quality that contains it, and at
which roots. Pure identity-level search — exact subset combinatorics over the
12-bit mask space; no realization, no key, no ranking policy. Symmetric
containers (whole tone, diminished) legitimately match at several roots —
all are reported; consumers can collapse them via the identity's symmetry
order if they wish.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from ..core.bitmask import mask_from_pcs, pcs_from_mask, rotate_mask
from ..core.quality import ChordQuality
from ..core.scale import Scale
from .pcset_math import containing_roots
from .results import CatalogContainer, CatalogContainment


def _containers(
    query_mask: int, entries: Iterable[Scale | ChordQuality]
) -> list[CatalogContainer]:
    containers: list[CatalogContainer] = []
    seen: set[str] = set()  # catalog mappings repeat entries under alias keys
    for entry in entries:
        if entry.name in seen:
            continue
        seen.add(entry.name)
        for root in containing_roots(entry.mask, query_mask):
            rooted_mask = rotate_mask(entry.mask, root)
            containers.append(
                CatalogContainer(
                    name=entry.name,
                    root_pc=root,
                    mask=rooted_mask,
                    cardinality=entry.mask.bit_count(),
                    is_exact=rooted_mask == query_mask,
                    aliases=list(entry.aliases),
                )
            )
    containers.sort(key=lambda c: (c.cardinality, c.name, c.root_pc))
    return containers


def find_containers(
    pcs: Iterable[int],
    *,
    catalog_scales: Mapping[str, Scale] | None = None,
    catalog_qualities: Mapping[str, ChordQuality] | None = None,
) -> CatalogContainment:
    """Every catalog scale and chord quality containing *pcs*, at which roots.

    Containers come back tightest-first (cardinality, name, root) with exact
    matches flagged. Pass explicit catalogs to search a ``SessionCatalog``'s
    view; defaults are the bundled catalogs.
    """

    query_mask = mask_from_pcs({int(pc) % 12 for pc in pcs})
    if query_mask == 0:
        raise ValueError("find_containers needs at least one pitch class.")
    if catalog_scales is None:
        from ..io.loaders import load_scales

        catalog_scales = load_scales()
    if catalog_qualities is None:
        from ..io.loaders import load_chord_qualities

        catalog_qualities = load_chord_qualities()
    return CatalogContainment(
        query_pcs=pcs_from_mask(query_mask),
        query_mask=query_mask,
        scales=_containers(query_mask, catalog_scales.values()),
        qualities=_containers(query_mask, catalog_qualities.values()),
    )
