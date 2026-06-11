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


@dataclass(frozen=True)
class SetClassData:
    """Set-class identity of a pitch-class set (Phase 3.5a).

    ``prime_form`` follows Rahn's convention; ``prime_form_mask`` is the
    canonical set-class id (same integer convention as Ian Ring's scale
    numbers). ``dft_magnitudes`` is |f1|..|f6| of the PC-set characteristic
    function — a transposition- and inversion-invariant fingerprint
    (|f5|≈diatonicity, |f6|≈whole-tone-ness, |f4|≈octatonicity).
    ``z_partner_prime_form`` is the prime form sharing this set's interval
    vector, when one exists.
    """

    normal_order: list[int]
    prime_form: list[int]
    prime_form_mask: int
    dft_magnitudes: list[float]
    z_partner_prime_form: list[int] | None
    complement_prime_form: list[int]


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


@dataclass(frozen=True)
class KeyCandidate:
    """One candidate key reading: a tonic, a mode, and its correlation score."""

    tonic_pc: int
    mode: str     # a mode name from the profile set, e.g. "major" | "minor"
    score: float  # Pearson correlation of input weights vs. the rotated profile


@dataclass(frozen=True)
class KeyInductionResult:
    """Ranked key candidates for a body of pitch material (Phase 3.5b).

    Per Decision 7 this is plural and evidenced: every candidate is present
    with its score, ``margin`` is the gap between the top two (small margins —
    canonically relative major/minor — mean "genuinely ambiguous, treat as
    such"), ``pc_weights`` is the exact input the ranking was computed from,
    and ``profile_version`` cites the versioned prior used.
    """

    candidates: list[KeyCandidate]  # all candidates, best first
    margin: float
    pc_weights: list[float]
    profile_version: str

    @property
    def best(self) -> KeyCandidate:
        return self.candidates[0]

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class VoiceLeadingResult:
    """Minimal voice leading between two pc-set identities (Phase 3.5).

    ``distance`` is the total motion in semitones under the optimal
    assignment; ``mapping`` is that assignment as ``[from_pc, to_pc]`` voice
    pairs (the evidence, and the seed generative consumers realize in
    register). ``policy`` names the cardinality convention used — the choice
    is a versioned prior, not a fact; cite it when comparing numbers.
    """

    distance: int
    mapping: list[list[int]]  # [from_pc, to_pc] per voice
    policy: str
    source_pcs: list[int]
    target_pcs: list[int]

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Context-sensitive naming (Phase 3 disambiguation slice)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AnalyticalContextSnapshot:
    """Frozen capture of the :class:`AnalyticalContext` used (numeric).

    Lives here (not in ``mts/dataset``) so naming results can label each
    reading with the context it is conditional on without an upward import;
    the dataset layer re-exports it.
    """

    tonic_pc: int | None = None
    key_name: str | None = None
    key_degrees: list[int] | None = None


@dataclass(frozen=True)
class NamingEvidence:
    """One scored signal behind a ranked interpretation (inspectable, per
    Decision 7). ``weight`` is the value applied from the versioned table."""

    signal: str
    weight: float
    detail: str | None = None


@dataclass(frozen=True)
class RankedInterpretation:
    """One candidate naming with its score and the evidence behind it."""

    interpretation: ChordInterpretation
    score: float
    rank: int
    functional_role: str | None = None    # "tonic" | "predominant" | "dominant"
    root_degree: int | None = None        # 0-based degree of the root in the key
    function_category: str | None = None  # special-function flag (aug6, V/x, ...)
    evidence: list[NamingEvidence] = dataclasses.field(default_factory=list)


@dataclass(frozen=True)
class ChordNaming:
    """The contextually-chosen reading of a pc set, with ranked alternatives.

    Per Decision 7: plural (every alternative kept, scored), explicit
    (``evidence`` per reading; ``weights_version`` cites the prior), and
    honest (``is_ambiguous`` flags near-ties instead of hiding them).
    ``context`` is the snapshot this naming is *conditional on* — ``None``
    means intrinsic-only ranking (no key was supplied; none was invented).
    ``chosen`` is ``None`` when the set matches nothing in the catalog.
    """

    chosen: RankedInterpretation | None
    alternatives: list[RankedInterpretation]
    is_ambiguous: bool
    context: AnalyticalContextSnapshot | None
    weights_version: str

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class NamingUnderKey:
    """One key candidate's conditional naming, with its marginalization weight."""

    candidate: KeyCandidate
    key_weight: float
    naming: ChordNaming


@dataclass(frozen=True)
class MultiKeyNaming:
    """Namings conditional on each ranked key candidate, plus a combined view.

    ``per_key`` keeps every reading conditional on its context (requirement
    of the recorded design); ``combined`` marginalizes scores over the key
    weights. Combined entries carry no functional_role / root_degree /
    function_category — those facts are key-conditional and live on the
    per-key readings.
    """

    per_key: list[NamingUnderKey]
    combined: list[RankedInterpretation]
    is_ambiguous: bool
    weights_version: str

    @property
    def chosen(self) -> RankedInterpretation | None:
        return self.combined[0] if self.combined else None

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


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
    set_class: SetClassData | None = None

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
    set_class: SetClassData | None = None

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


__all__ = [
    "AnalyticalContextSnapshot",
    "ChordAnalysisResult",
    "ChordInterpretation",
    "ChordNaming",
    "KeyCandidate",
    "KeyInductionResult",
    "MultiKeyNaming",
    "NamingEvidence",
    "NamingUnderKey",
    "RankedInterpretation",
    "ChordInterpretations",
    "ChordIntervalSummary",
    "Inversion",
    "ModeRotation",
    "ReflectionAxis",
    "ScaleAnalysisResult",
    "ScaleIntervalSummary",
    "SetClassData",
    "SymmetryData",
    "TonnetzAnalysis",
    "TonicContext",
    "VoiceLeadingResult",
    "VoicingAnalysis",
    "VoicingEntry",
    "VoicingSet",
]
