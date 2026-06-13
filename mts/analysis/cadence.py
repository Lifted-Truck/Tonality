"""Cadence detection: cadential formulas as evidenced events (gap 7).

Scans a named chord progression in a key and emits the cadential formulas it
contains — authentic (V→I), plagal (IV→I), deceptive (V→vi), and half
(arrival on V) — each as a discrete event carrying per-signal evidence
(Decision 7). Builds the *sequential* harmonic vocabulary the next-chord
recommendation (gap 14) and TERRANE/A1/A4 consume.

**Formula, not confirmed cadence.** A cadence *functions* as one only at a
phrase ending on a metrically strong arrival; without timing we cannot
confirm that. So this reports cadential *formulas* and surfaces ``is_final``
(the arrival is the progression's last chord) as the strongest evidence — and
emits a **half** cadence only at a final arrival on the dominant (a
mid-progression V is just a dominant, not a half cadence). Authentic / plagal
/ deceptive formulas are reported wherever they occur, finality noted.

Functional roles come from the same `theory/functions.py` mappings the namer
uses — **major/minor only** (accepted limitation, theory-review pass #1).
Modal keys return ``mode_supported=False`` with no roles and no cadences:
the engine does not claim function it cannot ground.

This is a faithful *consumer* of that functional vocabulary, not a second
implementation — so it inherits the vocabulary's coverage. Notably the minor
templates list **V7** (and richer dominants) but not the bare **major V
triad**, so a bare major-V→i in minor is not recognized; use V7 (the
representative minor-key cadential dominant). Widening the minor vocabulary
is a `theory/functions.py` change, not a cadence change.
"""

from __future__ import annotations

from collections.abc import Sequence

from .results import CadenceChord, CadenceEvent, CadenceResult

_SUPPORTED_MODES = ("major", "minor")
_ROOT_MOTION_NAME = {5: "root up a fourth (down a fifth)", 7: "root up a fifth"}


def _role_table(mode: str) -> dict[tuple[int, str], tuple[str, str]]:
    """{(relative_root, quality): (role, roman)} for the mode's functions."""

    from ..io.loaders import load_function_mappings

    table: dict[tuple[int, str], tuple[str, str]] = {}
    for mapping in load_function_mappings(mode):
        table.setdefault(
            (mapping.degree_pc, mapping.chord_quality), (mapping.role, mapping.modal_label)
        )
    return table


def _annotate(
    chords: Sequence[tuple[int, str]], tonic_pc: int, table: dict
) -> list[CadenceChord]:
    annotated: list[CadenceChord] = []
    for index, (root_pc, quality) in enumerate(chords):
        relative_root = (root_pc - tonic_pc) % 12
        role, roman = table.get((relative_root, quality), (None, None))
        annotated.append(
            CadenceChord(
                index=index,
                root_pc=root_pc,
                quality=quality,
                relative_root=relative_root,
                role=role,
                roman=roman,
            )
        )
    return annotated


def _event(
    cadence_type: str,
    approach: CadenceChord,
    arrival: CadenceChord,
    is_final: bool,
    extra_evidence: list[str],
) -> CadenceEvent:
    root_motion = (arrival.root_pc - approach.root_pc) % 12
    evidence = list(extra_evidence)
    if root_motion in _ROOT_MOTION_NAME:
        evidence.append(_ROOT_MOTION_NAME[root_motion])
    if is_final:
        evidence.append("arrival is the progression's final chord")
    else:
        evidence.append("mid-progression formula (no phrase/metric confirmation)")
    return CadenceEvent(
        type=cadence_type,
        arrival_index=arrival.index,
        approach=approach,
        arrival=arrival,
        root_motion=root_motion,
        is_final=is_final,
        evidence=evidence,
    )


def detect_cadences(
    chords: Sequence[tuple[int, str]], *, tonic_pc: int, mode: str
) -> CadenceResult:
    """Detect cadential formulas in a named progression within a key.

    ``chords`` is an ordered list of ``(root_pc, quality_name)`` pairs;
    ``mode`` is ``"major"`` or ``"minor"`` (others yield
    ``mode_supported=False``, no cadences). Raises ``ValueError`` on an empty
    progression or an out-of-range tonic.
    """

    if not 0 <= tonic_pc < 12:
        raise ValueError(f"tonic_pc out of range: {tonic_pc} (use 0-11).")
    if not chords:
        raise ValueError("detect_cadences needs at least one chord.")

    mode_key = mode.lower()
    if mode_key not in _SUPPORTED_MODES:
        unsupported = [
            CadenceChord(i, root, quality, (root - tonic_pc) % 12, None, None)
            for i, (root, quality) in enumerate(chords)
        ]
        return CadenceResult(tonic_pc, mode_key, False, unsupported, [])

    table = _role_table(mode_key)
    annotated = _annotate(chords, tonic_pc, table)
    last_index = len(annotated) - 1
    cadences: list[CadenceEvent] = []

    for approach, arrival in zip(annotated, annotated[1:]):
        is_final = arrival.index == last_index
        on_tonic_degree = arrival.relative_root == 0 and arrival.role == "tonic"

        if approach.role == "dominant" and on_tonic_degree:
            kind = "V" if approach.relative_root == 7 else "leading-tone"
            cadences.append(
                _event("authentic", approach, arrival, is_final,
                       [f"dominant ({kind}) resolving to tonic"])
            )
        elif (
            approach.role == "dominant"
            and approach.relative_root == 7
            and arrival.relative_root == 9
            and arrival.role == "tonic"
        ):
            cadences.append(
                _event("deceptive", approach, arrival, is_final,
                       ["dominant V resolving deceptively to submediant (vi)"])
            )
        elif (
            approach.relative_root == 5
            and approach.role == "predominant"
            and on_tonic_degree
        ):
            cadences.append(
                _event("plagal", approach, arrival, is_final,
                       ["subdominant (IV) resolving to tonic"])
            )

    # Half cadence: a *final* arrival on the dominant (a mid-progression V is
    # not a half cadence). The approach is whatever precedes it.
    final = annotated[-1]
    if len(annotated) >= 2 and final.relative_root == 7 and final.role == "dominant":
        cadences.append(
            _event("half", annotated[-2], final, True,
                   ["phrase arrives on the dominant (V)"])
        )

    return CadenceResult(tonic_pc, mode_key, True, annotated, cadences)


__all__ = ["detect_cadences"]
