"""MCP tool functions: one thin adapter per analysis entry point.

Every function here is pure glue — parse agent-friendly inputs (note names or
pitch-class ints, catalog names, MIDI numbers), call exactly one engine entry
point, return its dict form. Errors surface as ``ValueError`` with actionable
messages (a blind agent can discover valid names via ``list_scales`` /
``list_chord_qualities``). The functions are SDK-free so the full surface is
testable without the optional ``mcp`` dependency; ``server.py`` registers
``TOOLS`` with FastMCP.
"""

from __future__ import annotations

from ..analysis import (
    AnalyticalContext,
    ChordAnalysisRequest,
    InsufficientInformation,
    ScaleAnalysisRequest,
    analyze_chord,
    analyze_scale,
    analyze_voicing,
    contextualize_chord,
    find_containers,
    infer_key,
    interpret_chord,
    name_chord,
    name_chord_across_keys,
    parse_chord_spec,
    suggest_voicings,
    voice_leading,
)
from ..analysis.comparisons import compare_chord_qualities
from ..analysis.pcset_math import set_class_data
from ..analysis.summaries import chord_brief
from ..search import search_identities as _search_identities
from ..search import search_voicings as _search_voicings
from ..core.bitmask import mask_from_pcs
from ..core.chord import Chord
from ..core.enharmonics import pc_from_name
from ..core.pitch import Pitch
from ..core.realization import Realization
from ..core.symmetry import rotational_period
from ..dataset.builders import dataset_from_sequence
from ..io.loaders import load_chord_qualities, load_key_profiles, load_scales


# --- input helpers (agent-friendly coercions) --------------------------------------

def _pc(value: int | str) -> int:
    """A pitch class from an int (0-11) or a note name ('C', 'F#', 'Bb')."""
    if isinstance(value, str):
        return pc_from_name(value)
    pc = int(value)
    if not 0 <= pc < 12:
        raise ValueError(f"Pitch class out of range: {pc} (use 0-11 or a note name).")
    return pc


def _quality(name: str):
    catalog = load_chord_qualities()
    if name not in catalog:
        raise ValueError(
            f"Unknown chord quality {name!r}. Call list_chord_qualities for valid names/aliases."
        )
    return catalog[name]


def _scale(name: str):
    catalog = load_scales()
    if name not in catalog:
        raise ValueError(f"Unknown scale {name!r}. Call list_scales for valid names/aliases.")
    return catalog[name]


def _context(tonic: int | str | None, key_name: str | None) -> AnalyticalContext | None:
    if tonic is None and key_name is None:
        return None
    if tonic is None:
        raise ValueError("A key_name needs a tonic (the key's root pitch class or note name).")
    key = _scale(key_name) if key_name is not None else None
    return AnalyticalContext(tonic_pc=_pc(tonic), key=key)


def _profiles(profile_version: str | None):
    """Load a key-profile set by version, or None to use the engine default
    (kk-1982.1 — the pinned A5/A7 stability contract). Surfaces an actionable
    ValueError on an unknown version (the loader lists the known versions)."""
    if profile_version is None:
        return None
    return load_key_profiles(str(profile_version))


def _realization(midi_notes: list[int] | None, root: int | str | None = None) -> Realization | None:
    if not midi_notes:
        return None
    pitches = tuple(Pitch.from_midi(int(m)) for m in midi_notes)
    return Realization(pitches, root_pc=_pc(root) if root is not None else None)


# --- catalog discovery (for blind agent use) -----------------------------------------

def list_scales() -> list[dict]:
    """All catalog scales: name, degrees (intervals above the root), aliases."""
    seen: dict[str, dict] = {}
    for scale in load_scales().values():
        seen.setdefault(
            scale.name,
            {"name": scale.name, "degrees": list(scale.degrees), "aliases": list(scale.aliases)},
        )
    return list(seen.values())


def list_chord_qualities() -> list[dict]:
    """All catalog chord qualities: name, intervals above the root, tensions, aliases."""
    seen: dict[str, dict] = {}
    for quality in load_chord_qualities().values():
        seen.setdefault(
            quality.name,
            {
                "name": quality.name,
                "intervals": list(quality.intervals),
                "tensions": list(quality.tensions),
                "aliases": list(quality.aliases),
            },
        )
    return list(seen.values())


# --- identity analysis ---------------------------------------------------------------

def parse_chord(text: str) -> dict:
    """Parse a chord expression in any supported notation.

    Forms: interval lists "C3[0,4,7]" / "[0,3,7]", degree lists "(1,b3,5)",
    note tokens "[C,E,G]", MIDI sets "{60,64,67}", catalog names "C:min7",
    inline alias "=label".
    """
    return parse_chord_spec(text).to_dict()


def chord_analysis(
    root: int | str,
    quality: str,
    tonic: int | str | None = None,
    include_inversions: bool = True,
    include_set_class: bool = True,
) -> dict:
    """Full identity analysis of a rooted chord (intervals, symmetry, set class, Tonnetz)."""
    chord = Chord.from_quality(_pc(root), _quality(quality))
    request = ChordAnalysisRequest(
        chord=chord,
        tonic_pc=_pc(tonic) if tonic is not None else None,
        include_inversions=include_inversions,
        include_set_class=include_set_class,
    )
    return analyze_chord(request).to_dict()


def scale_analysis(
    scale_name: str | None = None,
    degrees: list[int] | None = None,
    tonic: int | str | None = None,
) -> dict:
    """Full analysis of a scale by catalog name OR an explicit degree list."""
    if (scale_name is None) == (degrees is None):
        raise ValueError("Provide exactly one of scale_name or degrees.")
    if scale_name is not None:
        scale = _scale(scale_name)
    else:
        from ..core.scale import Scale

        scale = Scale.from_degrees("Custom", [int(d) % 12 for d in degrees])
    request = ScaleAnalysisRequest(
        scale=scale, tonic_pc=_pc(tonic) if tonic is not None else None
    )
    return analyze_scale(request).to_dict()


def set_class_info(pcs: list[int]) -> dict:
    """Set-class identity of a pc set: normal order, Rahn prime form, Z-partner,
    DFT magnitudes AND phases, rotational period, trichord chirality.

    `rotational_period` is the smallest self-mapping transposition (12 = no
    rotational symmetry; augmented → 4, dim7 → 3 — renamed from the misleading
    `rotational_symmetry_order` 2026-06-30; value unchanged).

    `dft_magnitudes` (|f1..f6|) is the transposition- and inversion-invariant
    interval-content fingerprint; `dft_phases` (arg f1..f6, radians) is NOT
    invariant — it rotates under transposition and negates under inversion,
    carrying the absolute-position/handedness info the magnitudes discard (colour
    hue, chirality inputs — Audiology brief-15). `trichord_chirality` is the
    inversion-odd step-gap handedness for 3-note sets (major −2 / minor +2 /
    achiral 0), null for non-trichords; `general_chirality` is the bispectrum-slice
    handedness `Im(f1·f2·conj(f3))` that works for ANY cardinality (transposition-
    invariant, inversion-odd; major<0 / minor>0; 0 for achiral sets; separates
    dom7 from m7♭5 — which the trichord scalar cannot — Audiology brief-15);
    `chirality_sign` (-1/0/+1) is the COMPLETE handedness — 0 **iff** the set is
    achiral, -1 for major's handedness / +1 for its mirror — the signed-chirality
    research result (general_chirality carries a magnitude but false-zeros on a few
    exotic classes; this never does). `chirality` is the complete signed CONTINUOUS
    scalar (Audiology brief-16) = chirality_sign · √R, R the best-fit reflection-axis
    residual: 0 iff achiral, inversion-odd, major<0/minor>0, dom7 = -m7♭5, with a
    real magnitude (|chirality| = √R orders sets by how chiral they are).
    `prime_form`, `prime_form_mask`, and the 12-bit `mask` are all returned."""
    from ..analysis.pcset_math import trichord_chirality
    from ..core.setclass import (
        chirality,
        chirality_sign,
        dft_phases,
        general_chirality,
        reflection_residual,
    )

    mask = mask_from_pcs({int(pc) % 12 for pc in pcs})
    if mask == 0:
        raise ValueError("set_class_info needs at least one pitch class.")
    data = set_class_data(mask).to_dict()
    data["dft_phases"] = list(dft_phases(mask))
    data["rotational_period"] = rotational_period(mask)
    data["trichord_chirality"] = trichord_chirality(mask)
    data["general_chirality"] = general_chirality(mask)
    data["chirality_sign"] = chirality_sign(mask)
    data["chirality"] = chirality(mask)
    # export.2 mirror: R itself, the best-fit reflection-axis residual
    # (|chirality| = sqrt(R)) — added alongside the table column so the
    # tool/table mirror holds on every field (tonality-core slice 1b).
    data["reflection_residual"] = reflection_residual(mask)
    data["mask"] = mask
    return data


def interpretations(pcs: list[int]) -> dict:
    """Every structurally-valid (root, quality) naming of a pc set
    (symmetric and ambiguous sets yield several)."""
    return interpret_chord(int(pc) % 12 for pc in pcs).to_dict()


def catalog_containment(pcs: list[int]) -> dict:
    """Every catalog scale and chord quality that contains a pc set, at which
    roots — tightest containers first, exact matches flagged, absolute masks.
    The reverse of chord-in-scale compatibility."""
    return find_containers(pcs).to_dict()


def search_identities(
    constraints: dict,
    expand_transpositions: bool = False,
    limit: int | None = None,
) -> dict:
    """Inverse analysis: every pitch-class-set identity satisfying a constraint
    object, enumerated exactly over the 4096-identity universe.

    constraints is {field: condition}. Scalar fields — cardinality, ic1..ic6
    (interval-vector entries), rotational_period, is_achiral,
    no_consecutive_semitones — take a literal (equality), {"in": [...]},
    {"gte": n}, or {"lte": n}. Float fields — df1..df6 (DFT magnitudes |f1..f6|;
    df5 = diatonicity/fifthiness, df6 = whole-tone-ness) — are range-queried with
    {"gte": x} / {"lte": x} only. Structural fields — contains / contained_in —
    take a pc-set matched at ANY transposition; a `contains` match reports the
    roots where the shape appears. Fields AND together. Every match also carries
    its full |f1..f6| `dft_magnitudes` spectrum, so callers can rank, not just
    filter.

    Default universe is the 223 set classes (prime forms); expand_transpositions
    widens to every rooted image. limit caps reported matches (count stays the
    true total; truncated flags the cut). Invalid constraints raise ValueError
    listing EVERY problem at once. Example: {"cardinality": 7, "contains":
    [0,4,7], "no_consecutive_semitones": true} — 7-note scales holding a major
    triad with no chromatic run."""
    return _search_identities(
        constraints, expand_transpositions=expand_transpositions, limit=limit
    ).to_dict()


# --- contextual analysis -----------------------------------------------------------------

def chord_in_key(root: int | str, quality: str, tonic: int | str, key_name: str) -> dict:
    """Place a rooted chord in a key: scale degrees, diatonic membership, chromatic tones."""
    chord = Chord.from_quality(_pc(root), _quality(quality))
    context = _context(tonic, key_name)
    return contextualize_chord(chord, context).to_dict()


def name_pcs(
    pcs: list[int],
    tonic: int | str | None = None,
    key_name: str | None = None,
    realization_midi: list[int] | None = None,
) -> dict:
    """The contextually-chosen naming of a pc set, with ranked alternatives and
    evidence. Omit tonic/key_name for intrinsic-only ranking (no key is invented);
    pass realization_midi (actual sounding notes) to let the bass note weigh in."""
    return name_chord(
        pcs, _context(tonic, key_name), realization=_realization(realization_midi)
    ).to_dict()


def key_induction(pc_weights: list[float], profile_version: str | None = None) -> dict:
    """Ranked key candidates for duration-weighted pitch-class content
    (12 weights, index = pc). All 24 candidates, scores, and the top-two margin.
    profile_version selects the versioned key-profile set: default (None) uses
    kk-1982.1; 'tkp-cbms.1' is the opt-in Temperley-Kostka-Payne profile (better-
    balanced for major keys / less dominant-biased — A6 brief-9). The result cites
    the profile_version used."""
    return infer_key(pc_weights, profiles=_profiles(profile_version)).to_dict()


def relative_key(pc_weights: list[float]) -> dict:
    """Relative-major/minor tie-breaker over duration-weighted pitch-class content
    (12 weights, index = pc). Relative pairs (e.g. C major / A minor) share a
    diatonic collection, so the KK-profile correlation in key_induction separates
    them weakly; this applies tonal-hierarchy signals (leading-tone, tonic-triad
    and tonic salience) to choose between them, evidenced and versioned
    (rel-key.1). key_induction itself is unchanged and carried in the result as
    `induction`. `applied` is false when the top key and its relative partner are
    not a near-tie (nothing to second-guess); `is_ambiguous` flags an honestly
    inconclusive tie-break. Positive `tiebreak_score` favors the minor reading."""
    from ..analysis import disambiguate_relative_key

    return disambiguate_relative_key(pc_weights).to_dict()


def meter_estimation(
    events: list[list],
    bpm: float = 120.0,
    numerator: int = 4,
    denominator: int = 4,
    phase_search: bool = False,
) -> dict:
    """Infer the time signature from note content — ranked candidate signatures
    with scores + margin, and a declared-vs-estimated disagreement flag. Each
    candidate's score combines bar-period autocorrelation (does the content
    repeat each bar?) with metric-profile correlation (does the within-bar
    accent match the meter's template — distinguishing e.g. 3/4 from 6/8);
    templates are a versioned prior (meter-grid.1, cited). The engine NEVER
    overrides the file's meter — numerator/denominator set the declared meter
    and `agrees_with_declared` evidences against it. events: the canonical event form [onset_beats, duration_beats, midi_note, velocity?, voice?] — velocity numeric at index 3, voice string at index 4 (a bare string at index 3 reads as the legacy voice form) (velocity, when
    present, weights the accent). phase_search (default off): also search every bar phase and
    report the top candidate's winning downbeat offset (the anacrusis / global
    phase) as `downbeat_offset_beats` — `None` when off. Raises on too few onsets
    or content with no metric information."""
    from ..analysis import infer_meter
    from ..temporal import Event, Sequence

    sequence = _canonical_sequence(
        events, bpm=float(bpm), time_signature=(int(numerator), int(denominator))
    )
    return infer_meter(sequence, phase_search=bool(phase_search)).to_dict()


def meter_tracking(
    events: list[list],
    window_beats: float = 16.0,
    hop_beats: float = 4.0,
    bpm: float = 120.0,
) -> dict:
    """Local meter tracking: time-signature regions through time — the windowed
    form of meter_estimation, as key_tracking is to key_induction. A window
    slides over the events; each window's onset/accent content is ranked by the
    same metric-fit method (same versioned meter-grid prior), with a per-window
    PHASE SEARCH so a window not starting on a bar line is still read correctly;
    consecutive same-best-meter windows merge into regions (beats+seconds extents,
    mean score/margin, per-window evidence). The per-window phase search also
    reports its winning bar phase as `downbeat_offset_beats` on each window and
    aggregated per region (the local anacrusis estimate). A window with too few onsets or no
    differential accent makes no claim (regions merge across it). Meter needs
    several bars of evidence, so windows default larger than key tracking's
    (window_beats 16, hop_beats 4); boundary resolution is the hop grid. events: the canonical event form [onset_beats, duration_beats, midi_note, velocity?, voice?] — velocity numeric at index 3, voice string at index 4 (a bare string at index 3 reads as the legacy voice form) (velocity,
    when present, weights the accent). Raises if no window carries metric information."""
    from ..temporal import Event, Sequence, track_meter

    sequence = _canonical_sequence(events, bpm=float(bpm))
    return track_meter(
        sequence, window_beats=float(window_beats), hop_beats=float(hop_beats)
    ).to_dict()


def name_pcs_in_inferred_keys(
    pcs: list[int],
    pc_weights: list[float],
    realization_midi: list[int] | None = None,
) -> dict:
    """Infer the key from pc_weights, then name the pc set conditional on each
    ranked key candidate, plus a key-confidence-weighted combined ranking."""
    keys = infer_key(pc_weights)
    return name_chord_across_keys(
        pcs, keys, realization=_realization(realization_midi)
    ).to_dict()


def cadences(chords: list[list], tonic: int | str, mode: str = "major") -> dict:
    """Detect cadential formulas (authentic / plagal / half / deceptive) in a
    named chord progression within a key — each an evidenced event (Decision 7
    shape). chords: ordered [root, quality] pairs (root = note name or pc 0-11,
    quality = a catalog name like 'maj', '7', 'min'). mode: 'major' or 'minor'
    (others return mode_supported=false — functional vocabulary is major/minor
    only). These are formulas, not phrase-confirmed cadences: arrival-as-final
    is the strongest evidence, and a half cadence is only flagged at a final
    arrival on V."""
    from ..analysis import detect_cadences

    try:
        parsed = [(_pc(entry[0]), str(entry[1])) for entry in chords]
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError(
            f"Each chord must be [root, quality] (root = note name or pc; "
            f"quality = a catalog name): {exc}"
        ) from exc
    return detect_cadences(parsed, tonic_pc=_pc(tonic), mode=str(mode)).to_dict()


def next_chord(
    current: list,
    tonic: int | str,
    mode: str = "major",
    history: list[list] | None = None,
    qualities: list[str] | None = None,
    vl_neighbours: bool = False,
    vl_max_distance: int = 3,
) -> dict:
    """Recommend ranked candidate next chords from a current chord in a key,
    each TAGGED with succession context (Decision 7 — plural + evidenced). Tags
    span functional-succession (dominant_resolution, descending_fifth,
    prolongation, retrogression, applied_dominant, borrowed + the cadential
    formula authentic/plagal/deceptive/half), voice-leading (smooth,
    parsimonious with P/L/R detail, chromatic_mediant, common_tone count), and a
    reported-but-unscored color_shift (DFT delta). Scoring weights are a
    versioned prior (succession.1, cited); every candidate exposes its raw axes
    (vl_distance, common_tones, root_interval, color_shift) so you can re-rank.
    current: [root, quality] (root = note name or pc 0-11; quality = a catalog
    name like 'maj', '7', 'min'). mode: 'major' or 'minor' (others raise —
    function is not guessed). history: optional preceding [[root, quality], ...]
    for cadential context. qualities: optional candidate-vocabulary override
    (default = core triads + sevenths). Set vl_neighbours=true to ALSO generate
    voice-leading-neighbour candidates — chords reachable within vl_max_distance
    semitones of total motion but outside the functional vocabulary, so chromatic
    mediants surface (tagged vl_neighbour; role/roman null when out-of-vocabulary).
    The historical/corpus tags are a planned follow-on (ROADMAP gap 14)."""
    from ..analysis import recommend_next_chord

    try:
        cur = (_pc(current[0]), str(current[1]))
        hist = (
            [(_pc(entry[0]), str(entry[1])) for entry in history]
            if history is not None
            else None
        )
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError(
            f"current and each history entry must be [root, quality] (root = "
            f"note name or pc; quality = a catalog name): {exc}"
        ) from exc
    return recommend_next_chord(
        cur,
        tonic_pc=_pc(tonic),
        mode=str(mode),
        history=hist,
        qualities=[str(q) for q in qualities] if qualities is not None else None,
        vl_neighbours=bool(vl_neighbours),
        vl_max_distance=int(vl_max_distance),
    ).to_dict()


def melodic_tendency(
    pc: int | str | None = None,
    degree: int | None = None,
    tonic: int | str = 0,
    mode: str = "major",
    chord_pcs: list[int | str] | None = None,
    targets: str = "diatonic_steps",
    prior_version: str | None = None,
) -> dict:
    """Where a pitch wants to resolve, and how strongly — the melodic sibling
    of next_chord (gap 19). Ranked resolutions with evidence + the full 12-pc
    stability landing table, in one call.

    Provide EXACTLY ONE of pc (note name or 0-11) or degree (1-7, resolved
    through the mode's scale). mode: 'major' or 'minor'. Model: anchoring
    attraction (s_target/s_source)/d^2 with stabilities from a versioned prior
    (melodic-tendency.1 — frozen from the kk-1982.1 profiles); ti->do ranks
    strongest by construction, stable tones barely tend anywhere. chord_pcs
    opts into chord-tone anchoring (boost cited in the prior). targets selects
    the resolution-target policy: 'diatonic_steps' (default — scale members
    within a step; a leap is not a resolution) or 'chromatic_steps' (all step
    neighbors; out-of-key targets flagged in_key=false). The stability table is
    the cited replacement for root>third hand rules; the caller owns any snap
    policy (strengths are continuous signals, Decision 7)."""
    from ..analysis import melodic_tendency as _melodic_tendency

    return _melodic_tendency(
        _pc(pc) if pc is not None else None,
        degree=int(degree) if degree is not None else None,
        tonic_pc=_pc(tonic),
        mode=str(mode),
        chord_pcs=[_pc(c) for c in chord_pcs] if chord_pcs is not None else None,
        targets=str(targets),
        prior_version=prior_version,
    ).to_dict()


def key_tracking(
    events: list[list],
    window_beats: float = 8.0,
    hop_beats: float = 2.0,
    bpm: float = 120.0,
    disambiguate_relative: bool = False,
    smoothing: bool = False,
    profile_version: str | None = None,
    key_inertia: bool = False,
) -> dict:
    """Local key tracking: key regions through time for a list of events —
    the canonical event form [onset_beats, duration_beats, midi_note,
    velocity?, voice?]. Windowed key induction (same
    versioned profiles; profile_version selects the set — default kk-1982.1,
    'tkp-cbms.1' the opt-in Temperley-Kostka-Payne alternative, A6 brief-9);
    regions carry beats+seconds extents, mean score/margin,
    and the per-window evidence. Boundary resolution is the window grid. Set
    disambiguate_relative=true to apply the relative-major/minor tie-breaker per
    window (off by default): a window over a relative near-tie adopts the
    tonal-hierarchy reading instead of the bare correlation argmax — better
    relative-key sections in the timeline; cited on the result. Set
    smoothing=true to absorb short, low-confidence key-region blips into their
    stronger neighbour (off by default, versioned hysteresis): removes residual
    micro-band noise on real performances; windows keep their raw argmax as
    evidence, only the region grouping is smoothed; cited via smoothing_version.
    Set key_inertia=true (off by default; A6 brief-13) to apply a continuity prior:
    a deterministic Viterbi over the per-window scores with a versioned switch
    penalty (key-inertia.1, cited via inertia_version) that rewards fit + penalizes
    switching, holding near-tie mode flips to context and cutting over-segmentation;
    composes with smoothing and leaves infer_key untouched."""
    from ..temporal import Event, Sequence, track_keys

    sequence = _canonical_sequence(events, bpm=float(bpm))
    return track_keys(
        sequence,
        window_beats=window_beats,
        hop_beats=hop_beats,
        disambiguate_relative=bool(disambiguate_relative),
        smoothing=bool(smoothing),
        profiles=_profiles(profile_version),
        key_inertia=bool(key_inertia),
    ).to_dict()


def structural_keys(
    events: list[list],
    window_beats: float = 8.0,
    hop_beats: float = 2.0,
    bpm: float = 120.0,
    disambiguate_relative: bool = False,
    smoothing: bool = False,
    anchor_method: str = "frame_weighted",
    profile_version: str | None = None,
    key_inertia: bool = False,
) -> dict:
    """Reduce the windowed local key track to **structural key-areas** — the
    fix for over-segmentation. The windowed `key_tracking` reports each window's
    best-fit key, so a brief tonicization (a V/V span) reads as the dominant's
    key; this distinguishes a **tonicization** (brief, diatonically-related
    excursion — absorbed into the parent key and recorded as a `degree`) from a
    **modulation** (sustained/structural change — kept), via relatedness AND
    (brevity OR return) — the functional context confidence-gating lacks.
    Returns structural `areas` (each with its absorbed `tonicizations` + the
    home key) and carries the underlying `tracking` + global key as evidence;
    thresholds are a versioned prior (structural-key.2, cited). Never overrides
    the file's meter/key. events: the canonical event form [onset_beats, duration_beats, midi_note, velocity?, voice?] — velocity numeric at index 3, voice string at index 4 (a bare string at index 3 reads as the legacy voice form). disambiguate_relative/smoothing choose the underlying local
    track the reduction runs on (the reduction is agnostic to either).
    anchor_method picks the home key: 'frame_weighted' (default — weights the
    opening + closing regions, the tonicization-robust home-key signal for pieces
    whose interior repeatedly tonicizes the dominant; promoted to default after A6
    brief-8 validated it on the full Winterreise set, a Pareto improvement) or
    'most_prevalent_region' (legacy — longest summed local duration).
    profile_version selects the versioned key-profile set used for both the
    windowed track and the global evidence (default kk-1982.1; 'tkp-cbms.1' opt-in,
    A6 brief-9)."""
    from ..temporal import Event, Sequence, reduce_to_structural_keys, track_keys

    sequence = _canonical_sequence(events, bpm=float(bpm))
    profiles = _profiles(profile_version)
    tracking = track_keys(
        sequence, window_beats=float(window_beats), hop_beats=float(hop_beats),
        disambiguate_relative=bool(disambiguate_relative), smoothing=bool(smoothing),
        profiles=profiles, key_inertia=bool(key_inertia),
    )
    return reduce_to_structural_keys(
        sequence, tracking=tracking, anchor_method=str(anchor_method), profiles=profiles,
    ).to_dict()


def voice_pair_motion(events: list[list]) -> dict:
    """Classify how voice pairs move (parallel/similar/contrary/oblique, with
    interval evidence) for voiced events — the canonical event form [onset_beats,
    duration_beats, midi_note, velocity?, voice?] (voiced = the voice slot is
    set; the legacy [.., voice]-at-index-3 string form still reads). The 'which voice moved' primitive counterpoint
    predicates filter — e.g. parallel fifths = motion 'parallel' with
    interval_class 7."""
    from ..temporal import Event, Sequence, voice_motion

    return voice_motion(_canonical_sequence(events)).to_dict()


def melodic_analysis(
    events: list[list],
    harmony: list[list] | None = None,
) -> dict:
    """Melodic atoms for one monophonic line: signed intervals, step/skip/leap
    classes, Parsons contour, ambitus, approach/departure per note — plus
    non-harmonic-tone typing (passing, neighbor, appoggiatura, escape,
    suspension, anticipation, pedal) when harmony is given. events: the canonical event form [onset_beats, duration_beats, midi_note, velocity?, voice?] — velocity numeric at index 3, voice string at index 4 (a bare string at index 3 reads as the legacy voice form). harmony (optional): spans
    [start_beat, end_beat, [pcs]] — without it no chord-tone claims are made."""
    from ..temporal import Event, Sequence, analyze_melody

    spans = None
    if harmony is not None:
        try:
            spans = [(float(s), float(e), [int(pc) for pc in pcs]) for s, e, pcs in harmony]
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Each harmony span must be [start_beat, end_beat, [pcs]]: {exc}"
            ) from exc
    return analyze_melody(_canonical_sequence(events), harmony=spans).to_dict()


def rhythmic_analysis(
    events: list[list],
    numerator: int = 4,
    denominator: int = 4,
) -> dict:
    """Rhythmic atoms for one monophonic line: metric placement (downbeat /
    beat / offbeat / subdivision against the felt beat — compound meters
    beat in threes), a precise syncopation predicate (a weak onset sounding
    through the next stronger grid line), durations and inter-onset
    intervals. events: the canonical event form [onset_beats, duration_beats, midi_note, velocity?, voice?] — velocity numeric at index 3, voice string at index 4 (a bare string at index 3 reads as the legacy voice form);
    numerator/denominator set a constant time signature (full meter maps via
    the library door)."""
    from ..temporal import Event, Sequence, analyze_rhythm

    sequence = _canonical_sequence(
        events, time_signature=(int(numerator), int(denominator))
    )
    return analyze_rhythm(sequence).to_dict()


def swing_analysis(
    events: list[list],
    numerator: int = 4,
    denominator: int = 4,
) -> dict:
    """Swing-feel estimate for a monophonic line with symbolically-encoded
    timing: measures where each two-way beat division places its interior
    onset (0.5 = straight, 2/3 = triplet swing 2:1, 0.75 = dotted shuffle
    3:1, < 0.5 = reversed) and classifies the feel under a versioned prior
    cited in the result. Raises when there are too few divisions to claim a
    feel. events: the canonical event form [onset_beats, duration_beats, midi_note, velocity?, voice?] — velocity numeric at index 3, voice string at index 4 (a bare string at index 3 reads as the legacy voice form). NOTE:
    quantized-straight MIDI carries no swing to measure — swing must be in
    the onsets themselves."""
    from ..temporal import Event, Sequence, analyze_swing

    sequence = _canonical_sequence(
        events, time_signature=(int(numerator), int(denominator))
    )
    return analyze_swing(sequence).to_dict()


# --- performed-input tolerance (gap 12) ----------------------------------------------

def coalesce_events(
    events: list[list],
    onset_window_beats: float,
    snap_grid_beats: float | None = None,
) -> dict:
    """Opt-in repair for performed/humanized timing BEFORE temporal analysis:
    clusters near-simultaneous onsets/offsets (within onset_window_beats of a
    cluster's earliest point) and optionally snaps to a grid. Returns the
    cleaned events plus what changed (moved count, max shift) and any events
    dropped for collapsing to zero length — losses are itemized, never
    hidden. events: the canonical event form [onset_beats, duration_beats, midi_note, velocity?, voice?] — velocity numeric at index 3, voice string at index 4 (a bare string at index 3 reads as the legacy voice form). The engine never coalesces implicitly; exact input
    stays exact unless you call this."""
    from ..temporal import coalesce

    result = coalesce(
        _canonical_sequence(events),
        onset_window_beats=float(onset_window_beats),
        snap_grid_beats=float(snap_grid_beats) if snap_grid_beats is not None else None,
    )
    voiced = any(e.voice is not None for e in result.sequence.events)
    cleaned = [
        [e.onset, e.duration, e.pitch.midi] + ([e.voice] if voiced else [])
        for e in result.sequence.events
    ]
    return {"events": cleaned, **result.to_dict()}


# --- groove extract / apply (gap 10) -------------------------------------------------

def _canonical_events(events: list[list]) -> tuple:
    """Parse the ONE canonical event form every temporal tool accepts (RE-4a):

        [onset_beats, duration_beats, midi_note, velocity?, voice?]

    ``velocity`` (index 3) is a number or null; ``voice`` (index 4) is a
    string. Legacy compat, additive: a STRING at index 3 is read as the voice
    (the old ``[.., voice]`` convention several tools used) — the JSON types
    keep the two readings unambiguous, and a string at 3 combined with a
    voice at 4 is rejected as contradictory rather than guessed at.
    Returns the parsed Event tuple; callers build the Sequence (they differ
    on bpm/time-signature kwargs).
    """
    from ..temporal import Event

    try:
        parsed = []
        for entry in events:
            velocity = None
            voice = None
            if len(entry) > 3 and entry[3] is not None:
                if isinstance(entry[3], str):
                    if len(entry) > 4 and entry[4] is not None:
                        raise ValueError(
                            f"contradictory event {entry!r}: a string at index 3 "
                            "is the legacy voice form, which cannot combine with "
                            "a voice at index 4"
                        )
                    voice = entry[3]  # legacy [onset, duration, midi, voice]
                else:
                    velocity = int(entry[3])
            if len(entry) > 4 and entry[4] is not None:
                voice = str(entry[4])
            parsed.append(
                Event(
                    float(entry[0]),
                    float(entry[1]),
                    Pitch.from_midi(int(entry[2]), velocity=velocity),
                    voice=voice,
                )
            )
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError(
            "Each event must be [onset_beats, duration_beats, midi_note, "
            "velocity?, voice?] — velocity numeric at index 3 (a bare string "
            "there is read as the legacy voice form), voice string at index 4: "
            f"{exc}"
        ) from exc
    return tuple(parsed)


def _canonical_sequence(events: list[list], **kwargs) -> "Sequence":
    """Canonical events straight to a Sequence (kwargs: bpm, time_signature)."""
    from ..temporal import Sequence

    return Sequence.from_events(_canonical_events(events), **kwargs)


def extract_groove(
    events: list[list],
    base_unit_beats: float,
    loop_length_beats: float | None = None,
    voice: str | None = None,
) -> dict:
    """Distil a GrooveTemplate from a played loop's onset timing and velocity:
    per grid slot (at base_unit_beats, e.g. 0.25 = 1/16), the signed onset
    offset (fraction of the grid unit) and velocity accent (deviation from the
    loop mean), cycled over loop_length_beats. ANALYSIS — quantized input
    yields a NULL groove (all offsets 0.0); the feel must be in the onsets to
    be measured. Polyphony is fine (simultaneous onsets share a slot).
    loop_length_beats defaults to the sequence duration rounded to whole slots
    — pass it explicitly for a clean loop. events: the canonical event form
    [onset_beats, duration_beats, midi_note, velocity?, voice?]."""
    from ..temporal import extract_groove as _extract

    template = _extract(
        _canonical_sequence(events),
        base_unit_beats=float(base_unit_beats),
        loop_length_beats=(
            float(loop_length_beats) if loop_length_beats is not None else None
        ),
        voice=voice,
    )
    return template.to_dict()


def apply_groove(
    events: list[list],
    template: dict,
    quantize: float = 1.0,
    timing: float = 1.0,
    random: float = 0.0,
    velocity: float = 1.0,
    amount: float = 1.0,
    seed: int | None = None,
    voice: str | None = None,
) -> dict:
    """Apply a GrooveTemplate to events, returning new onset+velocity timing.
    GENERATIVE (A2's first transformation). Live Groove Pool parameters:
    quantize [0,1] pre-pulls onsets toward the grid; timing scales the
    template offsets (may exceed 1.0); random [0,1] adds deterministic jitter
    (REQUIRES seed when > 0 — same input + same seed → same output); velocity
    is a signed scale on the accent contour (negative reverses); amount [0,1]
    is a global multiplier on all feel. Onsets shift, durations are preserved.
    template is the dict returned by extract_groove. events: the canonical event
    form [onset_beats, duration_beats, midi_note, velocity?, voice?]; the
    result echoes velocity at index 3 (and voice at index 4 if
    present) plus the cited parameters and what changed."""
    from ..temporal import GrooveTemplate, apply_groove as _apply

    result = _apply(
        _canonical_sequence(events),
        GrooveTemplate.from_dict(template),
        quantize=float(quantize),
        timing=float(timing),
        random=float(random),
        velocity=float(velocity),
        amount=float(amount),
        seed=int(seed) if seed is not None else None,
        voice=voice,
    )
    voiced = any(e.voice is not None for e in result.sequence.events)
    out = [
        [e.onset, e.duration, e.pitch.midi, e.pitch.velocity]
        + ([e.voice] if voiced else [])
        for e in result.sequence.events
    ]
    return {"events": out, **result.to_dict()}


# --- rulesets (Phase 4.6) -----------------------------------------------------------

def validate_ruleset(ruleset: dict) -> dict:
    """Strictly validate a ruleset document (the Phase 4.6 DSL) WITHOUT
    evaluating it. Returns {"valid": bool, "errors": [...]} with every
    problem listed (unknown keys/families/fields/operators/enum values) —
    built so a blind agent can repair a translation in one round trip.
    Vocabulary: families voice_motion / melody / rhythm; each rule has id,
    family, optional where, exactly one of forbid/require, polarity
    hard|soft (+weight)."""
    from ..rules import validation_errors

    errors = validation_errors(ruleset)
    return {"valid": not errors, "errors": errors}


def evaluate_ruleset(
    ruleset: dict,
    events: list[list],
    harmony: list[list] | None = None,
    chords: list[list] | None = None,
    key: list | None = None,
    include_firings: bool = False,
) -> dict:
    """Evaluate a ruleset (Phase 4.6 DSL) against events — the canonical
    event form [onset_beats, duration_beats, midi_note, velocity?, voice?] —
    returning a
    ConformanceReport: per-rule violations with locations and atom evidence,
    conformance frequencies, hard/soft rollups. Rules referencing
    harmony-dependent fields (nht_type, is_chord_tone) need harmony spans
    [start_beat, end_beat, [pcs]] and are reported not-applicable without
    them. HARMONY-family rules (gap B: chord succession — roman/role/degree/
    quality/is_diatonic/root_motion/next_role/next_roman/common_tones/
    color_shift/cadence) need chords=[[root, quality], ...] and key=[tonic,
    mode] (mode 'major'|'minor'); without both they are not-applicable. Set
    include_firings=true to ALSO get each rule's located firings (considered
    items where it HELD). Invalid rulesets raise with the full error list (use
    validate_ruleset first). events may be [] for a harmony-only ruleset."""
    from ..rules import evaluate

    spans = None
    if harmony is not None:
        try:
            spans = [(float(s), float(e), [int(pc) for pc in pcs]) for s, e, pcs in harmony]
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Each harmony span must be [start_beat, end_beat, [pcs]]: {exc}"
            ) from exc
    chord_stream = None
    if chords is not None:
        try:
            chord_stream = [(_pc(root), str(quality)) for root, quality in chords]
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Each chord must be [root, quality] (root = note name or pc): {exc}"
            ) from exc
    key_pair = None
    if key is not None:
        try:
            key_pair = (_pc(key[0]), str(key[1]))
        except (TypeError, ValueError, IndexError) as exc:
            raise ValueError(f"key must be [tonic, mode] (mode 'major'|'minor'): {exc}") from exc
    return evaluate(
        ruleset, _canonical_sequence(events), harmony=spans,
        chords=chord_stream, key=key_pair, include_firings=bool(include_firings),
    ).to_dict()


def ruleset_field_manifest() -> dict:
    """The ruleset DSL's field vocabulary as a versioned, machine-readable
    manifest: per atom family (voice_motion / melody / rhythm), each legal
    where/check field with its kind, closed value vocabulary (when an enum),
    and harmony-dependence; plus the condition operators and rule polarities.
    The same data validate_ruleset enforces — use it to check field usage
    ahead of time and stay correct as the vocabulary grows."""
    from ..rules import ruleset_field_manifest as _manifest

    return _manifest()


def list_named_rulesets() -> list[str]:
    """The names of the citable rulesets shipped in the library (gap D) —
    e.g. 'first-species-counterpoint'. Load one with load_named_ruleset."""
    from ..rules import list_named_rulesets as _list

    return _list()


def load_named_ruleset(name: str) -> dict:
    """Load a shipped, citable ruleset by name (see list_named_rulesets) as a
    validated DSL payload — ready to feed evaluate_ruleset, or to read/adapt.
    The description documents the ruleset's scope assumptions and the rules it
    could NOT express in the current DSL (recorded expressiveness evidence).
    Unknown names raise with the known list."""
    from ..rules import load_named_ruleset as _load
    from ..rules.schema import ruleset_to_payload

    return ruleset_to_payload(_load(name))


def induce_rules(
    corpus: list[list[list]] | None = None,
    family: str = "voice_motion",
    harmony: list[list[list]] | None = None,
    chord_corpus: list[list] | None = None,
    scoring_prior: str | None = None,
    merge_disjunctions: bool = True,
) -> dict:
    """Mine a corpus for the statistically significant compositional rules it
    follows (Phase 4.6 induction), emitting a validated SOFT ruleset in the DSL
    plus per-rule evidence (support, confidence, leverage, Fisher p-value,
    BH-FDR q-value). Apriori frequent-pattern mining over the where-lattice
    (closed itemsets, arity cap 3) + Fisher's exact test vs an
    independence-given-marginals null, BH-FDR at q=0.05; weights are a versioned
    scoring prior cited in the result. NOTE families ('voice_motion' | 'melody'
    | 'rhythm') read corpus: a list of pieces, each a list of [onset_beats,
    duration_beats, midi_note] (or [..., voice_label] — voices needed for
    voice_motion). harmony: optional per-piece list of [start_beat, end_beat,
    [pcs]] spans (only melody's nht_type/is_chord_tone consult it). The HARMONY
    family instead reads chord_corpus: a list of pieces, each [chords, key] with
    chords=[[root, quality], ...] and key=[tonic, mode] ('major'|'minor') — it
    mines role/next_role/cadence/is_diatonic/degree/root_motion (an unknown
    chord quality raises; open-vocabulary roman/quality are a follow-on). Below
    ~30 pieces the result is flagged exploratory. merge_disjunctions (default
    true) collapses same-(where, field) single-value rules into one `in`-rule
    (forbid ic in {0,7} rather than two forbids), re-tested with Fisher — the
    human-readable form; set false for the raw single-value rules. The emitted
    ruleset round-trips through the validator."""
    from ..rules import induce_ruleset

    if str(family) == "harmony":
        if chord_corpus is None:
            raise ValueError(
                "The harmony family reads chord_corpus=[[chords, key], ...] with "
                "chords=[[root, quality], ...] and key=[tonic, mode] — not the note "
                "`corpus`."
            )
        try:
            pieces = [
                (
                    [(_pc(root), str(quality)) for root, quality in chords],
                    (_pc(key[0]), str(key[1])),
                )
                for chords, key in chord_corpus
            ]
        except (TypeError, ValueError, IndexError) as exc:
            raise ValueError(
                "Each harmony piece must be [chords, key] where "
                f"chords=[[root, quality], ...] and key=[tonic, mode]: {exc}"
            ) from exc
        return induce_ruleset(
            family="harmony", chord_corpus=pieces, scoring_prior=scoring_prior,
            merge_disjunctions=bool(merge_disjunctions),
        ).to_dict()

    if corpus is None:
        raise ValueError(f"family {family!r} reads a note `corpus` (a list of pieces).")
    pieces = [_canonical_sequence(piece) for piece in corpus]
    spans = None
    if harmony is not None:
        try:
            spans = [
                [(float(s), float(e), [int(pc) for pc in pcs]) for s, e, pcs in piece]
                for piece in harmony
            ]
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Each harmony span must be [start_beat, end_beat, [pcs]]: {exc}"
            ) from exc
    return induce_ruleset(
        pieces, family=str(family), harmony=spans, scoring_prior=scoring_prior,
        merge_disjunctions=bool(merge_disjunctions),
    ).to_dict()


def transition_matrix(
    chord_corpus: list[list],
    state: str = "degree",
    smoothing: str = "laplace",
    alpha: float | None = None,
    source: str | None = None,
) -> dict:
    """Aggregate a chord-stream corpus into a first-order degree-transition
    distribution (Phase 4.5, gap 14) — the SAMPLEABLE half of a style profile
    (the ruleset from induce_rules is the constraint half). chord_corpus: a list
    of pieces, each [chords, key] with chords=[[root, quality], ...] and
    key=[tonic, mode] — the same corpus induce_rules(family='harmony') reads; each
    piece contributes its consecutive within-piece state transitions. state keys
    the matrix over the harmony-atom vocabulary: 'degree' (default — scale degrees
    1..7, non-diatonic roots bucketed 'chromatic'), 'role', 'quality', or 'roman'.
    smoothing: 'laplace' (default — add-alpha, NO hard zeros, right for sampling a
    rare-but-possible transition) or 'none' (raw empirical, exact zeros); raw
    integer counts are returned either way, so the caller can re-normalize. alpha
    defaults to the versioned distribution.1 prior. source records provenance.
    Returns {state, states[], counts{}, probabilities{}, smoothing, alpha,
    prior_version, n_transitions, n_pieces, source}. An unknown chord quality
    raises (error, not guess). Deterministic."""
    from ..rules import build_transition_matrix

    try:
        pieces = [
            (
                [(_pc(root), str(quality)) for root, quality in chords],
                (_pc(key[0]), str(key[1])),
            )
            for chords, key in chord_corpus
        ]
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError(
            "Each piece must be [chords, key] where chords=[[root, quality], ...] "
            f"and key=[tonic, mode]: {exc}"
        ) from exc
    return build_transition_matrix(
        pieces, state=str(state), smoothing=str(smoothing), alpha=alpha, source=source,
    ).to_dict()


def segment_chords(
    events: list[list],
    key: list | None = None,
    subdivisions: int = 1,
    min_pc_weight: float = 0.1,
    downbeat_emphasis: float = 2.0,
) -> dict:
    """Reduce a note stream to a chord stream on a metric grid (gap B slice-2a) —
    the bridge from raw MIDI to the harmony family. events: the canonical event
    form [onset_beats, duration_beats, midi_note, velocity?, voice?]. One chord
    per metric window (a bar by default; subdivisions splits each bar into that
    many equal windows). Within a window, pitch classes are weighted by sounding
    duration × downbeat_emphasis (notes onsetting on a downbeat count more), the
    salient set is thresholded at min_pc_weight (fraction of the window's weighted
    content — drops brief non-harmonic tones), and named against the catalog in
    the key. key (optional [tonic, mode]) fixes the key; omit to infer it once
    globally (the result reports key_inferred + key_margin). A window that names
    NO catalog chord is returned with root_pc=null and a reason — never
    fabricated (error, not guess). Returns {tonic_pc, mode, key_inferred,
    key_margin, spans[], chords[[root, quality], …]}; `chords` + [tonic_pc, mode]
    feed evaluate_ruleset / induce_rules(family='harmony') directly. Honest
    limits: single global key (no local regions yet); NHT handling is only the
    salience threshold (no full nesting). Raises on an empty stream."""
    from ..temporal import segment_to_chords

    key_pair = None
    if key is not None:
        try:
            key_pair = (_pc(key[0]), str(key[1]))
        except (TypeError, ValueError, IndexError) as exc:
            raise ValueError(
                f"key must be [tonic, mode] (mode 'major'|'minor'): {exc}"
            ) from exc
    return segment_to_chords(
        _canonical_sequence(events),
        key=key_pair,
        subdivisions=int(subdivisions),
        min_pc_weight=float(min_pc_weight),
        downbeat_emphasis=float(downbeat_emphasis),
    ).to_dict()


def combine_rulesets(
    rulesets: list[dict], name: str, version: str, description: str = ""
) -> dict:
    """Union several ruleset documents (Phase 4.6 DSL) into one named, versioned
    ruleset. Identical same-id rules are deduplicated; rules sharing an id but
    differing in definition raise (use specialize_ruleset to let one override).
    Returns the combined ruleset as a DSL document."""
    from ..rules import combine, ruleset_to_payload

    return ruleset_to_payload(
        combine(rulesets, name=name, version=version, description=description)
    )


def specialize_ruleset(
    base: dict,
    overlay: dict,
    name: str,
    version: str,
    description: str = "",
) -> dict:
    """Overlay one ruleset onto a base (Phase 4.6 DSL): same-id overlay rules
    replace base rules (base order preserved), new overlay rules append — the
    'a style = common-practice + these overrides' move. Returns
    {ruleset_payload, overridden: [ids replaced], added: [new ids]}."""
    from ..rules import specialize

    return specialize(
        base, overlay, name=name, version=version, description=description
    ).to_dict()


def compare_rulesets(ruleset_a: dict, ruleset_b: dict) -> dict:
    """Structurally diff two ruleset documents (Phase 4.6 DSL): shared_ids (same
    id + definition), conflicting_ids (same id, different definition),
    only_in_a / only_in_b, and contradictions (rule pairs that cannot both hold
    — same family+filter+check, one forbids what the other requires)."""
    from ..rules import compare

    return compare(ruleset_a, ruleset_b).to_dict()


def voice_leading_distance(source_pcs: list[int], target_pcs: list[int]) -> dict:
    """Minimal voice-leading distance between two pc sets, with the optimal
    voice mapping as evidence."""
    return voice_leading(source_pcs, target_pcs).to_dict()


def realized_voice_leading(source_midi: list[int], target_midi: list[int]) -> dict:
    """Register-aware minimal voice leading between two voiced chords (actual
    MIDI notes; octaves cost 12, doublings are voices), with the optimal
    [from_midi, to_midi] mapping as evidence."""
    from ..analysis import voice_leading_realized

    return voice_leading_realized(
        _realization(source_midi), _realization(target_midi)
    ).to_dict()


# --- register-aware & generative ------------------------------------------------------------

def voicing_analysis(midi_notes: list[int], root: int | str | None = None) -> dict:
    """Register-aware analysis of actual sounding notes (inversion, spacing,
    recognized voicing type). Requires real notes — register is never invented."""
    realization = _realization(midi_notes, root)
    if realization is None:
        raise ValueError("voicing_analysis needs at least one MIDI note.")
    return analyze_voicing(realization).to_dict()


def voicing_suggestions(root: int | str, quality: str) -> dict:
    """GENERATIVE: invent candidate voicings (closed, drop-2/3, rootless, shell)
    for a chord identity."""
    chord = Chord.from_quality(_pc(root), _quality(quality))
    return suggest_voicings(chord).to_dict()


def search_voicings(
    pcs: list[int],
    root: int | None = None,
    constraints: dict | None = None,
    from_voicing: list[int] | None = None,
    limit: int | None = None,
) -> dict:
    """GENERATIVE: exhaustively enumerate every registered voicing of a pc-set
    inside a MIDI window, under spacing/bass/smoothness constraints (gap 17).

    constraints MUST include register: [lo, hi] (inclusive MIDI window) — the
    engine never invents a default register; bounding the space is the caller's
    generative choice. Optional fields: spread / top_midi (ints, full ops),
    bass_pc / top_pc (0-11), center (float, gte/lte), voicing_type (named shape
    closed/drop2/…, needs root), no_interval_over_bass (directed pc-intervals
    1-11 forbidden above the bass), max_voice_leading (needs from_voicing).

    Each pc is voiced exactly once (slice 1 — no doublings). root=None searches
    voicing TEMPLATES (registered+rootless; shape labels skipped). With
    from_voicing, every match carries vl_from (exact realized VL cost,
    doubling.1) and matches come back RANKED by it; without, ordered by
    (spread, pitches). count is always the true total (limit only cuts the
    reported list; an over-large window raises with advice instead of silently
    truncating). Invalid input raises ValueError listing EVERY problem."""
    return _search_voicings(
        pcs,
        root=root,
        constraints=constraints if constraints is not None else {},
        from_voicing=from_voicing,
        limit=limit,
    ).to_dict()


# --- comparison & summary ----------------------------------------------------------------------

def quality_comparison(quality_a: str, quality_b: str) -> dict:
    """Compare two chord qualities across the scale catalog (shared scales,
    placements, unique fits)."""
    return compare_chord_qualities(_quality(quality_a), _quality(quality_b)).to_dict()


def quality_brief(quality: str) -> dict:
    """Compact brief for a chord quality: interval fingerprint, top compatible
    scales, functional roles."""
    return chord_brief(_quality(quality)).to_dict()


# --- representation (Phase 5: projections as data) -----------------------------------

def keyboard_view(
    low_midi: int = 48,
    high_midi: int = 84,
    tonic: int | str | None = None,
    scale_name: str | None = None,
    active_midi: list[int] | None = None,
    active_pcs: list[int] | None = None,
) -> dict:
    """Render-agnostic keyboard/piano descriptor: per key — midi, pc, octave,
    black/white topology, scale membership + degree index + tonic flag (when
    tonic+scale_name give a context; no context, no claim), and activation.
    active_midi lights exact keys (register); active_pcs lights every octave
    of those pcs (a declared octave-invariant projection — the result's
    spec_level says which was used); both together is an error. Numeric only:
    labels, spelling, and colors are the renderer's business."""
    from ..representation import keyboard_descriptor

    if (scale_name is None) != (tonic is None):
        raise ValueError(
            "A tonal context needs both tonic and scale_name; supply both or neither."
        )
    scale = _scale(scale_name) if scale_name is not None else None
    return keyboard_descriptor(
        int(low_midi),
        int(high_midi),
        tonic_pc=_pc(tonic) if tonic is not None else None,
        scale=scale,
        active_midi=active_midi,
        active_pcs=active_pcs,
    ).to_dict()


def bracelet_view(
    pcs: list[int],
    tonic: int | str | None = None,
    scale_name: str | None = None,
) -> dict:
    """Render-agnostic pitch-class clock (bracelet) descriptor: the 12 ring
    positions with the active set flagged (and scale-backdrop membership when
    tonic+scale_name give a context), plus the active set's symmetry — its
    reflection axes (pc-unit centers) and rotational order — and its interval
    vector. Register-less (spec_level "identity_only"); numeric only."""
    from ..representation import bracelet_descriptor

    if (scale_name is None) != (tonic is None):
        raise ValueError(
            "A backdrop scale needs both tonic and scale_name; supply both or neither."
        )
    scale = _scale(scale_name) if scale_name is not None else None
    return bracelet_descriptor(
        [int(pc) for pc in pcs],
        tonic_pc=_pc(tonic) if tonic is not None else None,
        scale=scale,
    ).to_dict()


def tonnetz_view(pcs: list[int]) -> dict:
    """Render-agnostic Tonnetz descriptor: all 12 pitch classes at their
    canonical lattice coordinates (fifths/major-thirds/minor-thirds from C)
    with the active set flagged, the P5/M3/m3 EDGES among active pcs (the lit
    triangles a Tonnetz reads as triads), and the active centroid. Edges come
    from pitch-class interval (P5=5/7, M3=4/8, m3=3/9). Register-less; numeric
    only — the renderer projects the integer coordinates to its own plane."""
    from ..representation import tonnetz_descriptor

    return tonnetz_descriptor([int(pc) for pc in pcs]).to_dict()


def colour_content_view(pcs: list[int]) -> dict:
    """Render-agnostic colour-content descriptor (Audiology brief-15): the two
    resultant vectors behind the somatic-colour wheels, as numeric data — map
    each resultant's angle → hue, focus → saturation. `interval_content` is the
    root-blind, transposition-INVARIANT interval-colour (ic1..ic5 on a fixed
    pentagon, tritone central, normalized so focus ∈ [0,1]; inversional pairs
    collapse — maj=min, dom7=m7♭5). `fifths_centroid` is the root-aware,
    transposition-VARIANT circle-of-fifths centroid (= f5/n: angle arg(f5), focus
    |f5|/n). The interval vector + the fixed `rim_layout` ride along. Unlike the
    clock view the rim geometry is engine-fixed (the resultant angle IS the
    determination). Register-less; hue/OKLCH stays the consumer's rendering."""
    from ..representation import colour_content_descriptor

    return colour_content_descriptor([int(pc) for pc in pcs]).to_dict()


def tonal_orientation_view(midi_notes: list[int], octave_decay: float = 1.0) -> dict:
    """Register-aware tonal-orientation angle of a VOICING (Audiology brief-17):
    a continuous fifths-space angle that varies with voicing (inversion, spread,
    doublings) — map angle_radians → hue for a voicing-responsive colour. Each
    sounding pitch is placed at its circle-of-fifths angle and summed with a
    register weight (octave_decay per octave above the bass: 1.0 = uniform, <1
    weights the bass more so inversion/spread shift the angle). Reduces to the
    pc-level arg(f5) for a neutral closed voicing; rotates predictably under
    transposition. midi_notes: the sounding MIDI pitches (register-REQUIRED — a
    pc-set has no voicing to orient). Hue/OKLCH stays the consumer's rendering."""
    from ..representation import tonal_orientation

    return tonal_orientation(
        [int(m) for m in midi_notes], octave_decay=float(octave_decay)
    ).to_dict()


def chord_network(chords: list[list], max_distance: int = 2) -> dict:
    """Voice-leading network over a chord vocabulary (Phase 5): nodes (each
    chord + pcs + rotational period — augmented/dim hubs stand out by their
    low period) and undirected edges between chords whose voice-leading
    distance is <= max_distance, each edge carrying distance, common-tone
    count, and root interval. The render-agnostic form of the Cube-Dance
    parsimony mandala; every edge is the engine's exact voice_leading
    relation. chords: ordered [root, quality] pairs (root = note name or pc;
    quality = a catalog name). Register-less; numeric only. (The functional
    V7->I resolution arrows are a separate directed/key-relative layer, not
    this voice-leading graph.)"""
    from ..representation import chord_network_descriptor

    try:
        parsed = [(_pc(entry[0]), _quality(str(entry[1]))) for entry in chords]
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError(
            f"Each chord must be [root, quality] (root = note name or pc; "
            f"quality = a catalog name): {exc}"
        ) from exc
    return chord_network_descriptor(parsed, max_distance=int(max_distance)).to_dict()


# --- the A1 pipeline ------------------------------------------------------------------------------

def midi_file_analysis(
    path: str,
    infer_context: bool = True,
    include_key_regions: bool = True,
    coalesce_window_beats: float | None = None,
    per_region_context: bool = True,
    disambiguate_relative_keys: bool = False,
    smooth_key_regions: bool = False,
    profile_version: str | None = None,
    key_inertia: bool = False,
    include_meter_regions: bool = False,
) -> dict:
    """Analyze a Standard MIDI File end-to-end: segment it, infer the global key,
    and emit the enriched dataset (per-segment identity, namings, placement).

    When infer_context is true, segment namings are conditional on the local
    key region containing each segment's onset (the region's mean_margin
    rides on the record's context snapshot as confidence); set
    per_region_context=false for the old single-global-key conditioning.
    The full ranked global key result is returned alongside either way.
    When include_key_regions is true, "key_regions" carries the windowed
    tracking result (null if no window carries tonal information). For
    performed/humanized files, set coalesce_window_beats (e.g. 0.05) to
    coalesce near-simultaneous timing before analysis — off by default, and
    cited in the result under "coalesce" when used (losses itemized).
    Set disambiguate_relative_keys=true to apply the relative-major/minor
    tie-breaker to both the global key context and the per-window tracking
    (off by default): better relative-key readings where correlation alone is
    weak. The global "key" induction is returned unchanged; when the flag is on
    the tie-break is surfaced under "key_disambiguation". Set
    smooth_key_regions=true to absorb short, low-confidence key-region blips
    (off by default; versioned hysteresis, cited on the tracking result).
    profile_version selects the versioned key-profile set for both the global
    induction and the per-window tracking (default kk-1982.1; 'tkp-cbms.1' the
    opt-in Temperley-Kostka-Payne alternative — better-balanced for major keys,
    A6 brief-9). Set include_meter_regions=true to also infer the LOCAL meter from
    note content (off by default): "meter_regions" carries the windowed
    meter-tracking result (time-signature regions with beats+seconds extents and
    per-window evidence; null if no window carries metric information). Inferred
    from onsets/accents and independent of the file's declared meter map — compare
    them to spot a mis-tagged or changing meter."""
    from ..dataset.pipelines import analyze_midi_file

    return analyze_midi_file(
        path,
        infer_context=bool(infer_context),
        include_key_regions=bool(include_key_regions),
        coalesce_window_beats=coalesce_window_beats,
        per_region_context=bool(per_region_context),
        disambiguate_relative_keys=bool(disambiguate_relative_keys),
        smooth_key_regions=bool(smooth_key_regions),
        profiles=_profiles(profile_version),
        key_inertia=bool(key_inertia),
        include_meter_regions=bool(include_meter_regions),
    ).to_dict()


def piano_roll_view(
    path: str,
    chord_overlays: bool = True,
    track_local_keys: bool = True,
    coalesce_window_beats: float | None = None,
    disambiguate_relative_keys: bool = False,
    smooth_key_regions: bool = False,
) -> dict:
    """Render-ready piano-roll descriptor for a Standard MIDI File (Phase 5):
    per-note rectangles (midi/pc/voice/velocity, onset+duration in BOTH beats
    and seconds), segmented chord-region overlays with the contextually-chosen
    chord name (conditioned on the local key per onset when track_local_keys),
    and local-key backdrop bands. Chord-overlay names match midi_file_analysis
    byte-for-byte (same builder). Set coalesce_window_beats (e.g. 0.05) to
    repair performed timing first. Set disambiguate_relative_keys=true to apply
    the relative-major/minor tie-breaker to the key backdrop (matches
    midi_file_analysis under the same flag); smooth_key_regions=true absorbs
    short low-confidence key-band blips (both off by default). Numeric only —
    labels/colors are the renderer's business."""
    from ..dataset.pipelines import piano_roll_view_from_file

    return piano_roll_view_from_file(
        path,
        chord_overlays=bool(chord_overlays),
        track_local_keys=bool(track_local_keys),
        coalesce_window_beats=coalesce_window_beats,
        disambiguate_relative_keys=bool(disambiguate_relative_keys),
        smooth_key_regions=bool(smooth_key_regions),
    ).to_dict()


TOOLS = (
    list_scales,
    list_chord_qualities,
    parse_chord,
    chord_analysis,
    scale_analysis,
    set_class_info,
    interpretations,
    catalog_containment,
    search_identities,
    chord_in_key,
    name_pcs,
    key_induction,
    relative_key,
    meter_estimation,
    meter_tracking,
    key_tracking,
    structural_keys,
    cadences,
    next_chord,
    melodic_tendency,
    name_pcs_in_inferred_keys,
    voice_leading_distance,
    voice_pair_motion,
    melodic_analysis,
    rhythmic_analysis,
    swing_analysis,
    coalesce_events,
    extract_groove,
    apply_groove,
    validate_ruleset,
    evaluate_ruleset,
    ruleset_field_manifest,
    list_named_rulesets,
    load_named_ruleset,
    induce_rules,
    transition_matrix,
    segment_chords,
    combine_rulesets,
    specialize_ruleset,
    compare_rulesets,
    keyboard_view,
    bracelet_view,
    tonnetz_view,
    colour_content_view,
    tonal_orientation_view,
    chord_network,
    realized_voice_leading,
    voicing_analysis,
    voicing_suggestions,
    search_voicings,
    quality_comparison,
    quality_brief,
    midi_file_analysis,
    piano_roll_view,
)

__all__ = [fn.__name__ for fn in TOOLS] + ["TOOLS"]
