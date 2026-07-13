"""The ruleset evaluator: deterministic conformance checking with evidence.

``evaluate(ruleset, sequence)`` → :class:`ConformanceReport`. No new theory
lives here — the Workstream 0 atoms carry every fact a rule can reference;
this module only filters and counts:

- each rule quantifies over its family's item stream (voice-pair
  transitions; one voice's melodic notes; one voice's rhythmic notes —
  multi-voice material contributes every analyzable voice's line);
- items passing the rule's ``where`` filter are *considered*; a considered
  item matching a ``forbid`` (or failing a ``require``) is a
  :class:`Violation`, reported with its location and the referenced atom
  values as evidence (Decision 7 — violations are findings, not booleans);
- per-rule ``conformance`` = 1 − violations/considered.

Applicability is the error-don't-guess rule made reportable: a rule whose
stream the material cannot supply (voice-pair motion with fewer than two
voices; melodic ``nht_type`` without harmony spans) is returned as
``applicable=False`` with the reason — never silently skipped, never
guessed around. Voices whose lines cannot be analyzed (e.g. internal
overlaps) are likewise reported per-rule in ``skipped_voices``.

v1 substrate note (recorded in ROADMAP Phase 4.6): the evaluator reads a
temporal ``Sequence`` directly, because the atom streams are derived from
one; evaluation over dataset *records* arrives when the atoms join the
record schema.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from collections.abc import Iterable
from typing import TYPE_CHECKING

from ..temporal import Sequence, analyze_melody, analyze_rhythm, voice_motion
from .schema import HARMONY_DEPENDENT_FIELDS, Rule, Ruleset, parse_ruleset

if TYPE_CHECKING:
    from ..session import SessionCatalog


@dataclass(frozen=True)
class Violation:
    """One item that broke one rule, with the evidence to see why."""

    location: dict  # beats (and voices, for pair items)
    evidence: dict  # the referenced atom fields' actual values

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class Firing:
    """One considered item where a rule *held* — the positive complement to a
    :class:`Violation` (same location + evidence shape).

    Every considered item is exactly one of a firing or a violation, so
    ``items_considered == len(firings) + len(violations)`` whenever firings were
    computed. Emitted only when ``evaluate(..., include_firings=True)`` (the
    default keeps output byte-identical); a saliency/credit-assignment consumer
    correlates *where a rule was satisfied* with an external signal (A10 wont),
    which the violations-only stream cannot express.
    """

    location: dict
    evidence: dict

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    polarity: str
    weight: float
    applicable: bool
    reason: str | None  # why not applicable (None when applicable)
    skipped_voices: list[str]  # voices whose lines could not be analyzed
    items_considered: int
    violations: list[Violation]
    conformance: float | None  # None when not applicable or nothing considered
    holds: bool | None  # hard rules: no violations; soft rules: None
    # None = firings were not requested; a list (possibly empty) = requested and
    # computed. Distinct from [] so "not computed" never reads as "none held".
    firings: list[Firing] | None = None

    def to_dict(self) -> dict:
        data = dataclasses.asdict(self)
        # Omit the key entirely when not requested, so include_firings=False
        # output is byte-identical to before this field existed (the golden /
        # port surface only moves for callers that opt in).
        if self.firings is None:
            del data["firings"]
        return data


@dataclass(frozen=True)
class ConformanceReport:
    """Which rules hold, where they break, and how often (Decision 7 shape)."""

    ruleset_name: str
    ruleset_version: str
    # None when NO hard rule was applicable (RE-3d): "held" used to be claimed
    # vacuously — same shape as soft_score's "no soft signal" convention.
    hard_rules_hold: bool | None
    hard_violation_count: int
    soft_score: float | None  # weight-averaged conformance of applicable soft rules
    results: list[RuleResult]

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return {
            "ruleset_name": self.ruleset_name,
            "ruleset_version": self.ruleset_version,
            "hard_rules_hold": self.hard_rules_hold,
            "hard_violation_count": self.hard_violation_count,
            "soft_score": self.soft_score,
            "results": [r.to_dict() for r in self.results],
        }


@dataclass(frozen=True)
class _Stream:
    items: list  # (item, location) pairs
    skipped_voices: list[str]
    unavailable_reason: str | None  # the whole stream could not be built


def _melodic_location(note, voice: str | None) -> dict:
    location = {"onset_beats": note.onset}
    if voice is not None:
        location["voice"] = voice
    return location


def _line_streams(sequence: Sequence, analyzer, harmony) -> _Stream:
    """Per-voice note items from analyze_melody / analyze_rhythm."""

    voices = sequence.voices()
    items: list = []
    skipped: list[str] = []
    if not voices:
        try:
            kwargs = {"harmony": harmony} if analyzer is analyze_melody else {}
            result = analyzer(sequence, **kwargs)
        except ValueError as exc:
            return _Stream([], [], str(exc))
        items = [(note, _melodic_location(note, None)) for note in result.notes]
        return _Stream(items, [], None)
    for voice in voices:
        try:
            kwargs = {"voice": voice}
            if analyzer is analyze_melody:
                kwargs["harmony"] = harmony
            result = analyzer(sequence, **kwargs)
        except ValueError:
            skipped.append(voice)
            continue
        items.extend((note, _melodic_location(note, voice)) for note in result.notes)
    if not items and skipped:
        return _Stream([], skipped, "no voice produced an analyzable line")
    return _Stream(items, skipped, None)


def _build_stream(
    family: str, sequence: Sequence, harmony, chords=None, key=None, session=None
) -> _Stream:
    if family == "harmony":
        if chords is None or key is None:
            missing = "chords" if chords is None else "key"
            return _Stream(
                [], [],
                f"the harmony family needs an explicit chord stream and key "
                f"(missing: {missing}) — no chords, no claim",
            )
        from .harmony_stream import build_harmony_stream

        items, reason = build_harmony_stream(chords, key[0], key[1], session=session)
        return _Stream(items, [], reason)
    if family == "voice_motion":
        try:
            transitions = voice_motion(sequence).transitions
        except ValueError as exc:
            return _Stream([], [], str(exc))
        items = [
            (
                t,
                {
                    "from_beat": t.from_beat,
                    "to_beat": t.to_beat,
                    "voices": [t.voice_a, t.voice_b],
                },
            )
            for t in transitions
        ]
        return _Stream(items, [], None)
    if family == "texture":
        from ..temporal import part_relations

        try:
            relations = part_relations(sequence).relations
        except ValueError as exc:
            return _Stream([], [], str(exc))  # fewer than two parts → no claim
        items = [(r, {"voices": [r.voice_a, r.voice_b]}) for r in relations]
        return _Stream(items, [], None)
    if family == "melody":
        return _line_streams(sequence, analyze_melody, harmony)
    return _line_streams(sequence, analyze_rhythm, harmony)  # "rhythm"


def _evaluate_rule(rule: Rule, stream: _Stream, *, include_firings: bool = False) -> RuleResult:
    considered = 0
    violations: list[Violation] = []
    firings: list[Firing] | None = [] if include_firings else None
    referenced = sorted(rule.referenced_fields())
    for item, location in stream.items:
        if not all(c.matches(getattr(item, c.field)) for c in rule.where):
            continue
        if any(getattr(item, c.field) is None for c in rule.check):
            continue  # a check field carries no claim here (line edge, no
            # harmony coverage): absence of evidence is not a violation,
            # so the item is not considered at all.
        considered += 1
        matched = all(c.matches(getattr(item, c.field)) for c in rule.check)
        violated = matched if rule.check_kind == "forbid" else not matched
        if violated:
            violations.append(
                Violation(
                    location=location,
                    evidence={f: getattr(item, f) for f in referenced},
                )
            )
        elif firings is not None:
            firings.append(
                Firing(
                    location=location,
                    evidence={f: getattr(item, f) for f in referenced},
                )
            )
    conformance = 1.0 - len(violations) / considered if considered else None
    return RuleResult(
        rule_id=rule.id,
        polarity=rule.polarity,
        weight=rule.weight,
        applicable=True,
        reason=None,
        skipped_voices=list(stream.skipped_voices),
        items_considered=considered,
        violations=violations,
        conformance=conformance,
        holds=(not violations) if rule.polarity == "hard" else None,
        firings=firings,
    )


def _not_applicable(rule: Rule, reason: str, skipped: list[str] | None = None) -> RuleResult:
    return RuleResult(
        rule_id=rule.id,
        polarity=rule.polarity,
        weight=rule.weight,
        applicable=False,
        reason=reason,
        skipped_voices=list(skipped or []),
        items_considered=0,
        violations=[],
        conformance=None,
        holds=None,
    )


def evaluate(
    ruleset: Ruleset | dict,
    sequence: Sequence,
    *,
    harmony: Iterable[tuple[float, float, Iterable[int]]] | None = None,
    chords: Iterable[tuple[int, str]] | None = None,
    key: tuple[int, str] | None = None,
    session: SessionCatalog | None = None,
    include_firings: bool = False,
) -> ConformanceReport:
    """Evaluate every rule against *sequence*; nothing is silently skipped.

    ``ruleset`` may be a parsed :class:`Ruleset` or a raw dict (validated
    here, raising :class:`RulesetValidationError` with the full error list).
    ``harmony`` spans are required only by rules referencing
    harmony-dependent melodic fields; such rules without harmony come back
    ``applicable=False``, never guessed. **``chords`` + ``key``** feed the
    ``harmony`` family (gap B): ``chords`` is ``[(root_pc, quality), …]`` and
    ``key`` is ``(tonic_pc, mode)``; harmony rules without both come back
    ``applicable=False`` (no chords, no claim) — the same discipline as harmony
    spans. ``session`` merges that session's registered chord qualities into the
    harmony family's catalog, so a user-defined quality resolves like a built-in
    one; a quality that resolves in neither raises ``ValueError`` (a caller
    error — error, not guess), like malformed harmony spans above.
    ``include_firings`` adds the located *firings* (considered items
    where the rule held) to each applicable result — the positive complement to
    violations, for saliency/credit-
    assignment consumers; off by default (output byte-identical when off).
    """

    if not isinstance(ruleset, Ruleset):
        ruleset = parse_ruleset(ruleset)
    if harmony is not None:
        harmony = list(harmony)
        # Validate spans once, up front: malformed harmony is a caller error
        # and must raise here — not be swallowed into per-voice
        # "unanalyzable line" applicability reasons downstream.
        from ..temporal.melodic import _normalize_harmony

        _normalize_harmony(harmony)
    chords = list(chords) if chords is not None else None

    streams: dict[str, _Stream] = {}
    results: list[RuleResult] = []
    for rule in ruleset.rules:
        harmony_fields = HARMONY_DEPENDENT_FIELDS.get(rule.family, set())
        if harmony is None and rule.referenced_fields() & harmony_fields:
            results.append(
                _not_applicable(
                    rule,
                    "references harmony-dependent fields "
                    f"({sorted(rule.referenced_fields() & harmony_fields)}) "
                    "but no harmony spans were provided — no harmony, no claim",
                )
            )
            continue
        if rule.family not in streams:
            streams[rule.family] = _build_stream(
                rule.family, sequence, harmony, chords, key, session
            )
        stream = streams[rule.family]
        if stream.unavailable_reason is not None:
            results.append(_not_applicable(rule, stream.unavailable_reason, stream.skipped_voices))
            continue
        results.append(_evaluate_rule(rule, stream, include_firings=include_firings))

    hard = [r for r in results if r.polarity == "hard" and r.applicable]
    hard_violations = sum(len(r.violations) for r in hard)
    soft = [
        r
        for r in results
        if r.polarity == "soft" and r.applicable and r.conformance is not None
    ]
    soft_weight = sum(r.weight for r in soft)
    soft_score = (
        sum(r.conformance * r.weight for r in soft) / soft_weight if soft_weight else None
    )
    return ConformanceReport(
        ruleset_name=ruleset.name,
        ruleset_version=ruleset.version,
        hard_rules_hold=all(r.holds for r in hard) if hard else None,
        hard_violation_count=hard_violations,
        soft_score=soft_score,
        results=results,
    )


__all__ = ["ConformanceReport", "RuleResult", "Violation", "evaluate"]
