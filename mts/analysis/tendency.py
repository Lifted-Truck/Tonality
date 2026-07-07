"""Melodic tendency: which pitch wants to resolve where, as a cited number.

The melodic sibling of ``next_chord`` (gap 19, A9 Wend): given a pitch class
in a key — optionally over a chord — report the **ranked resolutions** (where
it pulls, how strongly, and why) plus the full scale-degree **stability
table** (the cited replacement for a caller's ``root > third`` hand rule).

Model: Lerdahl's anchoring attraction (Tonal Pitch Space, 2001)

    a(p -> q) = (s_q / s_p) / d**n

with stabilities *s* frozen into the versioned prior
(``data/melodic_tendency.json``, derived from the kk-1982.1 key profiles —
copied, never read live, so a profile default flip cannot silently move
tendency scales). When a chord context is given, chord tones' stability is
multiplied by the prior's ``chord_anchor_boost`` in **both** roles (Bharucha
anchoring): a chord-tone target pulls harder, a chord-tone source is more
settled and pulls away less.

Target policy is a **caller parameter** (fork B ruling, 2026-07-07): rulesets
and styles may select their own resolution-target vocabulary; the default is
``diatonic_steps`` (anchoring theory's own target set — a leap is not a
resolution), and ``chromatic_steps`` widens to all step neighbors so
chromaticism is never shut out. The full 12-pc stability table is reported
regardless, so any other landing policy stays computable caller-side.

Analysis-side and register-free (identity level): direction in pitch space is
a realization concern; here distance is circular semitones. The engine
reports pulls with evidence and cites the prior version (Decision 7); **the
caller owns the snap policy** — the same seam as margin-as-signal.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..core.bitmask import validate_pc
from ..io.loaders import MelodicTendencyPrior, load_melodic_tendency
from .results import StabilityEntry, TendencyResolution, TendencyResult

# Diatonic collections per supported mode (natural minor: the raised 6th/7th
# are chromatic *sources* with correctly strong pulls — see tests).
_MODE_SCALES: dict[str, tuple[int, ...]] = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
}

_DEGREE_NAMES = {1: "tonic", 2: "supertonic", 3: "mediant", 4: "subdominant",
                 5: "dominant", 6: "submediant", 7: "leading/subtonic degree"}


def _circular_distance(a: int, b: int) -> int:
    up = (b - a) % 12
    return min(up, 12 - up)


def melodic_tendency(
    pc: int | None = None,
    *,
    degree: int | None = None,
    tonic_pc: int,
    mode: str,
    chord_pcs: Iterable[int] | None = None,
    targets: str = "diatonic_steps",
    prior: MelodicTendencyPrior | None = None,
    prior_version: str | None = None,
) -> TendencyResult:
    """Ranked resolutions + stability table for one pitch class in a key.

    Provide exactly one of ``pc`` (absolute, 0-11) or ``degree`` (1-7, resolved
    through the mode's scale). ``chord_pcs`` opts into chord-tone anchoring.
    ``targets`` selects the resolution-target policy (see module docstring).
    ``prior``/``prior_version`` pin the tendency prior (default: the file's
    first entry). Raises ``ValueError`` with actionable messages.
    """

    mode_key = str(mode).lower()
    scale = _MODE_SCALES.get(mode_key)
    if scale is None:
        raise ValueError(
            f"Unsupported mode {mode!r} (supported: {sorted(_MODE_SCALES)}). "
            "The tendency prior's stability tables are major/minor (kk-1982.1-derived)."
        )
    tonic = validate_pc(int(tonic_pc))

    if (pc is None) == (degree is None):
        raise ValueError("Provide exactly one of pc (0-11) or degree (1-7).")
    if degree is not None:
        if not 1 <= int(degree) <= 7:
            raise ValueError(f"degree out of range: {degree} (use 1-7).")
        source = (tonic + scale[int(degree) - 1]) % 12
    else:
        source = validate_pc(int(pc))

    if prior is not None and prior_version is not None and prior.version != prior_version:
        raise ValueError("Pass prior or prior_version, not both (they disagree).")
    table = prior if prior is not None else load_melodic_tendency(prior_version)
    if mode_key not in table.stability:
        raise ValueError(
            f"Prior {table.version!r} has no stability table for mode {mode_key!r}."
        )
    stability_row = table.stability[mode_key]

    chord: tuple[int, ...] | None = None
    if chord_pcs is not None:
        chord = tuple(sorted({validate_pc(int(c)) for c in chord_pcs}))
        if not chord:
            raise ValueError("chord_pcs, when given, must contain at least one pitch class.")

    if targets not in table.target_policies:
        raise ValueError(
            f"Unknown target policy {targets!r} (known: {list(table.target_policies)})."
        )

    scale_abs = tuple((tonic + step) % 12 for step in scale)
    degree_of = {p: i + 1 for i, p in enumerate(scale_abs)}

    def stab(p: int) -> float:
        base = stability_row[(p - tonic) % 12]
        if chord is not None and p in chord:
            return base * table.chord_anchor_boost
        return base

    s_source = stab(source)

    # --- ranked resolutions under the target policy ---------------------------
    candidate_pool = scale_abs if targets == "diatonic_steps" else tuple(range(12))
    resolutions: list[TendencyResolution] = []
    for q in candidate_pool:
        if q == source:
            continue
        d = _circular_distance(source, q)
        if not 1 <= d <= table.max_step_semitones:
            continue
        s_q = stab(q)
        strength = round((s_q / s_source) / (d ** table.distance_exponent), 4)
        evidence = [
            f"{'semitone' if d == 1 else 'whole-step'} neighbor (d={d})",
            f"target stability {round(s_q, 4)} vs source {round(s_source, 4)}",
        ]
        deg = degree_of.get(q)
        if deg is not None:
            evidence.append(f"target is the {_DEGREE_NAMES[deg]} (degree {deg})")
        else:
            evidence.append(f"chromatic neighbor (outside the {mode_key} scale)")
        if chord is not None and q in chord:
            evidence.append(f"chord tone (anchor boost x{table.chord_anchor_boost})")
        resolutions.append(
            TendencyResolution(
                target_pc=q,
                strength=strength,
                distance=d,
                in_key=q in degree_of,
                is_chord_tone=(q in chord) if chord is not None else None,
                evidence=tuple(evidence),
            )
        )
    resolutions.sort(key=lambda r: (-r.strength, r.target_pc))

    # --- the full landing table (descending stability) ------------------------
    stability_entries = tuple(
        sorted(
            (
                StabilityEntry(
                    pc=p,
                    degree=degree_of.get(p),
                    value=round(stab(p), 4),
                    in_key=p in degree_of,
                    is_chord_tone=(p in chord) if chord is not None else None,
                )
                for p in range(12)
            ),
            key=lambda e: (-e.value, e.pc),
        )
    )

    return TendencyResult(
        source_pc=source,
        source_degree=degree_of.get(source),
        tonic_pc=tonic,
        mode=mode_key,
        targets=targets,
        chord_pcs=chord,
        resolutions=tuple(resolutions),
        stability=stability_entries,
        prior_version=table.version,
    )


__all__ = ["melodic_tendency"]
