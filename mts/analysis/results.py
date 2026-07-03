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
    rotational_period: int
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
    """Interval statistics for a chord — **root-relative and therefore
    transposition-invariant** (a pure-identity analysis must report the same
    summary for the same shape at every root). ``span_semitones`` is the
    largest interval from the root within one octave of the root-position
    layout; ``span_compact`` is the tightest one-octave rotation of that
    layout; ``interval_pairs`` are pairwise intervals of the root-relative
    pcs."""
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
    is the conventional shorthand for **tertian** triads and seventh chords
    (e.g. ``6``, ``6/4``, ``6/5``); ``None`` for non-tertian chords (maj6,
    add9, sus…) and cardinalities without a standard figure — the figures name
    positions of a stack of thirds, so anything else gets no figure rather
    than a wrong one.
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
    matches a catalog quality). ``rotational_period`` explains why symmetric
    chords repeat. Roots are restricted to tones present in the set.
    """
    pcs: list[int]
    mask: int
    cardinality: int
    rotational_period: int
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
class RelativeKeyEvidence:
    """One tonal-hierarchy signal behind a relative-key tie-break (Decision 7).

    ``value`` is the (weight-normalized) signal reading, ``weight`` its
    contribution from the versioned table; both signed so positive favors the
    minor reading."""

    signal: str
    value: float
    weight: float
    detail: str | None = None


@dataclass(frozen=True)
class RelativeKeyDisambiguation:
    """A relative-major/minor tie-break over a key-induction result (3.5a).

    ``infer_key`` (the stability-contract surface) is left untouched and carried
    here as ``induction``; this is the additive, evidenced refinement applied on
    top. ``applied`` is False when the top candidate and its relative partner are
    *not* a near-tie (passthrough — nothing to second-guess). ``chosen`` /
    ``relative`` are the two members of the disambiguated pair; ``tiebreak_score``
    is signed (+ favors minor, − favors major); ``is_ambiguous`` flags a
    tie-break that itself stayed within the prior's decision band (honest, per
    Decision 7). ``weights_version`` cites the prior.
    """

    applied: bool
    chosen: KeyCandidate | None
    relative: KeyCandidate | None
    is_ambiguous: bool
    tiebreak_score: float
    evidence: list[RelativeKeyEvidence]
    induction: KeyInductionResult
    weights_version: str

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class MeterCandidate:
    """One candidate time signature with its estimation score (gap 11).

    ``score`` is the combined metric fit (bar-period autocorrelation ×
    metric-profile correlation); the two components are exposed as evidence.
    """

    numerator: int
    denominator: int
    score: float
    period_score: float    # bar-period autocorrelation (does the content repeat each bar?)
    profile_score: float   # within-bar accent vs the metric-profile template


@dataclass(frozen=True)
class MeterEstimationResult:
    """Ranked candidate time signatures inferred from note content (gap 11).

    Per Decision 7: plural + evidenced (every candidate with its score, plus the
    top-two ``margin``). The engine **never overrides** the file's declared
    meter — it evidences against it: ``declared_numerator``/``declared_denominator``
    carry the file's claim and ``agrees_with_declared`` flags a disagreement,
    leaving the sequence's ``MeterMap`` untouched. ``grid_beats`` + the cited
    ``profile_version`` make the reading reproducible.

    ``downbeat_offset_beats`` is the winning bar phase of the top candidate (the
    anacrusis / global-phase estimate) — how far into the bar the downbeat sits,
    in beats. It is populated only when ``infer_meter(..., phase_search=True)``;
    the default phase-0 path reports ``None`` (it makes no phase claim).
    """

    candidates: list[MeterCandidate]   # best first
    margin: float
    declared_numerator: int | None
    declared_denominator: int | None
    agrees_with_declared: bool
    grid_beats: float
    profile_version: str
    downbeat_offset_beats: float | None = None

    @property
    def best(self) -> MeterCandidate:
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


@dataclass(frozen=True)
class RealizedVoiceLeading:
    """Minimal voice leading between two *voiced* chords (register-aware).

    The register-required sibling of :class:`VoiceLeadingResult`: ``distance``
    is total motion in actual semitones between MIDI pitches (octaves cost
    12); ``mapping`` is the optimal assignment as ``[from_midi, to_midi]``
    voice pairs. Doublings participate as distinct voices. ``policy`` names
    the cardinality convention (shared with the identity-level metric).
    """

    distance: int
    mapping: list[list[int]]  # [from_midi, to_midi] per voice
    policy: str
    source_midi: list[int]
    target_midi: list[int]

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class CatalogContainer:
    """One catalog identity (scale or chord quality) that contains the query.

    ``root_pc`` is the transposition at which containment holds; ``mask`` is
    the *absolute* mask of the identity rooted there (same bit convention as
    everywhere: bit n = pitch class n). ``is_exact`` marks the query being
    that identity in full, not a proper subset.
    """

    name: str
    root_pc: int
    mask: int
    cardinality: int
    is_exact: bool
    aliases: list[str]


@dataclass(frozen=True)
class CatalogContainment:
    """All catalog scales/qualities containing a pc set (the gap-8 query).

    Containers are sorted tightest-first (cardinality, then name, then root),
    so exact matches lead and the widest scales trail.
    """

    query_pcs: list[int]
    query_mask: int
    scales: list[CatalogContainer]
    qualities: list[CatalogContainer]

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Cadence detection (gap 7)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CadenceChord:
    """A progression chord placed in its key (functional view)."""

    index: int
    root_pc: int
    quality: str
    relative_root: int        # (root_pc - tonic_pc) % 12
    role: str | None          # "tonic" | "predominant" | "dominant"; None = non-functional
    roman: str | None         # the functional roman label, when it has a role


@dataclass(frozen=True)
class CadenceEvent:
    """One detected cadential formula, with its per-signal evidence (Decision 7).

    A *formula*, not a confirmed phrase cadence: metric/phrase confirmation
    is absent without timing, so ``is_final`` (arrival is the last chord) is
    surfaced as the strongest evidence and half cadences are emitted only at
    a final arrival on the dominant. ``root_motion`` is ascending semitones
    approach→arrival (0–11).
    """

    type: str                 # "authentic" | "plagal" | "half" | "deceptive"
    arrival_index: int
    approach: CadenceChord
    arrival: CadenceChord
    root_motion: int
    is_final: bool
    evidence: list[str]


@dataclass(frozen=True)
class CadenceResult:
    """Cadence formulas across a progression in a key (gap 7).

    ``mode_supported`` is False for modes outside the functional vocabulary
    (major/minor only — an accepted limitation): roles are then all ``None``
    and no cadences are claimed, rather than guessed.
    """

    tonic_pc: int
    mode: str
    mode_supported: bool
    chords: list[CadenceChord]
    cadences: list[CadenceEvent]

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
    the dataset layer re-exports it. ``margin`` (additive, 2026-06-12) is
    the key-confidence margin of the induction candidate or key region this
    context came from — ``None`` when the context was supplied directly
    rather than inferred.
    """

    tonic_pc: int | None = None
    key_name: str | None = None
    key_degrees: list[int] | None = None
    margin: float | None = None


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
    # (RE-2e) There is deliberately no inverted_interval_class_histogram: the
    # interval matrix is symmetric under negation mod 12, so it was provably
    # always identical to interval_class_histogram — a dead-equal field.
    inverted_interval_matrix: list[list[int]]
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


# ---------------------------------------------------------------------------
# Next-chord recommendation (gap 14, slice 1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SuccessionEvidence:
    """One scored succession signal behind a candidate's rank (Decision 7).

    ``weight`` is the contribution applied from the versioned table — already
    scaled for the per-count signals (``common_tone``, ``vl_distance``)."""

    signal: str
    weight: float
    detail: str | None = None


@dataclass(frozen=True)
class NextChordCandidate:
    """One ranked candidate next chord with its transition tags + evidence.

    The qualitative annotations live in ``tags`` (functional-succession +
    voice-leading + cadential); the raw ranking axes are exposed directly
    (``vl_distance``, ``common_tones``, ``root_interval``, ``color_shift``) so
    a caller can re-rank by any of them. ``cadence`` is the cadential formula
    this single transition forms (authentic/plagal/deceptive/half), or None.
    """

    root_pc: int
    quality: str
    modal_label: str | None   # roman label (functional, not spelling); None if out of vocabulary
    role: str | None          # "tonic" | "predominant" | "dominant" | None
    score: float
    rank: int
    tags: tuple[str, ...]
    vl_distance: int
    common_tones: int
    root_interval: int        # (candidate_root - current_root) % 12
    color_shift: float        # Euclidean delta of the 6-D DFT magnitude vector
    cadence: str | None
    evidence: list[SuccessionEvidence]


@dataclass(frozen=True)
class NextChordRecommendation:
    """Ranked, tagged candidate next chords from a current chord in a key.

    Per Decision 7: plural (every candidate kept, scored), explicit
    (per-candidate ``evidence``; ``weights_version`` cites the prior), and
    register-free (identity-level). Major/minor only — modal keys raise rather
    than guess function. The per-style corpus transition prior that supplies
    *historical* tags is the planned follow-on (ROADMAP gap 14).
    """

    context: AnalyticalContextSnapshot
    current_root_pc: int
    current_quality: str
    current_role: str | None
    current_roman: str | None
    candidates: list[NextChordCandidate]
    weights_version: str

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


__all__ = [
    "AnalyticalContextSnapshot",
    "CatalogContainer",
    "CatalogContainment",
    "ChordAnalysisResult",
    "ChordInterpretation",
    "ChordNaming",
    "KeyCandidate",
    "KeyInductionResult",
    "RelativeKeyEvidence",
    "RelativeKeyDisambiguation",
    "MeterCandidate",
    "MeterEstimationResult",
    "MultiKeyNaming",
    "NamingEvidence",
    "NamingUnderKey",
    "NextChordCandidate",
    "NextChordRecommendation",
    "RankedInterpretation",
    "SuccessionEvidence",
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
    "RealizedVoiceLeading",
    "VoiceLeadingResult",
    "VoicingAnalysis",
    "VoicingEntry",
    "VoicingSet",
]
