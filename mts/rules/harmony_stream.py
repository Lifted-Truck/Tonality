"""The harmony atom stream (gap B): a named chord progression in a key, turned
into per-chord rule items carrying their move to the next chord.

The fourth ruleset family. Unlike voice-motion / melody / rhythm (which derive
their atoms from a raw note ``Sequence``), harmony atoms come from an **explicit
chord stream** — ``[(root_pc, quality), …]`` in a key — the same input form
``detect_cadences`` already takes. (Auto-deriving the chord stream from a
``Sequence`` via harmonic segmentation is the recorded slice-2 follow-on; slice
1 isolates the *vocabulary* from segmentation noise.)

Each item is a chord in context: its own function fields (roman / role / degree
/ quality / is_diatonic) plus the fields of its transition to the next chord
(root_motion / next_role / next_roman / common_tones / color_shift), so a single
item type supports both per-chord rules and adjacent-pair rules — exactly as a
``voice_motion`` item carries from/to. Transition fields are ``None`` on the last
chord (a line edge), so a rule referencing them there is simply not considered.

No new theory: roman/role come from ``theory/functions.py`` (major/minor only —
modal keys yield no roles, and the family reports unavailable rather than
guessing), cadence membership from ``detect_cadences``, colour shift from the
DFT magnitudes. The family only assembles a *rule vocabulary* over shipped
analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..core.setclass import dft_magnitudes
from ..io.loaders import load_chord_qualities, load_function_mappings

if TYPE_CHECKING:
    from ..session import SessionCatalog

_MODE_SCALE: dict[str, tuple[int, ...]] = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),  # natural minor
}


@dataclass(frozen=True)
class HarmonyItem:
    """One chord in a key, carrying its transition to the next (gap B item)."""

    roman: str | None
    role: str | None          # "tonic" | "predominant" | "dominant" | None
    degree: int | None        # 1..7 for a diatonic-rooted chord, else None
    quality: str
    is_diatonic: bool
    root_motion: int | None   # directed pc-interval to the next root (0..11); None at the end
    next_role: str | None
    next_roman: str | None
    common_tones: int | None  # shared pcs with the next chord; None at the end
    color_shift: float | None  # Σ|Δ DFT magnitude| to the next chord; None at the end
    cadence: str              # cadential formula arriving on this chord, or "none"


def _role_table(mode: str) -> dict[tuple[int, str], tuple[str, str]]:
    table: dict[tuple[int, str], tuple[str, str]] = {}
    for mapping in load_function_mappings(mode):
        table.setdefault((mapping.degree_pc, mapping.chord_quality),
                         (mapping.role, mapping.modal_label))
    return table


def _chord_pcs(root: int, quality: str, catalog) -> frozenset[int]:
    entry = catalog.get(quality)
    if entry is None:
        # Error, not guess (the cardinal rule): an unrecognized quality has no
        # known pitch content, so is_diatonic cannot be computed. Returning it
        # as False would be a definite *wrong* claim, not an absence — so raise,
        # matching every peer catalog consumer (succession/notation raise
        # ValueError on an unknown quality). A caller with custom qualities
        # passes a session (below) so they resolve instead of being typos.
        raise ValueError(
            f"Unknown chord quality {quality!r} — not in the catalog. "
            "Register it in the session (pass session=…) or fix the symbol; "
            "the harmony family errors rather than guess is_diatonic for an "
            "unrecognized quality."
        )
    return frozenset((root + iv) % 12 for iv in entry.intervals)


def build_harmony_stream(
    chords: list[tuple[int, str]], tonic_pc: int, mode: str,
    *, session: SessionCatalog | None = None,
) -> tuple[list[tuple[HarmonyItem, dict]], str | None]:
    """Build ``(item, location)`` pairs for a named progression in a key.

    Returns ``(items, None)`` on success, or ``([], reason)`` when the mode is
    unsupported (major/minor only) — the evaluator then reports harmony rules
    not-applicable, never guessed.

    ``session`` merges that session's registered chord qualities into the
    catalog (via :func:`load_chord_qualities`), so a user-defined quality
    resolves like a built-in one. **Raises** ``ValueError`` on a chord quality
    that resolves in neither the base catalog nor the session — a caller error
    (typo / unregistered symbol), distinct from the *soft* not-applicable an
    unsupported mode returns. This is the error-don't-guess rule: an unknown
    quality has no pitch content, so no ``is_diatonic`` claim can be made.
    """

    mode_key = str(mode).lower()
    scale = _MODE_SCALE.get(mode_key)
    if scale is None:
        return [], (
            f"harmony family supports major/minor only, got mode {mode!r} "
            "(theory/functions.py grounds no roles for other modes)"
        )
    if not chords:
        return [], "harmony family needs a non-empty chord stream"

    tonic = int(tonic_pc) % 12
    scale_pcs = frozenset((tonic + s) % 12 for s in scale)
    degree_of = {(tonic + s) % 12: i + 1 for i, s in enumerate(scale)}
    table = _role_table(mode_key)
    catalog = load_chord_qualities(session)

    # Cadence-arrival membership, reusing the shipped detector.
    from ..analysis.cadence import detect_cadences

    cad_result = detect_cadences(
        [(int(r) % 12, str(q)) for r, q in chords], tonic_pc=tonic, mode=mode_key
    )
    cadence_at: dict[int, str] = {}
    for event in cad_result.cadences:
        cadence_at.setdefault(event.arrival_index, event.type)

    pcs_list = [_chord_pcs(int(r) % 12, str(q), catalog) for r, q in chords]
    mags = [dft_magnitudes(_mask(p)) if p else None for p in pcs_list]

    items: list[tuple[HarmonyItem, dict]] = []
    for i, (root, quality) in enumerate(chords):
        rel = (int(root) % 12 - tonic) % 12
        role, roman = table.get((rel, str(quality)), (None, None))
        pcs = pcs_list[i]           # never None: an unknown quality raised above
        is_diatonic = pcs <= scale_pcs

        nxt = i + 1
        if nxt < len(chords):
            nrel = (int(chords[nxt][0]) % 12 - tonic) % 12
            nrole, nroman = table.get((nrel, str(chords[nxt][1])), (None, None))
            root_motion = (int(chords[nxt][0]) % 12 - int(root) % 12) % 12
            npcs = pcs_list[nxt]
            common = len(pcs & npcs)
            if mags[i] is not None and mags[nxt] is not None:
                color = round(sum(abs(a - b) for a, b in zip(mags[i], mags[nxt])), 10)
            else:
                color = None
        else:
            nrole = nroman = root_motion = common = color = None

        items.append((
            HarmonyItem(
                roman=roman, role=role, degree=degree_of.get(int(root) % 12),
                quality=str(quality), is_diatonic=is_diatonic,
                root_motion=root_motion, next_role=nrole, next_roman=nroman,
                common_tones=common, color_shift=color,
                cadence=cadence_at.get(i, "none"),
            ),
            {"chord_index": i},
        ))
    return items, None


def _mask(pcs: frozenset[int]) -> int:
    m = 0
    for p in pcs:
        m |= 1 << p
    return m


__all__ = ["HarmonyItem", "build_harmony_stream"]
