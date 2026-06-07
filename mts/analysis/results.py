"""Typed result dataclasses for scale and chord analysis.

These replace the previous ``dict[str, object]`` returns from
``analyze_scale`` and ``analyze_chord``.  Attribute access gives calling
code (including future generative systems) static type information and
IDE autocomplete without any runtime cost.

``to_dict()`` on either top-level result class delegates to
``dataclasses.asdict()``, which recursively converts nested dataclasses to
plain dicts so that ``json.dumps(result.to_dict())`` still works for
scripts that need JSON output.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Shared sub-types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReflectionAxis:
    """A single reflective symmetry axis of a pitch-class set."""
    type: str    # "pitch" | "between"
    center: float  # integer or half-integer (e.g. 0, 5.5)


@dataclass(frozen=True)
class SymmetryData:
    """Rotational and reflective symmetry properties of a scale or chord."""
    rotational_order: int
    rotational_steps: list[int]
    achiral: bool
    reflection_axes: list[ReflectionAxis]


# ---------------------------------------------------------------------------
# Scale-specific sub-types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ModeRotation:
    """One modal rotation of a parent scale."""
    mode_index: int
    root_pc: int
    degrees: list[int]
    mask: int
    step_pattern: list[int]
    interval_vector: list[int]


@dataclass(frozen=True)
class ScaleIntervalSummary:
    """Interval statistics for a scale."""
    cardinality: int
    interval_vector: list[int]
    largest_step: int | None
    smallest_step: int | None
    semitone_count: int
    tone_count: int
    tritone_pairs: int
    ic_map: dict[str, int]


# ---------------------------------------------------------------------------
# Chord-specific sub-types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ChordIntervalSummary:
    """Interval statistics for a chord."""
    cardinality: int
    distinct_pcs: int
    interval_vector: list[int]
    smallest_interval: int | None
    largest_interval: int | None
    span_semitones: int
    span_compact: int
    interval_pairs: list[int]


@dataclass(frozen=True)
class Inversion:
    """One inversion of a chord (root rotated to each chord tone).

    ``position_index`` is the inversion number (0 = root position). ``figured_bass``
    is the conventional shorthand for triads and seventh chords (e.g. ``6``,
    ``6/4``, ``6/5``); ``None`` for cardinalities without a standard figure.
    """
    root_pc: int
    intervals: list[int]
    position_index: int = 0
    position_name: str = "root position"
    figured_bass: str | None = None


@dataclass(frozen=True)
class VoicingEntry:
    """A single **generated** chord voicing (closed, drop-2, drop-3, etc.).

    Produced by ``suggest_voicings`` — a *generative* helper that invents
    register from a pitch-class identity. This is a suggestion, not analysis;
    real register-bearing input is described by :class:`VoicingAnalysis`.
    """
    label: str
    semitones_from_root: list[int]
    intervals_mod_12: list[int]
    spread: int


@dataclass(frozen=True)
class VoicingSet:
    """An ordered collection of **generated** named voicings for a chord
    (output of ``suggest_voicings``).

    The vocabulary is open-ended (closed, drop-2/3, rootless, shell, …); only the
    voicings that *apply* to a given chord are present. Generative, not
    analytical — see :class:`VoicingEntry`. Look up a voicing by name with
    :meth:`get`.
    """
    entries: list[VoicingEntry]

    def get(self, label: str) -> VoicingEntry | None:
        """Return the entry with this label, or ``None`` if not present."""
        return next((entry for entry in self.entries if entry.label == label), None)

    @property
    def labels(self) -> list[str]:
        """The labels present, in order."""
        return [entry.label for entry in self.entries]


@dataclass(frozen=True)
class ChordInterpretation:
    """One valid way to name a pitch-class set as a rooted chord.

    A symmetric set (dim7, augmented) yields several interpretations at different
    roots; an ambiguous set yields several qualities (e.g. C6 = Am7).
    """
    root_pc: int
    quality: str
    aliases: list[str]


@dataclass(frozen=True)
class ChordInterpretations:
    """All structurally-valid (root, quality) namings of a pitch-class set.

    Identity-level and register-free: this enumerates how a *set* can be named,
    surfacing enharmonic/structural equivalence (every root at which the set
    matches a catalog quality). ``rotational_symmetry`` explains why symmetric
    chords repeat. Roots are restricted to tones present in the set.
    """
    pcs: list[int]
    mask: int
    cardinality: int
    rotational_symmetry: int
    interpretations: list[ChordInterpretation]

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class VoicingAnalysis:
    """Register-aware analysis of an actual realization (voicing or template).

    Requires register: produced only by ``analyze_voicing`` from a
    :class:`~mts.core.realization.Realization`. Every field is read from real
    pitches — nothing is invented. Contrast :class:`VoicingSet`, which
    *generates* plausible register from a register-less identity.
    """
    spec_level: str
    rooted: bool
    root_pc: int | None
    midi: list[int]
    bass_pc: int
    bass_midi: int
    intervals_from_bass: list[int]
    spread_semitones: int
    distinct_pcs: list[int]
    doublings: list[int]
    mask: int
    # Recognition (register-aware). ``openness`` is always set; the rest require a
    # known root (``None`` for rootless templates). ``voicing_type`` is ``None``
    # when the spacing matches no named vocabulary entry.
    openness: str = "closed"
    inversion_index: int | None = None
    position_name: str | None = None
    figured_bass: str | None = None
    voicing_type: str | None = None

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class TonicContext:
    """Analysis of a chord relative to a named tonic (numeric; spelling at edge)."""
    tonic_pc: int
    root_interval_from_tonic: int
    relative_pcs: list[int]  # chord tones as intervals above the tonic


@dataclass(frozen=True)
class TonnetzAnalysis:
    """Tonnetz coordinates for the pitches in a chord."""
    coordinates: dict[int, tuple[int, int, int]]
    centroid: tuple[float, float, float] | None


# ---------------------------------------------------------------------------
# Top-level result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScaleAnalysisResult:
    """Full analysis result for a scale.

    Optional fields are ``None`` when the corresponding ``include_*`` flag
    on the request was ``False``, or when the prerequisite data was absent
    (e.g. ``note_names`` requires ``tonic_pc`` to be set).
    """

    scale_name: str
    tonic_pc: int | None
    degrees: list[int]
    cardinality: int
    step_pattern: list[int]
    interval_vector: list[int]
    mask: int
    mask_binary: str
    modes: list[ModeRotation] | None = None
    symmetry: SymmetryData | None = None
    intervals: ScaleIntervalSummary | None = None

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class ChordAnalysisResult:
    """Full analysis result for a chord.

    Optional fields are ``None`` when the corresponding ``include_*`` flag
    on the request was ``False``, or when the prerequisite data was absent
    (e.g. ``tonic_context`` requires ``tonic_pc`` to be set).
    """

    root_pc: int
    quality: str
    pcs: list[int]
    mask: int
    cardinality: int
    intervals_relative_to_root: list[int]
    interval_matrix: list[list[int]]
    interval_class_histogram: dict[int, int]
    inverted_interval_matrix: list[list[int]]
    inverted_interval_class_histogram: dict[int, int]
    interval_vector: list[int]
    interval_summary: ChordIntervalSummary
    symmetry: SymmetryData
    tonnetz: TonnetzAnalysis
    tonic_context: TonicContext | None = None
    inversions: list[Inversion] | None = None

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


__all__ = [
    "ChordAnalysisResult",
    "ChordInterpretation",
    "ChordInterpretations",
    "ChordIntervalSummary",
    "Inversion",
    "ModeRotation",
    "ReflectionAxis",
    "ScaleAnalysisResult",
    "ScaleIntervalSummary",
    "SymmetryData",
    "TonnetzAnalysis",
    "TonicContext",
    "VoicingAnalysis",
    "VoicingEntry",
    "VoicingSet",
]
