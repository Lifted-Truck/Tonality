"""Next-chord recommendation: succession as ranked, tagged candidates (gap 14).

The plural-and-evidenced contract (Decision 7) applied to *succession*. Given a
key (major/minor) and a current chord (optionally a short history), enumerate the
key's functional chord vocabulary as candidate next chords and tag each
current→candidate transition with the music-theoretic context computable today,
then rank under a versioned scoring prior.

This is a **synthesis**, not greenfield — every signal reuses an existing engine
primitive:

- the **candidate set** + each chord's (role, roman) come from the same
  functional vocabulary the cadence detector uses
  (:func:`mts.io.loaders.load_function_mappings`);
- **functional-succession** tags come from roles + root motion, and the
  cadential formula of a transition is read straight from
  :func:`mts.analysis.cadence.detect_cadences` on the pair;
- **voice-leading** tags come from :func:`mts.analysis.voice_leading.voice_leading`
  (the chord-network edge, computed per candidate);
- **color-shift** is the Euclidean delta of the 6-D DFT magnitude fingerprint
  (:func:`mts.core.setclass.dft_magnitudes`) — reported as a neutral tension
  axis, not scored.

:func:`tag_transition` annotates a *single* current→candidate move (independently
useful to a progression annotator); :func:`recommend_next_chord` is the thin loop
over the key's vocabulary that ranks them.

Slice 1 (this module) ships the no-new-data tagged recommender. Deferred to
follow-on PRs (ROADMAP gap 14): the *historical* tags (per-style corpus
transition priors); **pure voice-leading-neighbour candidates** outside the
functional vocabulary (so chromatic-mediant *candidates* surface — the
`chromatic_mediant` tag is implemented and fires on any qualifying transition,
but the default candidate set is the diatonic+borrowed functional vocabulary,
which rarely contains one); and register-aware ranking.

Major/minor only, like the cadence detector: a modal key raises rather than
claim function it cannot ground.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Sequence

from ..core.bitmask import mask_from_pcs
from ..core.setclass import dft_magnitudes
from .results import (
    AnalyticalContextSnapshot,
    NextChordCandidate,
    NextChordRecommendation,
    SuccessionEvidence,
)
from ..io.loaders import load_chord_qualities, load_function_mappings, load_scales, load_succession_weights

_SUPPORTED_MODES = ("major", "minor")

# A legible default candidate vocabulary: triads + sevenths. The full generated
# vocabulary (sixths, add9s, extensions) is reachable via the ``qualities``
# override — a caller-set scope, cited in no prior.
CORE_QUALITIES = (
    "maj", "min", "dim", "aug",
    "maj7", "min7", "7", "min7b5", "dim7", "minmaj7",
)


def _role_table(mode: str) -> dict[tuple[int, str], tuple[str, str]]:
    """{(relative_root, quality): (role, roman)} for the mode (cadence's table)."""


    table: dict[tuple[int, str], tuple[str, str]] = {}
    for mapping in load_function_mappings(mode):
        table.setdefault(
            (mapping.degree_pc, mapping.chord_quality),
            (mapping.role, mapping.modal_label),
        )
    return table


def _diatonic_degrees(mode: str) -> frozenset[int]:
    """Relative pitch classes of the mode's reference scale (for applied dominants)."""


    scale_name = "Ionian" if mode == "major" else "Natural Minor"
    return frozenset(load_scales()[scale_name].degrees)


def _quality_intervals(quality: str) -> tuple[int, ...]:

    catalog = load_chord_qualities()
    if quality not in catalog:
        raise ValueError(
            f"Unknown chord quality {quality!r} — see list_chord_qualities for "
            "the catalog of valid names."
        )
    return catalog[quality].intervals


def _pcs(root_pc: int, intervals: Sequence[int]) -> list[int]:
    return sorted({(root_pc + iv) % 12 for iv in intervals})


def _is_dominant_quality(intervals: Sequence[int]) -> bool:
    """A major third and a minor seventh above the root — a dominant-type chord."""

    pcs = {iv % 12 for iv in intervals}
    return 4 in pcs and 10 in pcs


def _plr_detail(root_interval: int) -> str | None:
    """Neo-Riemannian sub-label for a parsimonious triad pair, where unambiguous."""

    if root_interval == 0:
        return "P (parallel: major↔minor on the same root)"
    if root_interval in (4, 8):
        return "L (leading-tone exchange: root moves a major third)"
    if root_interval in (3, 9):
        return "R (relative: root moves a minor third)"
    return None


def _score_transition(
    *,
    current_root: int,
    current_quality: str,
    current_pcs: list[int],
    current_dft: tuple[float, ...],
    current_role: str | None,
    cand_root: int,
    cand_quality: str,
    cand_intervals: Sequence[int],
    cand_role: str | None,
    cand_roman: str | None,
    cand_own_tags: set[str],
    tonic_pc: int,
    mode: str,
    diatonic: frozenset[int],
    weights: dict[str, float],
    history: list[tuple[int, str]],
) -> NextChordCandidate:
    """Tag + score one current→candidate transition (rank assigned by the caller)."""

    cand_pcs = _pcs(cand_root, cand_intervals)
    root_interval = (cand_root - current_root) % 12

    evidence: list[SuccessionEvidence] = []
    tags: set[str] = set()

    def fire(signal: str, *, scale: float = 1.0, detail: str | None = None) -> None:
        weight = weights.get(signal, 0.0) * scale
        tags.add(signal)
        evidence.append(SuccessionEvidence(signal=signal, weight=weight, detail=detail))

    # --- functional-succession (roles + root motion) ---
    if current_role is not None and current_role == cand_role:
        fire("prolongation", detail=f"both {cand_role}")
    if root_interval == 5:
        fire("descending_fifth", detail="root down a fifth")
    elif root_interval == 7:
        fire("ascending_fifth", detail="root up a fifth")
    elif root_interval in (1, 2, 10, 11):
        fire("step", detail="root by step")
    if current_role == "dominant" and cand_role == "tonic":
        fire("dominant_resolution", detail="dominant → tonic function")
    if current_role == "dominant" and cand_role == "predominant":
        fire("retrogression", detail="dominant → predominant")
    if (
        _is_dominant_quality(cand_intervals)
        and (cand_root - tonic_pc) % 12 != 7
        and ((cand_root + 5) - tonic_pc) % 12 in diatonic
        and ((cand_root + 5) - tonic_pc) % 12 != 0
    ):
        target_rel = ((cand_root + 5) - tonic_pc) % 12
        fire("applied_dominant", detail=f"resolves down a fifth to degree {target_rel}")
    for own in ("borrowed", "modal_mix"):
        if own in cand_own_tags:
            fire(own, detail="from the candidate's functional tag")
    if "vl_neighbour" in cand_own_tags:
        # Provenance: generated by smooth-voice-leading reachability, not the
        # functional vocabulary (weight 0 — informational, never scores).
        fire("vl_neighbour", detail="reachable by smooth voice-leading, outside the functional vocabulary")

    # --- cadential formula of this transition (history prepended) ---
    cadence_type = _transition_cadence(
        history, (current_root, current_quality),
        (cand_root, cand_quality), tonic_pc, mode,
    )
    if cadence_type is not None:
        fire(cadence_type, detail="cadential formula on this transition")

    # --- voice-leading ---
    from .voice_leading import voice_leading

    vl = voice_leading(current_pcs, cand_pcs)
    common = len(set(current_pcs) & set(cand_pcs))
    both_triads = len(current_pcs) == 3 and len(cand_pcs) == 3
    if vl.distance <= 2:
        fire("smooth", detail=f"voice-leading distance {vl.distance}")
    if common >= 1:
        fire("common_tone", scale=float(common), detail=f"{common} common tone(s)")
    if both_triads and common == 2 and vl.distance <= 2:
        fire("parsimonious", detail=_plr_detail(root_interval))
    elif (
        root_interval in (3, 4, 8, 9)
        and common == 1
        and both_triads
        and current_quality == cand_quality
    ):
        fire("chromatic_mediant", detail="same-quality triads a third apart")
    if vl.distance:
        fire("vl_distance", scale=float(vl.distance), detail=f"{vl.distance} semitones of motion")

    # --- color (reported, not scored) ---
    cand_dft = dft_magnitudes(mask_from_pcs(cand_pcs))
    color_shift = math.sqrt(sum((a - b) ** 2 for a, b in zip(current_dft, cand_dft)))

    score = sum(e.weight for e in evidence)
    return NextChordCandidate(
        root_pc=cand_root,
        quality=cand_quality,
        modal_label=cand_roman,
        role=cand_role,
        score=round(score, 6),
        rank=0,
        tags=tuple(sorted(tags)),
        vl_distance=vl.distance,
        common_tones=common,
        root_interval=root_interval,
        color_shift=round(color_shift, 6),
        cadence=cadence_type,
        evidence=evidence,
    )


def tag_transition(
    current: tuple[int, str],
    candidate: tuple[int, str],
    *,
    tonic_pc: int,
    mode: str,
    history: Sequence[tuple[int, str]] | None = None,
    weights_version: str | None = None,
) -> NextChordCandidate:
    """Tag + score one current→candidate transition in a key (rank is 0).

    The single-pair primitive behind :func:`recommend_next_chord` — annotate any
    transition (e.g. an edge of an existing progression), even when the
    candidate is outside the key's functional vocabulary (then ``role`` /
    ``modal_label`` are ``None``). Major/minor only.
    """

    if not 0 <= tonic_pc < 12:
        raise ValueError(f"tonic_pc out of range: {tonic_pc} (use 0-11).")
    mode_key = mode.lower()
    if mode_key not in _SUPPORTED_MODES:
        raise ValueError(
            f"Unsupported mode {mode!r}: succession tagging needs the functional "
            "vocabulary (major/minor only — modal keys are not guessed)."
        )


    weights = load_succession_weights(weights_version).weights
    table = _role_table(mode_key)
    diatonic = _diatonic_degrees(mode_key)

    current_root, current_quality = int(current[0]), str(current[1])
    current_pcs = _pcs(current_root, _quality_intervals(current_quality))
    current_dft = dft_magnitudes(mask_from_pcs(current_pcs))
    current_role, _ = table.get(((current_root - tonic_pc) % 12, current_quality), (None, None))

    cand_root, cand_quality = int(candidate[0]), str(candidate[1])
    cand_intervals = _quality_intervals(cand_quality)
    cand_role, cand_roman = table.get(((cand_root - tonic_pc) % 12, cand_quality), (None, None))

    return _score_transition(
        current_root=current_root,
        current_quality=current_quality,
        current_pcs=current_pcs,
        current_dft=current_dft,
        current_role=current_role,
        cand_root=cand_root,
        cand_quality=cand_quality,
        cand_intervals=cand_intervals,
        cand_role=cand_role,
        cand_roman=cand_roman,
        cand_own_tags=set(),
        tonic_pc=tonic_pc,
        mode=mode_key,
        diatonic=diatonic,
        weights=weights,
        history=[(int(r), str(q)) for r, q in (history or [])],
    )


def recommend_next_chord(
    current: tuple[int, str],
    *,
    tonic_pc: int,
    mode: str,
    history: Sequence[tuple[int, str]] | None = None,
    qualities: Sequence[str] | None = None,
    weights_version: str | None = None,
    vl_neighbours: bool = False,
    vl_max_distance: int = 3,
) -> NextChordRecommendation:
    """Rank tagged candidate next chords from ``current`` in a key.

    ``current`` is ``(root_pc, quality_name)``; ``mode`` is ``"major"`` or
    ``"minor"`` (others raise — function is not guessed). ``history`` is an
    optional preceding ``(root, quality)`` progression, prepended for cadential
    context. ``qualities`` overrides the default core candidate vocabulary.
    Set ``vl_neighbours=True`` to *also* generate voice-leading-neighbour
    candidates — chords reachable within ``vl_max_distance`` semitones of total
    motion but outside the key's functional vocabulary (so chromatic mediants and
    other parsimonious moves surface as candidates, tagged ``vl_neighbour``).
    Raises ``ValueError`` on an out-of-range tonic or an unsupported mode.
    """

    if not 0 <= tonic_pc < 12:
        raise ValueError(f"tonic_pc out of range: {tonic_pc} (use 0-11).")
    mode_key = mode.lower()
    if mode_key not in _SUPPORTED_MODES:
        raise ValueError(
            f"Unsupported mode {mode!r}: next-chord recommendation needs the "
            "functional vocabulary (major/minor only — modal keys are not "
            "guessed)."
        )


    prior = load_succession_weights(weights_version)
    weights = prior.weights
    table = _role_table(mode_key)
    diatonic = _diatonic_degrees(mode_key)
    allowed = set(qualities) if qualities is not None else set(CORE_QUALITIES)

    current_root, current_quality = int(current[0]), str(current[1])
    current_pcs = _pcs(current_root, _quality_intervals(current_quality))
    current_dft = dft_magnitudes(mask_from_pcs(current_pcs))
    current_rel = (current_root - tonic_pc) % 12
    current_role, current_roman = table.get((current_rel, current_quality), (None, None))
    history_pairs = [(int(r), str(q)) for r, q in (history or [])]

    # Candidate vocabulary: the key's functional mappings (incl. borrowed),
    # filtered to the allowed qualities, deduped by absolute (root, quality).
    seen: dict[tuple[int, str], dict] = {}
    for mapping in load_function_mappings(mode_key, include_borrowed=True):
        if mapping.chord_quality not in allowed:
            continue
        abs_root = (tonic_pc + mapping.degree_pc) % 12
        key = (abs_root, mapping.chord_quality)
        if key in seen:
            seen[key]["tags"].update(mapping.tags)
            continue
        seen[key] = {
            "root_pc": abs_root,
            "quality": mapping.chord_quality,
            "intervals": mapping.intervals,
            "role": mapping.role,
            "roman": mapping.modal_label,
            "tags": set(mapping.tags),
        }

    # Opt-in: also generate **voice-leading-neighbour** candidates — chords
    # reachable from `current` within `vl_max_distance` semitones of total motion
    # but *outside* the functional vocabulary (gap 14). This is what surfaces
    # chromatic mediants etc. as candidates (the `chromatic_mediant` tag fires on
    # them once they exist). Role/roman come from the table if the chord happens to
    # be functional, else None (out-of-vocabulary, named honestly). The smoothness
    # bound is caller geometry (cited here, no prior); they carry a `vl_neighbour`
    # provenance tag.
    if vl_neighbours:
        from .voice_leading import voice_leading

        for quality in sorted(allowed):
            intervals = _quality_intervals(quality)
            for abs_root in range(12):
                key = (abs_root, quality)
                if key == (current_root, current_quality) or key in seen:
                    continue
                cand_pcs = _pcs(abs_root, intervals)
                if voice_leading(current_pcs, cand_pcs).distance > vl_max_distance:
                    continue
                rel = (abs_root - tonic_pc) % 12
                role, roman = table.get((rel, quality), (None, None))
                seen[key] = {
                    "root_pc": abs_root,
                    "quality": quality,
                    "intervals": intervals,
                    "role": role,
                    "roman": roman,
                    "tags": {"vl_neighbour"},
                }

    candidates = [
        _score_transition(
            current_root=current_root,
            current_quality=current_quality,
            current_pcs=current_pcs,
            current_dft=current_dft,
            current_role=current_role,
            cand_root=info["root_pc"],
            cand_quality=info["quality"],
            cand_intervals=info["intervals"],
            cand_role=info["role"],
            cand_roman=info["roman"],
            cand_own_tags=info["tags"],
            tonic_pc=tonic_pc,
            mode=mode_key,
            diatonic=diatonic,
            weights=weights,
            history=history_pairs,
        )
        for info in seen.values()
    ]

    candidates.sort(key=lambda c: (-c.score, c.vl_distance, c.root_pc, c.quality))
    ranked = [dataclasses.replace(c, rank=i + 1) for i, c in enumerate(candidates)]

    snapshot = AnalyticalContextSnapshot(
        tonic_pc=tonic_pc,
        key_name=mode_key,
        key_degrees=sorted(diatonic),
    )
    return NextChordRecommendation(
        context=snapshot,
        current_root_pc=current_root,
        current_quality=current_quality,
        current_role=current_role,
        current_roman=current_roman,
        candidates=ranked,
        weights_version=prior.version,
    )


def _transition_cadence(
    history: list[tuple[int, str]],
    current: tuple[int, str],
    candidate: tuple[int, str],
    tonic_pc: int,
    mode: str,
) -> str | None:
    """The cadential formula whose arrival is ``candidate``, or None."""

    from .cadence import detect_cadences

    progression = [*history, current, candidate]
    result = detect_cadences(progression, tonic_pc=tonic_pc, mode=mode)
    arrival = len(progression) - 1
    for cadence in result.cadences:
        if cadence.arrival_index == arrival:
            return cadence.type
    return None


__all__ = ["recommend_next_chord", "tag_transition", "CORE_QUALITIES"]
