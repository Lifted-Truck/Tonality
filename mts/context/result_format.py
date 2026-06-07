"""Edge formatters: turn numeric analysis results into spelled / labeled views.

This is the **display edge** of the analysis layer. The analysis functions produce
PC-level / numeric facts (pitch classes, semitone intervals, masks); these helpers
apply a :class:`DisplayContext` (spelling preference, key signature, tonal center,
label style) to render note names and interval labels for humans.

Direction of dependence: display depends on analysis, never the reverse — this
module imports `analysis.results`; nothing in `analysis/` imports this. It spells
from the *numeric* fields (``pcs``, ``root_pc``, ``intervals_relative_to_root``,
``degrees``, ``midi``), so it stays correct after Phase 3 Slice 1b removes the
spelled fields from the analysis results themselves.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from ..analysis.results import (
    ChordAnalysisResult,
    ChordInterpretation,
    ScaleAnalysisResult,
    VoicingAnalysis,
)
from ..core.enharmonics import PC_TO_NAMES
from .context import DisplayContext
from .formatters import _INTERVAL_LABELS, format_pitch_class


# ---------------------------------------------------------------------------
# Display views
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EnharmonicChoice:
    """Preferred spelling of a pitch class plus its alternates, per context."""
    pc: int
    preferred: str
    alternates: list[str]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class ChordAnalysisDisplay:
    """Spelled / labeled view of a :class:`ChordAnalysisResult`."""
    root_name: str
    note_names: list[str]
    interval_labels: list[str]
    enharmonics: list[EnharmonicChoice]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class ScaleAnalysisDisplay:
    """Spelled view of a :class:`ScaleAnalysisResult`."""
    note_names: list[str]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _label_style(context: DisplayContext) -> str:
    """Interval label style is a display choice; default to classical names."""
    return context.get("interval_label_style", "classical")


def interval_label(semitones: int, context: DisplayContext) -> str:
    """Label an interval (in semitones) per the context's style."""
    rel = semitones % 12
    if _label_style(context) == "classical":
        return _INTERVAL_LABELS.get(rel, f"ic{rel}")
    return str(rel)


def enharmonics_for(pcs: list[int], context: DisplayContext) -> list[EnharmonicChoice]:
    """Preferred + alternate spellings for each pitch class, per context."""
    choices: list[EnharmonicChoice] = []
    for pc in pcs:
        preferred = format_pitch_class(pc, context)
        alternates = [name for name in PC_TO_NAMES.get(pc % 12, []) if name != preferred]
        choices.append(EnharmonicChoice(pc=pc, preferred=preferred, alternates=alternates))
    return choices


# ---------------------------------------------------------------------------
# Result formatters
# ---------------------------------------------------------------------------

def format_chord_analysis(
    result: ChordAnalysisResult, context: DisplayContext
) -> ChordAnalysisDisplay:
    """Render a chord analysis: spelled root/notes, interval labels, enharmonics."""
    return ChordAnalysisDisplay(
        root_name=format_pitch_class(result.root_pc, context),
        note_names=[format_pitch_class(pc, context) for pc in result.pcs],
        interval_labels=[interval_label(iv, context) for iv in result.intervals_relative_to_root],
        enharmonics=enharmonics_for(list(result.pcs), context),
    )


def format_scale_analysis(
    result: ScaleAnalysisResult, context: DisplayContext
) -> ScaleAnalysisDisplay:
    """Render a scale analysis: spelled degree names."""
    return ScaleAnalysisDisplay(
        note_names=[format_pitch_class(pc, context) for pc in result.degrees],
    )


def name_interpretation(interp: ChordInterpretation, context: DisplayContext) -> str:
    """Spell one ``interpret_chord`` candidate as ``"<root> <quality>"``."""
    return f"{format_pitch_class(interp.root_pc, context)} {interp.quality}"


def name_interpretations(
    interpretations: list[ChordInterpretation], context: DisplayContext
) -> list[str]:
    """Spell every candidate naming of a set."""
    return [name_interpretation(i, context) for i in interpretations]


def spell_voicing(result: VoicingAnalysis, context: DisplayContext) -> list[str]:
    """Spell a voicing's pitches with octaves (e.g. ``["C3", "E3", "G3"]``)."""
    names: list[str] = []
    for midi in result.midi:
        pc = midi % 12
        octave = midi // 12 - 1  # MIDI octave convention (C4 == 60)
        names.append(f"{format_pitch_class(pc, context)}{octave}")
    return names


__all__ = [
    "EnharmonicChoice",
    "ChordAnalysisDisplay",
    "ScaleAnalysisDisplay",
    "interval_label",
    "enharmonics_for",
    "format_chord_analysis",
    "format_scale_analysis",
    "name_interpretation",
    "name_interpretations",
    "spell_voicing",
]
