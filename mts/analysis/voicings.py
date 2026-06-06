"""Generative voicing suggestions — NOT analysis.

``suggest_voicings`` *invents* register from a register-less chord identity: it
stacks the chord's pitch classes and re-spaces them into a vocabulary of named
voicings (closed, drop-2/3, rootless, shell, …). This is a **generative** act
(choosing a voicing), deliberately kept out of the analysis path (ROADMAP
"cardinal rule"). The re-spacings are idiomatic heuristics, not the only correct
voicing — they are suggestions. For register-*aware* analysis of an actual
realization, use ``analyze_voicing`` in :mod:`mts.analysis.chord_analysis`.

Adding a voicing = add one entry to ``_VOICING_BUILDERS``. Each builder takes the
closed stack (ascending semitone offsets from the root) and returns a re-spaced
offset list, or ``None`` when the voicing does not apply to that chord.
"""

from __future__ import annotations

from typing import Callable

from ..core.chord import Chord
from ..core.enharmonics import SpellingPref, name_for_pc
from .results import VoicingEntry, VoicingSet

# A builder maps the closed stack -> a re-spaced offset list (or None if N/A).
VoicingBuilder = Callable[[list[int]], "list[int] | None"]


def _normalize_register(values: list[int]) -> list[int]:
    """Stack offsets into a strictly-ascending register (invents octaves)."""

    if not values:
        return []
    ordered = sorted(values)
    normalized = [ordered[0]]
    for val in ordered[1:]:
        nxt = val
        while nxt <= normalized[-1]:
            nxt += 12
        normalized.append(nxt)
    return normalized


def _has(stack: list[int], *mods: int) -> int | None:
    """Return the first offset whose pitch class is in ``mods``, else None."""

    return next((o for o in stack if o % 12 in mods), None)


# --- named voicing builders -------------------------------------------------
# Each receives the closed stack (ascending offsets) and returns re-spaced
# offsets or None. Final registration/ordering happens in suggest_voicings.

def _closed(stack: list[int]) -> list[int]:
    return list(stack)


def _drop(stack: list[int], *positions_from_top: int) -> list[int] | None:
    """Drop the given voices (counted from the top) down an octave."""

    if len(stack) <= max(positions_from_top):
        return None
    out = list(stack)
    for pos in positions_from_top:
        out[-pos] -= 12
    return out


def _spread(stack: list[int]) -> list[int] | None:
    """Open the voicing by lifting alternate inner voices up an octave."""

    if len(stack) < 3:
        return None
    return [o + 12 if i % 2 == 1 else o for i, o in enumerate(stack)]


def _rootless(stack: list[int], *, variant: str) -> list[int] | None:
    """Omit the root; idiomatic for 7th/extended chords (needs a 7th present)."""

    if len(stack) < 4 or _has(stack, 0) is None or _has(stack, 10, 11) is None:
        return None
    remaining = sorted(o for o in stack if o % 12 != 0)
    if variant == "a":
        return remaining
    # variant "b": lift the bottom voice an octave so the next tone sits on the bottom
    rotated = list(remaining)
    rotated[0] += 12
    return rotated


def _shell(stack: list[int]) -> list[int] | None:
    """Guide-tone shell: root + 3rd + 7th (needs both a 3rd and a 7th)."""

    third = _has(stack, 3, 4)
    seventh = _has(stack, 10, 11)
    if third is None or seventh is None:
        return None
    return [0, third, seventh]


_VOICING_BUILDERS: list[tuple[str, VoicingBuilder]] = [
    ("closed", _closed),
    ("drop2", lambda s: _drop(s, 2)),
    ("drop3", lambda s: _drop(s, 3)),
    ("drop2and3", lambda s: _drop(s, 2, 3)),
    ("drop2and4", lambda s: _drop(s, 2, 4)),
    ("spread", _spread),
    ("rootless-a", lambda s: _rootless(s, variant="a")),
    ("rootless-b", lambda s: _rootless(s, variant="b")),
    ("shell", _shell),
]


def voicing_shapes(closed_stack: list[int]) -> dict[str, tuple[int, ...]]:
    """Normalized offset *shapes* for each applicable named voicing.

    Each shape is the voicing's ascending offsets with the lowest note shifted to
    0 — a register-independent spacing fingerprint. This is the single source of
    truth shared by generation (``suggest_voicings``) and recognition
    (``analyze_voicing``): generation labels a chord *with* these shapes;
    recognition matches an actual realization's spacing *against* them. Builders
    are applied in registry order, so the first matching label is the canonical
    one.
    """

    closed = _normalize_register(closed_stack)
    shapes: dict[str, tuple[int, ...]] = {}
    for label, builder in _VOICING_BUILDERS:
        offsets = builder(closed)
        if offsets is None:
            continue
        ordered = _normalize_register(offsets)
        base = ordered[0]
        shapes[label] = tuple(o - base for o in ordered)
    return shapes


def suggest_voicings(
    chord: Chord,
    *,
    spelling: SpellingPref = "auto",
    key_signature: int | None = None,
) -> VoicingSet:
    """Generate a vocabulary of suggested voicings for a chord.

    Generative, not analytical: the register is *chosen*, not read from input.
    Only voicings that apply to the chord are returned, and exact duplicate
    spacings are collapsed (keeping the first / most-canonical label).
    """

    relative = sorted(((pc - chord.root_pc) % 12) for pc in chord.pcs)
    closed_stack = _normalize_register(relative)

    def make_voicing(offsets: list[int], *, label: str) -> VoicingEntry:
        ordered = _normalize_register(offsets)
        return VoicingEntry(
            label=label,
            semitones_from_root=ordered,
            intervals_mod_12=[o % 12 for o in ordered],
            spread=(ordered[-1] - ordered[0]) if len(ordered) > 1 else 0,
            note_names=[
                name_for_pc((chord.root_pc + o) % 12, prefer=spelling, key_signature=key_signature)
                for o in ordered
            ],
        )

    entries: list[VoicingEntry] = []
    seen: set[tuple[int, ...]] = set()
    for label, builder in _VOICING_BUILDERS:
        offsets = builder(closed_stack)
        if offsets is None:
            continue
        entry = make_voicing(offsets, label=label)
        fingerprint = tuple(entry.semitones_from_root)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        entries.append(entry)

    return VoicingSet(entries=entries)


__all__ = ["suggest_voicings", "voicing_shapes"]
