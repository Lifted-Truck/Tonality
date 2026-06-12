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
from ..io.loaders import load_chord_qualities, load_scales


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


def key_induction(pc_weights: list[float]) -> dict:
    """Ranked key candidates for duration-weighted pitch-class content
    (12 weights, index = pc). All 24 candidates, scores, and the top-two margin."""
    return infer_key(pc_weights).to_dict()


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


def key_tracking(
    events: list[list[float]],
    window_beats: float = 8.0,
    hop_beats: float = 2.0,
    bpm: float = 120.0,
) -> dict:
    """Local key tracking: key regions through time for a list of events, each
    [onset_beats, duration_beats, midi_note]. Windowed key induction (same
    versioned profiles); regions carry beats+seconds extents, mean score/margin,
    and the per-window evidence. Boundary resolution is the window grid."""
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
        sequence, window_beats=window_beats, hop_beats=hop_beats
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


# --- the A1 pipeline ------------------------------------------------------------------------------

def midi_file_analysis(
    path: str, infer_context: bool = True, include_key_regions: bool = True
) -> dict:
    """Analyze a Standard MIDI File end-to-end: segment it, infer the global key,
    and emit the enriched dataset (per-segment identity, namings, placement).

    When infer_context is true, the best inferred key becomes the analytical
    context every segment's naming is conditional on; the full ranked key
    result is returned alongside either way. When include_key_regions is true,
    local key tracking adds "key_regions" (windowed; null if no window carries
    tonal information).
    """
    from ..analysis import candidate_context
    from ..io.midi import sequence_from_midi_file
    from ..temporal import track_keys

    sequence = sequence_from_midi_file(path)
    keys = infer_key(sequence)
    context = candidate_context(keys.best) if infer_context else None
    dataset = dataset_from_sequence(sequence, analytical_context=context)
    result = {"key": keys.to_dict(), "dataset": dataset.to_dict()}
    if include_key_regions:
        try:
            result["key_regions"] = track_keys(sequence).to_dict()
        except ValueError:
            result["key_regions"] = None  # no window carried tonal information
    return result


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
    key_tracking,
    name_pcs_in_inferred_keys,
    voice_leading_distance,
    voice_pair_motion,
    melodic_analysis,
    rhythmic_analysis,
    swing_analysis,
    realized_voice_leading,
    voicing_analysis,
    voicing_suggestions,
    quality_comparison,
    quality_brief,
    midi_file_analysis,
)

__all__ = [fn.__name__ for fn in TOOLS] + ["TOOLS"]
