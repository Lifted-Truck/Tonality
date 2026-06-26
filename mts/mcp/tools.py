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

import dataclasses

from ..analysis import (
    AnalyticalContext,
    ChordAnalysisRequest,
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
from ..core.bitmask import mask_from_pcs
from ..core.chord import Chord
from ..core.enharmonics import pc_from_name
from ..core.pitch import Pitch
from ..core.realization import Realization
from ..core.symmetry import mask_symmetry_order
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
    return dataclasses.asdict(parse_chord_spec(text))


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
    DFT magnitudes, rotational symmetry."""
    mask = mask_from_pcs({int(pc) % 12 for pc in pcs})
    if mask == 0:
        raise ValueError("set_class_info needs at least one pitch class.")
    data = dataclasses.asdict(set_class_data(mask))
    data["rotational_symmetry_order"] = mask_symmetry_order(mask)
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
    events: list[list[float]],
    bpm: float = 120.0,
    numerator: int = 4,
    denominator: int = 4,
) -> dict:
    """Infer the time signature from note content — ranked candidate signatures
    with scores + margin, and a declared-vs-estimated disagreement flag. Each
    candidate's score combines bar-period autocorrelation (does the content
    repeat each bar?) with metric-profile correlation (does the within-bar
    accent match the meter's template — distinguishing e.g. 3/4 from 6/8);
    templates are a versioned prior (meter-grid.1, cited). The engine NEVER
    overrides the file's meter — numerator/denominator set the declared meter
    and `agrees_with_declared` evidences against it. events: each [onset_beats,
    duration_beats, midi_note] or [..., velocity] (velocity at index 3 weights
    the accent). Raises on too few onsets or content with no metric information."""
    from ..analysis import infer_meter
    from ..temporal import Event, Sequence

    try:
        parsed = tuple(
            Event(
                float(e[0]), float(e[1]),
                Pitch.from_midi(int(e[2]),
                                velocity=int(e[3]) if len(e) > 3 and e[3] is not None else None),
            )
            for e in events
        )
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError(
            "Each event must be [onset_beats, duration_beats, midi_note] with "
            f"optional velocity (index 3): {exc}"
        ) from exc
    sequence = Sequence.from_events(
        parsed, bpm=float(bpm), time_signature=(int(numerator), int(denominator))
    )
    return infer_meter(sequence).to_dict()


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
    (default = core triads + sevenths). The historical/corpus tags are a planned
    follow-on (ROADMAP gap 14)."""
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
    ).to_dict()


def key_tracking(
    events: list[list[float]],
    window_beats: float = 8.0,
    hop_beats: float = 2.0,
    bpm: float = 120.0,
    disambiguate_relative: bool = False,
    smoothing: bool = False,
    profile_version: str | None = None,
    key_inertia: bool = False,
) -> dict:
    """Local key tracking: key regions through time for a list of events, each
    [onset_beats, duration_beats, midi_note]. Windowed key induction (same
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

    try:
        parsed = tuple(
            Event(float(onset), float(duration), Pitch.from_midi(int(midi)))
            for onset, duration, midi in events
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Each event must be [onset_beats, duration_beats, midi_note]: {exc}"
        ) from exc
    sequence = Sequence.from_events(parsed, bpm=float(bpm))
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
    events: list[list[float]],
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
    the file's meter/key. events: each [onset_beats, duration_beats, midi_note]
    or [..., voice]. disambiguate_relative/smoothing choose the underlying local
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

    try:
        parsed = tuple(
            Event(float(onset), float(duration), Pitch.from_midi(int(midi)),
                  voice=str(entry[3]) if len(entry) > 3 and entry[3] is not None else None)
            for entry in events
            for onset, duration, midi in [entry[:3]]
        )
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError(
            f"Each event must be [onset_beats, duration_beats, midi_note] (optional voice): {exc}"
        ) from exc
    sequence = Sequence.from_events(parsed, bpm=float(bpm))
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
    interval evidence) for voiced events, each [onset_beats, duration_beats,
    midi_note, voice_label]. The 'which voice moved' primitive counterpoint
    predicates filter — e.g. parallel fifths = motion 'parallel' with
    interval_class 7."""
    from ..temporal import Event, Sequence, voice_motion

    try:
        parsed = tuple(
            Event(
                float(onset),
                float(duration),
                Pitch.from_midi(int(midi)),
                voice=str(voice),
            )
            for onset, duration, midi, voice in events
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Each event must be [onset_beats, duration_beats, midi_note, voice_label]: {exc}"
        ) from exc
    return voice_motion(Sequence.from_events(parsed)).to_dict()


def melodic_analysis(
    events: list[list[float]],
    harmony: list[list] | None = None,
) -> dict:
    """Melodic atoms for one monophonic line: signed intervals, step/skip/leap
    classes, Parsons contour, ambitus, approach/departure per note — plus
    non-harmonic-tone typing (passing, neighbor, appoggiatura, escape,
    suspension, anticipation, pedal) when harmony is given. events: each
    [onset_beats, duration_beats, midi_note]. harmony (optional): spans
    [start_beat, end_beat, [pcs]] — without it no chord-tone claims are made."""
    from ..temporal import Event, Sequence, analyze_melody

    try:
        parsed = tuple(
            Event(float(onset), float(duration), Pitch.from_midi(int(midi)))
            for onset, duration, midi in events
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Each event must be [onset_beats, duration_beats, midi_note]: {exc}"
        ) from exc
    spans = None
    if harmony is not None:
        try:
            spans = [(float(s), float(e), [int(pc) for pc in pcs]) for s, e, pcs in harmony]
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Each harmony span must be [start_beat, end_beat, [pcs]]: {exc}"
            ) from exc
    return analyze_melody(Sequence.from_events(parsed), harmony=spans).to_dict()


def rhythmic_analysis(
    events: list[list[float]],
    numerator: int = 4,
    denominator: int = 4,
) -> dict:
    """Rhythmic atoms for one monophonic line: metric placement (downbeat /
    beat / offbeat / subdivision against the felt beat — compound meters
    beat in threes), a precise syncopation predicate (a weak onset sounding
    through the next stronger grid line), durations and inter-onset
    intervals. events: each [onset_beats, duration_beats, midi_note];
    numerator/denominator set a constant time signature (full meter maps via
    the library door)."""
    from ..temporal import Event, Sequence, analyze_rhythm

    try:
        parsed = tuple(
            Event(float(onset), float(duration), Pitch.from_midi(int(midi)))
            for onset, duration, midi in events
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Each event must be [onset_beats, duration_beats, midi_note]: {exc}"
        ) from exc
    sequence = Sequence.from_events(
        parsed, time_signature=(int(numerator), int(denominator))
    )
    return analyze_rhythm(sequence).to_dict()


def swing_analysis(
    events: list[list[float]],
    numerator: int = 4,
    denominator: int = 4,
) -> dict:
    """Swing-feel estimate for a monophonic line with symbolically-encoded
    timing: measures where each two-way beat division places its interior
    onset (0.5 = straight, 2/3 = triplet swing 2:1, 0.75 = dotted shuffle
    3:1, < 0.5 = reversed) and classifies the feel under a versioned prior
    cited in the result. Raises when there are too few divisions to claim a
    feel. events: each [onset_beats, duration_beats, midi_note]. NOTE:
    quantized-straight MIDI carries no swing to measure — swing must be in
    the onsets themselves."""
    from ..temporal import Event, Sequence, analyze_swing

    try:
        parsed = tuple(
            Event(float(onset), float(duration), Pitch.from_midi(int(midi)))
            for onset, duration, midi in events
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Each event must be [onset_beats, duration_beats, midi_note]: {exc}"
        ) from exc
    sequence = Sequence.from_events(
        parsed, time_signature=(int(numerator), int(denominator))
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
    hidden. events: each [onset_beats, duration_beats, midi_note] or
    [..., voice_label]. The engine never coalesces implicitly; exact input
    stays exact unless you call this."""
    from ..temporal import coalesce

    result = coalesce(
        _flex_events(events),
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

def _vel_events(events: list[list]) -> "Sequence":
    """Events as [onset, duration, midi, velocity?] or [..., velocity, voice].

    Distinct from ``_flex_events``: velocity is at index 3 (``None``/omitted =
    no velocity) and voice is promoted to index 4 — the groove tools need
    per-note velocity, which the [.., voice]-at-index-3 convention can't carry.
    """
    from ..temporal import Event, Sequence

    try:
        parsed = tuple(
            Event(
                float(entry[0]),
                float(entry[1]),
                Pitch.from_midi(
                    int(entry[2]),
                    velocity=(
                        int(entry[3]) if len(entry) > 3 and entry[3] is not None else None
                    ),
                ),
                voice=str(entry[4]) if len(entry) > 4 and entry[4] is not None else None,
            )
            for entry in events
        )
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError(
            "Each event must be [onset_beats, duration_beats, midi_note] with "
            f"optional velocity (index 3) and voice (index 4): {exc}"
        ) from exc
    return Sequence.from_events(parsed)


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
    — pass it explicitly for a clean loop. events: each [onset_beats,
    duration_beats, midi_note] with optional velocity (index 3) and voice
    (index 4)."""
    from ..temporal import extract_groove as _extract

    template = _extract(
        _vel_events(events),
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
    template is the dict returned by extract_groove. events: each [onset_beats,
    duration_beats, midi_note] with optional velocity (index 3) and voice
    (index 4); the result echoes velocity at index 3 (and voice at index 4 if
    present) plus the cited parameters and what changed."""
    from ..temporal import GrooveTemplate, apply_groove as _apply

    result = _apply(
        _vel_events(events),
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

def _flex_events(events: list[list]) -> "Sequence":
    """Events as [onset, duration, midi] or [onset, duration, midi, voice]."""
    from ..temporal import Event, Sequence

    try:
        parsed = tuple(
            Event(
                float(entry[0]),
                float(entry[1]),
                Pitch.from_midi(int(entry[2])),
                voice=str(entry[3]) if len(entry) > 3 and entry[3] is not None else None,
            )
            for entry in events
        )
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError(
            "Each event must be [onset_beats, duration_beats, midi_note] or "
            f"[onset_beats, duration_beats, midi_note, voice_label]: {exc}"
        ) from exc
    return Sequence.from_events(parsed)


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
) -> dict:
    """Evaluate a ruleset (Phase 4.6 DSL) against events — each [onset_beats,
    duration_beats, midi_note] or [..., voice_label] — returning a
    ConformanceReport: per-rule violations with locations and atom evidence,
    conformance frequencies, hard/soft rollups. Rules referencing
    harmony-dependent fields (nht_type, is_chord_tone) need harmony spans
    [start_beat, end_beat, [pcs]] and are reported not-applicable without
    them. Invalid rulesets raise with the full error list (use
    validate_ruleset first)."""
    from ..rules import evaluate

    spans = None
    if harmony is not None:
        try:
            spans = [(float(s), float(e), [int(pc) for pc in pcs]) for s, e, pcs in harmony]
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Each harmony span must be [start_beat, end_beat, [pcs]]: {exc}"
            ) from exc
    return evaluate(ruleset, _flex_events(events), harmony=spans).to_dict()


def induce_rules(
    corpus: list[list[list]],
    family: str,
    harmony: list[list[list]] | None = None,
    scoring_prior: str | None = None,
    merge_disjunctions: bool = True,
) -> dict:
    """Mine a corpus for the statistically significant compositional rules it
    follows (Phase 4.6 induction), emitting a validated SOFT ruleset in the DSL
    plus per-rule evidence (support, confidence, leverage, Fisher p-value,
    BH-FDR q-value). Apriori frequent-pattern mining over the where-lattice
    (closed itemsets, arity cap 3) + Fisher's exact test vs an
    independence-given-marginals null, BH-FDR at q=0.05; weights are a versioned
    scoring prior cited in the result. corpus: a list of pieces, each a list of
    [onset_beats, duration_beats, midi_note] (or [..., voice_label] — voices
    needed for the voice_motion family). family: 'voice_motion' | 'melody' |
    'rhythm'. harmony: optional per-piece list of [start_beat, end_beat, [pcs]]
    spans (only melody's nht_type/is_chord_tone consult it). Below ~30 pieces
    the result is flagged exploratory. merge_disjunctions (default true)
    collapses same-(where, field) single-value rules into one `in`-rule
    (forbid ic in {0,7} rather than two forbids), re-tested with Fisher — the
    human-readable form; set false for the raw single-value rules. The emitted
    ruleset round-trips through the validator."""
    from ..rules import induce_ruleset

    pieces = [_flex_events(piece) for piece in corpus]
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
    return dataclasses.asdict(suggest_voicings(chord))


# --- comparison & summary ----------------------------------------------------------------------

def quality_comparison(quality_a: str, quality_b: str) -> dict:
    """Compare two chord qualities across the scale catalog (shared scales,
    placements, unique fits)."""
    return dataclasses.asdict(
        compare_chord_qualities(_quality(quality_a), _quality(quality_b))
    )


def quality_brief(quality: str) -> dict:
    """Compact brief for a chord quality: interval fingerprint, top compatible
    scales, functional roles."""
    return dataclasses.asdict(chord_brief(_quality(quality)))


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


def chord_network(chords: list[list], max_distance: int = 2) -> dict:
    """Voice-leading network over a chord vocabulary (Phase 5): nodes (each
    chord + pcs + rotational symmetry — augmented/dim hubs stand out by their
    symmetry order) and undirected edges between chords whose voice-leading
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
    A6 brief-9)."""
    from ..analysis import candidate_context, disambiguate_relative_key
    from ..io.midi import sequence_from_midi_file
    from ..temporal import coalesce, track_keys

    sequence = sequence_from_midi_file(path)
    profiles = _profiles(profile_version)
    coalesce_meta = None
    if coalesce_window_beats is not None:
        cleaned = coalesce(sequence, onset_window_beats=float(coalesce_window_beats))
        sequence = cleaned.sequence
        coalesce_meta = cleaned.to_dict()
    keys = infer_key(sequence, profiles=profiles)
    best = keys.best
    disambiguation = None
    if disambiguate_relative_keys:
        disambiguation = disambiguate_relative_key(keys)
        if disambiguation.applied and not disambiguation.is_ambiguous:
            best = disambiguation.chosen
    context = candidate_context(best) if infer_context else None

    regions = None
    if include_key_regions or (per_region_context and infer_context):
        try:
            regions = track_keys(
                sequence,
                disambiguate_relative=bool(disambiguate_relative_keys),
                smoothing=bool(smooth_key_regions),
                profiles=profiles,
                key_inertia=bool(key_inertia),
            )
        except ValueError:
            regions = None  # no window carried tonal information

    dataset = dataset_from_sequence(
        sequence,
        analytical_context=context,
        key_regions=regions if (per_region_context and infer_context) else None,
    )
    result = {"key": keys.to_dict(), "dataset": dataset.to_dict()}
    if coalesce_meta is not None:
        result["coalesce"] = coalesce_meta
    if disambiguation is not None:
        result["key_disambiguation"] = disambiguation.to_dict()
    if include_key_regions:
        result["key_regions"] = regions.to_dict() if regions is not None else None
    return result


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
    from ..analysis import candidate_context, disambiguate_relative_key
    from ..io.midi import sequence_from_midi_file
    from ..representation import piano_roll_descriptor
    from ..temporal import coalesce, track_keys

    sequence = sequence_from_midi_file(path)
    if coalesce_window_beats is not None:
        sequence = coalesce(
            sequence, onset_window_beats=float(coalesce_window_beats)
        ).sequence

    regions = None
    context = None
    if track_local_keys:
        try:
            regions = track_keys(
                sequence,
                disambiguate_relative=bool(disambiguate_relative_keys),
                smoothing=bool(smooth_key_regions),
            )
        except ValueError:
            regions = None  # no window carried tonal information
    if regions is None and chord_overlays:
        try:
            best = infer_key(sequence)
            chosen = best.best
            if disambiguate_relative_keys:
                rel = disambiguate_relative_key(best)
                if rel.applied and not rel.is_ambiguous:
                    chosen = rel.chosen
            context = candidate_context(chosen)
        except ValueError:
            context = None  # no tonal information — intrinsic naming only

    return piano_roll_descriptor(
        sequence,
        analytical_context=context,
        key_regions=regions,
        chord_overlays=chord_overlays,
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
    chord_in_key,
    name_pcs,
    key_induction,
    relative_key,
    meter_estimation,
    key_tracking,
    structural_keys,
    cadences,
    next_chord,
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
    induce_rules,
    combine_rulesets,
    specialize_ruleset,
    compare_rulesets,
    keyboard_view,
    bracelet_view,
    tonnetz_view,
    chord_network,
    realized_voice_leading,
    voicing_analysis,
    voicing_suggestions,
    quality_comparison,
    quality_brief,
    midi_file_analysis,
    piano_roll_view,
)

__all__ = [fn.__name__ for fn in TOOLS] + ["TOOLS"]
