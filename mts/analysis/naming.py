"""Context-sensitive naming / disambiguation (Phase 3, final slice).

``name_chord`` consumes the candidate ``(root, quality)`` readings that
``interpret_chord`` enumerates and ranks them for a given analytical frame,
returning the chosen reading **with ranked alternatives and the evidence for
each** (Decision 7) — never a bare label.

Signals (tiers (a)+(b) of the recorded design; sequential/voice-leading
signals are an additive follow-up):

- intrinsic — ``bass_is_root`` (only when a real ``Realization`` is present;
  register is never invented), ``quality_canonicality`` (root-supported:
  a perfect fifth above the candidate root);
- key-relative — ``root_diatonic``, ``functional_fit`` (the generated
  functional-harmony tables), ``all_tones_diatonic`` (via the cached
  ``compatibility_roots``), and a ``special_function`` seam that flags
  recognized chromatic functions (augmented-sixth family, secondary
  dominants, Neapolitan) instead of merely penalizing their chromaticism.

Signal weights come from a **versioned weight table**
(``data/naming_weights.json``); every result cites the version it used.

**Two distinct don't-guess rules** apply here: the register rule (no
``bass_is_root`` signal without a realization — register is never invented)
and the key rule (``context=None`` means intrinsic-only ranking with
``is_ambiguous`` honesty — a key is never fabricated).

``name_chord`` is deliberately **single-context**; ``name_chord_across_keys``
is the thin wrapper over ranked key candidates from ``infer_key`` (recorded
design adaptation): per-key conditional namings plus a combined view weighted
by key confidence under a versioned marginalization scheme.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ..core.bitmask import mask_from_pcs
from ..core.quality import ChordQuality
from ..core.realization import Realization
from ..core.scale import Scale
from .analytical_context import AnalyticalContext
from .equivalence import interpret_chord
from .key_induction import candidate_context
from .pcset_math import compatibility_roots
from .results import (
    AnalyticalContextSnapshot,
    ChordNaming,
    KeyInductionResult,
    MultiKeyNaming,
    NamingEvidence,
    NamingUnderKey,
    RankedInterpretation,
)
from ..io.loaders import NamingWeights, load_chord_qualities, load_function_mappings, load_naming_weights


# Modes for which generated functional-harmony tables exist (3.5b mapping).
_MODE_FOR_KEY = {"Ionian": "major", "Aeolian": "minor"}

_DOM7_RELATIVE_MASK = mask_from_pcs([0, 4, 7, 10])
_DOM7_FLAT5_RELATIVE_MASK = mask_from_pcs([0, 4, 6, 10])
_MAJ_TRIAD_RELATIVE_MASK = mask_from_pcs([0, 4, 7])


def _snapshot(context: AnalyticalContext | None) -> AnalyticalContextSnapshot | None:
    if context is None:
        return None
    return AnalyticalContextSnapshot(
        tonic_pc=context.tonic_pc,
        key_name=context.key.name if context.key is not None else None,
        key_degrees=list(context.key.degrees) if context.key is not None else None,
    )


def _special_function_category(
    relative_root: int, quality: ChordQuality, key_degrees: frozenset[int]
) -> tuple[str | None, str | None]:
    """The special-function seam: recognize standard chromatic functions.

    Returns ``(category, detail)``. Order matters: the augmented-sixth family
    is checked before the secondary-dominant pattern it would otherwise
    shadow. Detect-and-flag only — fully-spelled It/Fr/Ger labelling is a
    recorded follow-up.
    """

    if relative_root == 8 and quality.mask == _DOM7_RELATIVE_MASK:
        return "augmented_sixth_german", "enharmonic dominant 7th on b6"
    if relative_root in (8, 2) and quality.mask == _DOM7_FLAT5_RELATIVE_MASK:
        return "augmented_sixth_french", "enharmonic dominant 7th flat-5"
    has_dominant_core = 4 in quality.intervals and 10 in quality.intervals
    if has_dominant_core and relative_root != 7:
        target = (relative_root + 5) % 12
        if target in key_degrees:
            return "secondary_dominant", f"resolves down a fifth to degree pc {target}"
    if relative_root == 1 and quality.mask == _MAJ_TRIAD_RELATIVE_MASK:
        return "neapolitan", "major triad on the flat second degree"
    return None, None


def name_chord(
    material: Any,
    context: AnalyticalContext | None,
    *,
    realization: Realization | None = None,
    catalog: Mapping[str, ChordQuality] | None = None,
    weights: "NamingWeights | None" = None,
) -> ChordNaming:
    """Rank every valid naming of *material* within an analytical frame.

    ``material`` is a rooted ``Chord``, anything with ``.pcs``, or a plain
    iterable of pitch classes (segments are rootless — naming is exactly the
    act of choosing a root). ``context=None`` ranks on intrinsic signals only
    and never fabricates a key. The result is conditional on ``context`` and
    cites the weight-table version used.
    """

    # ``.pcs`` is uniform now — a field on Chord, a property on Scale and
    # Realization (RE-6d) — so no method-vs-attribute probe; a raw iterable
    # (no ``.pcs``) is used directly.
    pcs_attr = getattr(material, "pcs", None)
    pcs: Iterable[int] = material if pcs_attr is None else pcs_attr
    pc_set = sorted({int(pc) % 12 for pc in pcs})
    if not pc_set:
        raise ValueError("name_chord needs at least one pitch class.")

    if catalog is None:

        catalog = load_chord_qualities()
    if weights is None:

        weights = load_naming_weights()
    w = weights.weights

    interpretations = interpret_chord(pc_set, catalog=catalog).interpretations

    has_key = context is not None and context.has_key
    tonic = context.tonic_pc if context is not None else None
    key_degrees = frozenset(context.key.degrees) if has_key else frozenset()
    bass_pc = realization.bass.pc if realization is not None else None

    ranked: list[RankedInterpretation] = []
    for interp in interpretations:
        quality = catalog[interp.quality]
        evidence: list[NamingEvidence] = []
        functional_role: str | None = None
        function_category: str | None = None

        if bass_pc is not None and bass_pc == interp.root_pc:
            evidence.append(
                NamingEvidence(
                    signal="bass_is_root",
                    weight=w["bass_is_root"],
                    detail=f"realized bass pc {bass_pc} is the candidate root",
                )
            )
        if 7 in quality.intervals:
            evidence.append(
                NamingEvidence(
                    signal="quality_canonicality",
                    weight=w["quality_canonicality"],
                    detail="root-supported: perfect fifth above the root",
                )
            )

        relative_root = (interp.root_pc - tonic) % 12 if tonic is not None else None
        if has_key and relative_root is not None:
            if relative_root in key_degrees:
                evidence.append(
                    NamingEvidence(
                        signal="root_diatonic",
                        weight=w["root_diatonic"],
                        detail=f"root is scale degree pc {relative_root}",
                    )
                )
            mode = _MODE_FOR_KEY.get(context.key.name)
            if mode is not None:

                for mapping in load_function_mappings(mode):
                    if (
                        mapping.degree_pc == relative_root
                        and mapping.chord_quality == interp.quality
                    ):
                        functional_role = mapping.role
                        evidence.append(
                            NamingEvidence(
                                signal="functional_fit",
                                weight=w["functional_fit"],
                                detail=f"{mapping.modal_label} ({mapping.role}, {mode})",
                            )
                        )
                        break
            if relative_root in compatibility_roots(context.key, quality):
                evidence.append(
                    NamingEvidence(
                        signal="all_tones_diatonic",
                        weight=w["all_tones_diatonic"],
                        detail="every chord tone is in the key",
                    )
                )
            else:
                function_category, detail = _special_function_category(
                    relative_root, quality, key_degrees
                )
                if function_category is not None:
                    evidence.append(
                        NamingEvidence(
                            signal="special_function",
                            weight=w["special_function"],
                            detail=f"{function_category}: {detail}",
                        )
                    )

        ranked.append(
            RankedInterpretation(
                interpretation=interp,
                score=sum(e.weight for e in evidence),
                rank=0,  # assigned after sorting
                functional_role=functional_role,
                root_degree=context.degree_of(interp.root_pc) if has_key else None,
                function_category=function_category,
                evidence=evidence,
            )
        )

    ranked.sort(key=lambda r: (-r.score, r.interpretation.root_pc, r.interpretation.quality))
    ranked = [
        RankedInterpretation(
            interpretation=r.interpretation,
            score=r.score,
            rank=i + 1,
            functional_role=r.functional_role,
            root_degree=r.root_degree,
            function_category=r.function_category,
            evidence=r.evidence,
        )
        for i, r in enumerate(ranked)
    ]

    if len(ranked) > 1:
        is_ambiguous = (
            context is None
            or (ranked[0].score - ranked[1].score) < weights.ambiguity_margin
        )
    else:
        is_ambiguous = False

    return ChordNaming(
        chosen=ranked[0] if ranked else None,
        alternatives=ranked[1:],
        is_ambiguous=is_ambiguous,
        context=_snapshot(context),
        weights_version=weights.version,
    )


def name_chord_across_keys(
    material: Any,
    key_result: KeyInductionResult,
    *,
    scales: Mapping[str, Scale] | None = None,
    realization: Realization | None = None,
    catalog: Mapping[str, ChordQuality] | None = None,
    weights: "NamingWeights | None" = None,
) -> MultiKeyNaming:
    """Name *material* conditional on each ranked key candidate, then combine.

    The thin wrapper of the recorded design: maps the single-context
    ``name_chord`` over the top key candidates from ``infer_key`` and returns
    every per-key conditional naming plus a combined ranking whose scores are
    marginalized over key-confidence weights (versioned scheme; v1
    ``relu-normalized``: weights ∝ max(correlation, 0) over the top-N,
    renormalized — falling back to the single best key if none is positive).
    Combined entries carry no key-conditional facts (role/degree/category);
    read those from ``per_key``.
    """

    if weights is None:

        weights = load_naming_weights()
    top_n = int(weights.marginalization.get("top_n", 3))

    considered = [c for c in key_result.candidates[:top_n] if c.score > 0]
    if not considered:
        considered = [key_result.best]
    total = sum(c.score for c in considered)
    key_weights = (
        [c.score / total for c in considered]
        if total > 0
        else [1.0 / len(considered)] * len(considered)
    )

    per_key: list[NamingUnderKey] = []
    combined_scores: dict[tuple[int, str], float] = {}
    combined_evidence: dict[tuple[int, str], list[NamingEvidence]] = {}
    combined_interp: dict[tuple[int, str], Any] = {}
    for candidate, key_weight in zip(considered, key_weights):
        context = candidate_context(candidate, scales=scales)
        naming = name_chord(
            material, context, realization=realization, catalog=catalog, weights=weights
        )
        per_key.append(
            NamingUnderKey(candidate=candidate, key_weight=key_weight, naming=naming)
        )
        for entry in ([naming.chosen] if naming.chosen else []) + naming.alternatives:
            key = (entry.interpretation.root_pc, entry.interpretation.quality)
            contribution = key_weight * entry.score
            combined_scores[key] = combined_scores.get(key, 0.0) + contribution
            combined_interp[key] = entry.interpretation
            combined_evidence.setdefault(key, []).append(
                NamingEvidence(
                    signal="key_weighted_score",
                    weight=contribution,
                    detail=(
                        f"tonic_pc={candidate.tonic_pc} {candidate.mode}"
                        f" (key_weight={key_weight:.3f}, score={entry.score:.3f})"
                    ),
                )
            )

    combined = [
        RankedInterpretation(
            interpretation=combined_interp[key],
            score=score,
            rank=0,
            evidence=combined_evidence[key],
        )
        for key, score in combined_scores.items()
    ]
    combined.sort(key=lambda r: (-r.score, r.interpretation.root_pc, r.interpretation.quality))
    combined = [
        RankedInterpretation(
            interpretation=r.interpretation,
            score=r.score,
            rank=i + 1,
            evidence=r.evidence,
        )
        for i, r in enumerate(combined)
    ]

    is_ambiguous = (
        len(combined) > 1
        and (combined[0].score - combined[1].score) < weights.ambiguity_margin
    )
    return MultiKeyNaming(
        per_key=per_key,
        combined=combined,
        is_ambiguous=is_ambiguous,
        weights_version=weights.version,
    )


__all__ = ["name_chord", "name_chord_across_keys"]
