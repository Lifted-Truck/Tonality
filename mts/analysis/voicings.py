"""Generative voicing suggestions — NOT analysis.

``suggest_voicings`` *invents* register from a register-less chord identity: it
stacks the chord's pitch classes into a plausible closed voicing and derives
drop-2 / drop-3 variants. This is a **generative** act (choosing a voicing),
deliberately kept out of the analysis path (ROADMAP "cardinal rule"). For
register-*aware* analysis of an actual realization, use
``analyze_voicing`` in :mod:`mts.analysis.chord_analysis`.

This code was relocated from ``chord_analysis.py`` during Phase 1, where
``analyze_chord`` used to fabricate these stacks and present them as analysis.
"""

from __future__ import annotations

from ..core.chord import Chord
from ..core.enharmonics import SpellingPref, name_for_pc
from .results import VoicingEntry, VoicingSet


def _normalize_register(values: list[int]) -> list[int]:
    """Stack intervals into a strictly-ascending register (invents octaves)."""

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


def suggest_voicings(
    chord: Chord,
    *,
    spelling: SpellingPref = "auto",
    key_signature: int | None = None,
) -> VoicingSet:
    """Generate suggested closed / drop-2 / drop-3 voicings for a chord.

    Generative, not analytical: the register is *chosen*, not read from input.
    The result documents that via :class:`~mts.analysis.results.VoicingSet`.
    """

    pcs = list(chord.pcs)
    relative = sorted(((pc - chord.root_pc) % 12) for pc in pcs)
    closed_stack = _normalize_register(relative)

    def make_voicing(intervals: list[int], *, label: str) -> VoicingEntry:
        ordered = _normalize_register(intervals)
        modulo = [iv % 12 for iv in ordered]
        return VoicingEntry(
            label=label,
            semitones_from_root=ordered,
            intervals_mod_12=modulo,
            spread=(ordered[-1] - ordered[0]) if len(ordered) > 1 else 0,
            note_names=[
                name_for_pc((chord.root_pc + iv) % 12, prefer=spelling, key_signature=key_signature)
                for iv in ordered
            ],
        )

    closed = make_voicing(closed_stack, label="closed")
    drop2: VoicingEntry | None = None
    drop3: VoicingEntry | None = None

    if len(closed_stack) >= 3:
        d2 = closed_stack.copy()
        d2[-2] -= 12
        drop2 = make_voicing(d2, label="drop2")
    if len(closed_stack) >= 4:
        d3 = closed_stack.copy()
        d3[-3] -= 12
        drop3 = make_voicing(d3, label="drop3")

    return VoicingSet(closed=closed, drop2=drop2, drop3=drop3)


__all__ = ["suggest_voicings"]
