"""Conformance repair (Phase 4.6/7, slice 1): impose a ruleset on existing material.

The third operation of the ruleset triad — *extract* (``induce_ruleset``),
*compare* (``compare_rulesets``), **impose** (this): given a piece and a ruleset,
find a **minimal set of edits** that eliminates the hard violations without
worsening the soft score, preserving everything the ruleset does not speak to.

**GENERATIVE-side** per the cardinal rule (an edit invents pitch content), which is
why it lives in ``search/`` — like its siblings it is exact, exhaustive, bounded
search, not sampling. The Phase 4.6 **evaluator is the oracle**: every candidate is
re-evaluated in full, so a repair can never *think* it fixed something — it either
passes ``evaluate`` or it is not a repair. Deterministic throughout (sorted
enumeration, no RNG, no clock), capped by construction.

Slice-1 scope (ROADMAP, and the 2026-07-08 design brief):

- **Edit vocabulary: re-pitch a single note.** No rhythm edits, no insertion or
  deletion; one edit per note.
- **Voice-motion–driven**: candidate notes come from the hard voice-motion
  violations' locations (a pair transition names its two voices and two beats —
  the four implicated notes). Hard violations in any *other* family are reported
  honestly as out of slice-1 scope, never silently ignored. The oracle re-check
  still covers the **whole** ruleset — an edit that fixed the parallels but
  created a melodic tritone is rejected.
- **Minimality is lexicographic** (Julian's call): fewest notes edited first,
  total absolute semitone displacement as the tie-break. Implemented exactly via
  iterative deepening — depth k is only explored if no repair exists at depth
  k-1 — so the edit *count* of every returned repair is globally minimal.

Ranked plural output (Decision 7): every distinct minimal repair found, each with
its edit list, per-edit violated-rule provenance, and the after-report summary.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable

from ..core.pitch import Pitch
from ..rules import Ruleset, evaluate, parse_ruleset
from ..temporal import Sequence
from .results import Repair, RepairEdit, RepairResult

_EPS = 1e-6
_MAX_EDIT_CAP = 6          # hard ceiling on max_edits (safety by construction)
_MAX_EVAL_CAP = 20000      # hard ceiling on oracle calls


def _hard_violations(report) -> list[tuple[str, dict]]:
    """(rule_id, location) for every hard-rule violation in the report."""
    out = []
    for result in report.results:
        if result.polarity != "hard" or not result.applicable:
            continue
        for violation in result.violations:
            out.append((result.rule_id, violation.location))
    return out


def _implicated_notes(
    sequence: Sequence, violations: list[tuple[str, dict]]
) -> dict[tuple[str, float], list[str]]:
    """Map each implicated note ``(voice, onset)`` to the rule_ids implicating it.

    A voice-motion violation location names two voices and two beats; the notes
    sounding for those voices at those beats are the edit candidates.
    """
    implicated: dict[tuple[str, float], list[str]] = {}
    for rule_id, location in violations:
        voices = location.get("voices")
        if voices is None:
            continue  # not a voice-motion location — out of slice-1 scope
        beats = [location.get("from_beat"), location.get("to_beat")]
        for event in sequence.events:
            if event.voice not in voices:
                continue
            if any(b is not None and abs(event.onset - b) <= _EPS for b in beats):
                key = (event.voice, event.onset)
                rules = implicated.setdefault(key, [])
                if rule_id not in rules:
                    rules.append(rule_id)
    return implicated


def _re_pitch(sequence: Sequence, voice: str, onset: float, new_midi: int) -> Sequence:
    """A new sequence with the (voice, onset) note re-pitched — all else preserved."""
    events = tuple(
        dataclasses.replace(e, pitch=Pitch.from_midi(new_midi))
        if e.voice == voice and abs(e.onset - onset) <= _EPS
        else e
        for e in sequence.events
    )
    return Sequence(events=events, tempo=sequence.tempo, meter=sequence.meter)


def repair_sequence(
    sequence: Sequence,
    ruleset: Ruleset | dict,
    *,
    max_edits: int = 2,
    pitch_window: int = 7,
    allowed_pcs: Iterable[int] | None = None,
    max_evaluations: int = 4000,
    max_repairs: int = 8,
) -> RepairResult:
    """Find minimal re-pitch edits making *sequence* satisfy *ruleset*'s hard rules.

    ``max_edits`` bounds the edit count (≤ 6); ``pitch_window`` bounds each edit to
    ± that many semitones of the original; ``allowed_pcs``, when given, restricts
    candidate pitches to those pitch classes (e.g. a scale). ``max_evaluations``
    caps oracle calls — if exhausted, ``budget_exhausted`` is set and the result is
    honest about incompleteness. Repairs are ranked lexicographically:
    ``(edit count, total |semitone| displacement)``; iterative deepening makes the
    edit count exactly minimal. Raises on out-of-range parameters; a piece whose
    hard violations lie outside the voice-motion family is reported unrepairable
    *in this slice* with the offending families named (error/report, not guess).
    """

    if not isinstance(ruleset, Ruleset):
        ruleset = parse_ruleset(ruleset)
    if not 1 <= max_edits <= _MAX_EDIT_CAP:
        raise ValueError(f"max_edits must be 1..{_MAX_EDIT_CAP}, got {max_edits}.")
    if pitch_window < 1:
        raise ValueError(f"pitch_window must be >= 1, got {pitch_window}.")
    if not 1 <= max_evaluations <= _MAX_EVAL_CAP:
        raise ValueError(
            f"max_evaluations must be 1..{_MAX_EVAL_CAP}, got {max_evaluations}."
        )
    pcs_filter = (
        frozenset(int(pc) % 12 for pc in allowed_pcs) if allowed_pcs is not None else None
    )

    evaluations = 0

    def oracle(seq: Sequence):
        nonlocal evaluations
        evaluations += 1
        return evaluate(ruleset, seq)

    before = oracle(sequence)
    before_hard = _hard_violations(before)
    before_soft = before.soft_score

    def soft_ok(report) -> bool:
        if before_soft is None or report.soft_score is None:
            return True
        return report.soft_score >= before_soft - 1e-9

    if not before_hard:
        return RepairResult(
            already_conformant=True, repairs=[], reason=None,
            evaluations=evaluations, budget_exhausted=False,
            before_hard_violations=0, ruleset_name=before.ruleset_name,
        )

    # Slice-1 scope check: every hard violation must be voice-motion-locatable.
    unsupported = sorted(
        {rule_id for rule_id, loc in before_hard if loc.get("voices") is None}
    )
    if unsupported:
        return RepairResult(
            already_conformant=False, repairs=[],
            reason=(
                "hard violations outside the voice-motion family cannot be repaired "
                f"in slice 1 (rules: {unsupported}); re-pitch repair is driven by "
                "pair-transition locations"
            ),
            evaluations=evaluations, budget_exhausted=False,
            before_hard_violations=len(before_hard), ruleset_name=before.ruleset_name,
        )

    midi_of = {(e.voice, e.onset): e.pitch.midi for e in sequence.events}

    def candidates_for(note: tuple[str, float]) -> list[int]:
        original = midi_of[note]
        out = []
        for midi in range(max(0, original - pitch_window), min(127, original + pitch_window) + 1):
            if midi == original:
                continue
            if pcs_filter is not None and midi % 12 not in pcs_filter:
                continue
            out.append(midi)
        return out

    found: dict[frozenset, Repair] = {}
    budget_exhausted = False

    def dfs(seq: Sequence, edits: tuple[RepairEdit, ...], depth_left: int,
            visited: set[frozenset]) -> None:
        nonlocal budget_exhausted
        if budget_exhausted:
            return
        report = oracle(seq) if edits else before  # root already evaluated
        hard = _hard_violations(report) if edits else before_hard
        if edits and not hard:
            if soft_ok(report):
                key = frozenset((e.voice, e.onset_beats, e.midi_to) for e in edits)
                if key not in found:
                    found[key] = Repair(
                        edits=list(edits),
                        total_displacement=sum(
                            abs(e.midi_to - e.midi_from) for e in edits
                        ),
                        soft_score_after=report.soft_score,
                        events=[
                            [e.onset, e.duration, e.pitch.midi, e.voice]
                            for e in seq.events
                        ],
                    )
            return  # hard fixed (or soft worsened) — either way, don't extend
        if depth_left <= 0:
            return  # depth-limited: expansion only below the current ceiling
        implicated = _implicated_notes(seq, hard)
        edited_notes = {(e.voice, e.onset) for e in edits}
        for note in sorted(implicated):
            if note in edited_notes or note not in midi_of:
                continue
            for midi in candidates_for(note):
                if evaluations >= max_evaluations:
                    budget_exhausted = True
                    return
                key = frozenset(
                    {(e.voice, e.onset_beats, e.midi_to) for e in edits}
                    | {(note[0], note[1], midi)}
                )
                if key in visited:
                    continue
                visited.add(key)
                edit = RepairEdit(
                    voice=note[0], onset_beats=note[1],
                    midi_from=midi_of[note], midi_to=midi,
                    fixes_rules=list(implicated[note]),
                )
                dfs(_re_pitch(seq, note[0], note[1], midi), edits + (edit,),
                    depth_left - 1, visited)

    # Iterative deepening: depth k only if nothing at depth k-1 → minimal count.
    for depth in range(1, max_edits + 1):
        dfs(sequence, (), depth, set())
        if found or budget_exhausted:
            break

    repairs = sorted(
        found.values(),
        key=lambda r: (
            len(r.edits), r.total_displacement,
            tuple((e.voice, e.onset_beats, e.midi_to) for e in r.edits),
        ),
    )[:max_repairs]

    reason = None
    if not repairs:
        reason = (
            "oracle budget exhausted before a repair was found"
            if budget_exhausted
            else f"no repair within max_edits={max_edits}, pitch_window={pitch_window}"
            + (", allowed_pcs" if pcs_filter is not None else "")
        )

    return RepairResult(
        already_conformant=False, repairs=repairs, reason=reason,
        evaluations=evaluations, budget_exhausted=budget_exhausted,
        before_hard_violations=len(before_hard), ruleset_name=before.ruleset_name,
    )


__all__ = ["repair_sequence"]
