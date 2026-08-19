"""Modal transform — analyze → plan → apply (gap 26's feature).

Switch a piece's MODE, not its key: analyze the structural key timeline, build
a **plan** — a serializable, inspectable, *editable* list of typed decisions,
one per note — and apply it. The three stages are separate on purpose:

- ``plan_modal_transform`` is a pure function of **(score, analysis, policy)**
  — never of "the engine's opinion at call time". Pass a precomputed
  ``structural``/``chromatic`` analysis to hold the hypothesis fixed and see
  the consequence of a different one.
- ``apply_transform_plan`` executes a plan **and nothing else**: every output
  pitch is already in the plan, so applying an *edited* plan is the supported
  way to override any decision (the options-exposed contract). It validates the
  plan against the sequence (count, onsets, source pitches) and **errors on any
  unresolved decision** — a plan with open questions cannot be silently played.
- ``modal_transform`` is the one-shot convenience: plan, then apply.

**A timeline, never one global key** (the failure mode every surveyed DAW
ships). Each structural key area gets its own ``InterscalarMap``: the area's
scale → the target collection **rooted to preserve the area tonic's interval
from home** ("the most computable default", Julian's ruling — a piece in C
modulating to G, transformed toward minor, gets a G-rooted area: the dominant
stays the dominant). Per-area overrides via ``area_targets`` expose the ideal.

**Chromatic notes keep their rhetoric** (the recorded default): a tone outside
its area's scale attaches to a degree (the primitive's shared rule — ties
attach below, flagged) and carries its alteration across. Each such decision is
enriched with the gap 25 classifier's **evidence** for the window it falls in
(plural readings + the confident/contested zone) and with the
**alternative not taken** (the other attachment's image, when tied). Under
``chromatic="strict"`` a chromatic note in a *contested* window becomes
**UNRESOLVED** — it sits in the plan with its evidence and alternatives, and
``apply`` refuses until a human (or a better policy) resolves it. Refusing to
guess is a feature: the contested band is exactly where analysts disagree.

**Percussion is never transformed.** Voices on MIDI channel 10 (ingestion
labels ``…c9``) are excluded automatically — each excluded note still gets a
decision (kind ``"excluded"``, image = source), so the exclusion is visible in
the plan rather than silent.

**Markedness is tracked per note**: ``chromatic_before``/``chromatic_after``
make absorption (chromatic in the source, diatonic in the target) a reported
fact on the decision, per the keep-and-report ruling.

Honest limit, stated up front: the output is musically **plausible, not
correct** — a mode switch changes voice-leading, so parallels and awkward leaps
can appear. ``repair_sequence`` over a counterpoint ruleset is the natural
post-pass (extract/compare/impose, pointed at the transform's output).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from ..temporal.sequence import Sequence
from ..temporal.structural_key import _MODE_SCALE, area_indices
from .remap import InterscalarMap, _attach_degree, _signed_delta

PLAN_VERSION = "modal-transform-plan.1"
_CHROMATIC_POLICIES = ("rhetoric", "strict")


@dataclass(frozen=True)
class TransformDecision:
    """One note's transform: coordinates, resolution, evidence, alternatives."""

    index: int
    voice: str | None
    onset: float
    from_midi: int
    kind: str                     # "diatonic" | "chromatic" | "excluded"
    status: str                   # "resolved" | "unresolved"
    area_index: int
    degree: int | None            # attachment degree (None for excluded)
    alteration: int               # signed; 0 for diatonic/excluded
    tied_attachment: bool
    to_midi: int | None           # None ⇔ unresolved
    chromatic_before: bool        # markedness in the source area's scale
    chromatic_after: bool | None  # ...in the target's (None while unresolved)
    zone: str | None              # classifier zone of the containing window
    evidence: list[dict]          # classifier readings, verbatim; [] if none
    alternatives: list[dict]      # e.g. the untaken tie attachment's image
    note: str | None
    range_corrected: bool = False   # the move was flipped an octave to stay in
                                    # 0..127 (audit #275) — forced by range, not
                                    # chosen, so it is reported not absorbed

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class AreaMap:
    """One structural area and the interscalar map chosen for it."""

    area_index: int
    start_beats: float
    end_beats: float
    source_tonic_pc: int
    source_mode: str
    target_root: int
    target_degrees: tuple[int, ...]
    overridden: bool              # True when area_targets supplied this map
    map: InterscalarMap

    def to_dict(self) -> dict:
        return {
            "area_index": self.area_index,
            "start_beats": self.start_beats,
            "end_beats": self.end_beats,
            "source_tonic_pc": self.source_tonic_pc,
            "source_mode": self.source_mode,
            "target_root": self.target_root,
            "target_degrees": list(self.target_degrees),
            "overridden": self.overridden,
            "map": self.map.to_dict(),
        }


@dataclass(frozen=True)
class TransformPlan:
    """The full, serializable record of what the transform will do and why.

    Every output pitch is in ``decisions`` — applying the plan reads nothing
    else — so editing a decision's ``to_midi`` (or resolving an unresolved one)
    IS the override mechanism. ``to_dict``/``plan_from_payload`` round-trip.
    """

    version: str
    home_tonic_pc: int
    home_mode: str
    target_scale_name: str | None
    target_degrees: tuple[int, ...]
    target_root: int
    chromatic_policy: str
    subdivisions: int
    areas: list[AreaMap]
    decisions: list[TransformDecision]
    notes_total: int
    notes_diatonic: int
    notes_chromatic: int
    notes_excluded: int
    unresolved: int

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "home_tonic_pc": self.home_tonic_pc,
            "home_mode": self.home_mode,
            "target_scale_name": self.target_scale_name,
            "target_degrees": list(self.target_degrees),
            "target_root": self.target_root,
            "chromatic_policy": self.chromatic_policy,
            "subdivisions": self.subdivisions,
            "areas": [a.to_dict() for a in self.areas],
            "decisions": [d.to_dict() for d in self.decisions],
            "notes_total": self.notes_total,
            "notes_diatonic": self.notes_diatonic,
            "notes_chromatic": self.notes_chromatic,
            "notes_excluded": self.notes_excluded,
            "unresolved": self.unresolved,
        }


@dataclass(frozen=True)
class TransformApplication:
    """The applied plan: the transformed piece plus what happened."""

    events: list[list]            # canonical [onset, dur, midi, velocity, voice]
    notes_changed: int
    notes_excluded: int
    absorbed_alterations: int     # chromatic_before and not chromatic_after

    def to_dict(self) -> dict:
        return {
            "events": [list(e) for e in self.events],
            "notes_changed": self.notes_changed,
            "notes_excluded": self.notes_excluded,
            "absorbed_alterations": self.absorbed_alterations,
        }


@dataclass(frozen=True)
class ModalTransformResult:
    """The one-shot result: the plan (inspect it) and its application."""

    plan: TransformPlan
    application: TransformApplication

    def to_dict(self) -> dict:
        return {"plan": self.plan.to_dict(),
                "application": self.application.to_dict()}


def _percussion_voice(voice) -> bool:
    return isinstance(voice, str) and voice.endswith("c9")


def _mode_degrees(mode: str, session) -> tuple[int, ...]:
    from ..io.loaders import load_scales

    return tuple(sorted(load_scales(session)[_MODE_SCALE[mode]].degrees))


def plan_modal_transform(
    sequence: Sequence,
    target_scale,
    *,
    target_root: int | None = None,
    area_targets: dict | None = None,
    chromatic: str = "rhetoric",
    subdivisions: int = 1,
    structural=None,
    chromatic_events=None,
    session=None,
) -> TransformPlan:
    """Build the plan: one typed decision per note, nothing applied.

    ``target_scale`` (catalog name or degree list) with ``target_root``
    defaulting to the home tonic — "switch the mode, keep the tonic".
    ``area_targets`` maps area index → ``(root_pc, scale)`` to override the
    tonic-interval-preserving default per area. ``chromatic`` is ``"rhetoric"``
    (preserve alterations; classifier evidence rides along) or ``"strict"``
    (a chromatic note in a classifier-**contested** window is left UNRESOLVED).
    ``structural``/``chromatic_events`` accept precomputed analyses so the plan
    is a pure function of a *stated* hypothesis. Raises on an empty sequence,
    an unknown policy, or a target of the wrong cardinality.
    """

    from .remap import _resolve_degrees
    from ..temporal.chromatic import classify_chromatic_events
    from ..temporal.structural_key import reduce_to_structural_keys

    if chromatic not in _CHROMATIC_POLICIES:
        raise ValueError(
            f"chromatic must be one of {_CHROMATIC_POLICIES}, got {chromatic!r}.")
    if not sequence.events:
        raise ValueError("plan_modal_transform needs a non-empty sequence.")

    target_name, target_degrees = _resolve_degrees(target_scale, session)

    result = structural if structural is not None else reduce_to_structural_keys(sequence)
    home_tonic, home_mode = result.home_tonic_pc, result.home_mode
    root = home_tonic if target_root is None else int(target_root) % 12

    classified = chromatic_events if chromatic_events is not None else (
        classify_chromatic_events(
            sequence, structural=result, subdivisions=subdivisions, session=session
        )
    )
    # window -> (zone, readings) for evidence attachment, bisect-ready (#256/L0003)
    ev_starts = [e.start_beat for e in classified.events]
    import bisect as _bisect

    def _window_evidence(beat: float):
        i = _bisect.bisect_right(ev_starts, beat + 1e-9) - 1
        if 0 <= i < len(classified.events):
            e = classified.events[i]
            if e.start_beat - 1e-9 <= beat < e.end_beat - 1e-9:
                return e.zone, [r.to_dict() for r in e.readings]
        return None, []

    # --- per-area interscalar maps ------------------------------------------
    overrides = dict(area_targets or {})
    areas: list[AreaMap] = []
    for i, area in enumerate(result.areas):
        if i in overrides:
            o_root, o_scale = overrides.pop(i)
            a_name, a_degrees = _resolve_degrees(o_scale, session)
            a_root, overridden = int(o_root) % 12, True
        else:
            # the most computable default: preserve the area tonic's interval
            # from home; use the one declared target collection
            a_degrees, a_name = target_degrees, target_name
            a_root = (root + (area.tonic_pc - home_tonic)) % 12
            overridden = False
        source_degrees = _mode_degrees(area.mode, session)
        imap = InterscalarMap(
            source_name=_MODE_SCALE[area.mode], source_degrees=source_degrees,
            source_root=area.tonic_pc,
            target_name=a_name, target_degrees=a_degrees, target_root=a_root,
        )
        areas.append(AreaMap(
            area_index=i, start_beats=area.start_beats, end_beats=area.end_beats,
            source_tonic_pc=area.tonic_pc, source_mode=area.mode,
            target_root=a_root, target_degrees=a_degrees,
            overridden=overridden, map=imap,
        ))
    if overrides:
        raise ValueError(
            f"area_targets refers to area indices {sorted(overrides)} but the "
            f"piece has {len(result.areas)} structural areas (0-based)."
        )

    # --- one decision per note ----------------------------------------------
    note_areas = area_indices(result.areas, [e.onset for e in sequence.events])
    decisions: list[TransformDecision] = []
    diatonic = chromatic_n = excluded = unresolved = 0

    for i, event in enumerate(sequence.events):
        midi = event.pitch.midi
        if _percussion_voice(event.voice):
            excluded += 1
            decisions.append(TransformDecision(
                index=i, voice=event.voice, onset=event.onset, from_midi=midi,
                kind="excluded", status="resolved", area_index=-1,
                degree=None, alteration=0, tied_attachment=False, to_midi=midi,
                chromatic_before=False, chromatic_after=None, zone=None,
                evidence=[], alternatives=[],
                note="percussion (MIDI channel 10) is never transformed",
            ))
            continue

        # clamp to the nearest area at the piece's edges (areas tile the middle)
        ai = note_areas[i]
        if ai is None:
            ai = 0 if event.onset < areas[0].start_beats else len(areas) - 1
        amap = areas[ai]
        imap = amap.map
        rel = (midi - imap.source_root) % 12
        degree_of = {d: k for k, d in enumerate(imap.source_degrees)}
        target_pcs = frozenset(
            (imap.target_root + d) % 12 for d in imap.target_degrees)

        if rel in degree_of:
            diatonic += 1
            degree, alteration, tied = degree_of[rel], 0, False
            zone, evidence = None, []
        else:
            chromatic_n += 1
            degree, alteration, tied = _attach_degree(rel, imap.source_degrees)
            zone, evidence = _window_evidence(event.onset)

        corrected = []          # set by _image when range forces an octave flip

        def _image(deg: int, alt: int) -> int:
            pc = (imap.target_root + imap.target_degrees[deg] + alt) % 12
            delta = _signed_delta(midi % 12, pc)
            new = midi + delta
            if not 0 <= new <= 127:
                corrected.append(True)
                new = midi + delta + (12 if delta < 0 else -12)
            return new

        to_midi = _image(degree, alteration)
        range_corrected = bool(corrected)
        corrected.clear()       # alternatives below must not pollute the flag
        alternatives: list[dict] = []
        if tied:
            # the untaken attachment: the equidistant degree ABOVE (negative
            # alteration) — recompute the candidate set and take the other side
            ties = [
                (k, _signed_delta(d, rel))
                for k, d in enumerate(imap.source_degrees)
                if abs(_signed_delta(d, rel)) == abs(alteration)
            ]
            for alt_degree, alt_alt in ties:
                if alt_degree == degree:
                    continue
                alternatives.append({
                    "label": "attach above (lowered-degree reading)",
                    "degree": alt_degree, "alteration": alt_alt,
                    "to_midi": _image(alt_degree, alt_alt),
                })

        strict_hold = (
            chromatic == "strict" and alteration != 0 and zone == "contested"
        )
        if strict_hold:
            unresolved += 1
        decisions.append(TransformDecision(
            index=i, voice=event.voice, onset=event.onset, from_midi=midi,
            kind="chromatic" if alteration != 0 or rel not in degree_of else "diatonic",
            status="unresolved" if strict_hold else "resolved",
            area_index=ai, degree=degree, alteration=alteration,
            tied_attachment=tied,
            to_midi=None if strict_hold else to_midi,
            chromatic_before=rel not in degree_of,
            chromatic_after=None if strict_hold else (to_midi % 12) not in target_pcs,
            zone=zone, evidence=evidence, alternatives=alternatives,
            range_corrected=range_corrected,
            note=("contested window: the classifier's readings disagree, and "
                  "the strict policy refuses to guess — resolve by editing "
                  "to_midi (the computed rhetoric image is "
                  f"{to_midi}) or re-plan with chromatic='rhetoric'")
            if strict_hold else None,
        ))

    return TransformPlan(
        version=PLAN_VERSION,
        home_tonic_pc=home_tonic, home_mode=home_mode,
        target_scale_name=target_name, target_degrees=target_degrees,
        target_root=root, chromatic_policy=chromatic,
        subdivisions=subdivisions,
        areas=areas, decisions=decisions,
        notes_total=len(sequence.events),
        notes_diatonic=diatonic, notes_chromatic=chromatic_n,
        notes_excluded=excluded, unresolved=unresolved,
    )


def apply_transform_plan(sequence: Sequence, plan) -> TransformApplication:
    """Execute a plan — and nothing else. Errors, never guesses.

    ``plan`` is a ``TransformPlan`` or its ``to_dict()`` payload (so an edited
    JSON round-trips). Validates the plan against the sequence — note count,
    per-note onset and source pitch — and refuses any unresolved decision.
    """

    if isinstance(plan, dict):
        plan = plan_from_payload(plan)

    if len(plan.decisions) != len(sequence.events):
        raise ValueError(
            f"plan has {len(plan.decisions)} decisions but the sequence has "
            f"{len(sequence.events)} notes — this plan was built for a "
            "different piece.")
    open_decisions = [d.index for d in plan.decisions if d.status == "unresolved"
                      or d.to_midi is None]
    if open_decisions:
        raise ValueError(
            f"plan has {len(open_decisions)} unresolved decision(s) at indices "
            f"{open_decisions[:10]} — resolve them (edit to_midi) before "
            "applying; a plan with open questions cannot be silently played.")

    events: list[list] = []
    changed = excluded = absorbed = 0
    for decision, event in zip(plan.decisions, sequence.events):
        if abs(decision.onset - event.onset) > 1e-9 or decision.from_midi != event.pitch.midi:
            raise ValueError(
                f"decision {decision.index} does not match the sequence "
                f"(expected onset {decision.onset}/midi {decision.from_midi}, "
                f"found {event.onset}/{event.pitch.midi}) — this plan was "
                "built for a different piece.")
        events.append([event.onset, event.duration, decision.to_midi,
                       event.pitch.velocity, event.voice])
        if decision.kind == "excluded":
            excluded += 1
        elif decision.to_midi != decision.from_midi:
            changed += 1
        if decision.chromatic_before and decision.chromatic_after is False:
            absorbed += 1

    return TransformApplication(
        events=events, notes_changed=changed, notes_excluded=excluded,
        absorbed_alterations=absorbed,
    )


def modal_transform(
    sequence: Sequence,
    target_scale,
    *,
    target_root: int | None = None,
    area_targets: dict | None = None,
    chromatic: str = "rhetoric",
    subdivisions: int = 1,
    session=None,
) -> ModalTransformResult:
    """One-shot: plan, then apply. The plan rides the result for inspection.

    With ``chromatic="strict"`` this raises whenever the plan holds unresolved
    decisions — use ``plan_modal_transform`` + ``apply_transform_plan`` to
    inspect and resolve them instead; the one-shot refuses to hide the hold.
    """

    plan = plan_modal_transform(
        sequence, target_scale, target_root=target_root,
        area_targets=area_targets, chromatic=chromatic,
        subdivisions=subdivisions, session=session,
    )
    return ModalTransformResult(
        plan=plan, application=apply_transform_plan(sequence, plan))


def plan_from_payload(payload: dict) -> TransformPlan:
    """Parse a plan dict (e.g. an edited ``to_dict`` round-trip). Strict."""

    if not isinstance(payload, dict):
        raise ValueError("plan payload must be a dict (TransformPlan.to_dict()).")
    version = payload.get("version")
    if version != PLAN_VERSION:
        raise ValueError(
            f"unknown plan version {version!r} (this engine reads {PLAN_VERSION}).")
    try:
        areas = [
            AreaMap(
                area_index=int(a["area_index"]),
                start_beats=float(a["start_beats"]),
                end_beats=float(a["end_beats"]),
                source_tonic_pc=int(a["source_tonic_pc"]),
                source_mode=str(a["source_mode"]),
                target_root=int(a["target_root"]),
                target_degrees=tuple(int(d) for d in a["target_degrees"]),
                overridden=bool(a["overridden"]),
                map=InterscalarMap(
                    source_name=a["map"]["source_name"],
                    source_degrees=tuple(int(d) for d in a["map"]["source_degrees"]),
                    source_root=int(a["map"]["source_root"]),
                    target_name=a["map"]["target_name"],
                    target_degrees=tuple(int(d) for d in a["map"]["target_degrees"]),
                    target_root=int(a["map"]["target_root"]),
                ),
            )
            for a in payload["areas"]
        ]
        decisions = [
            TransformDecision(
                index=int(d["index"]), voice=d["voice"], onset=float(d["onset"]),
                from_midi=int(d["from_midi"]), kind=str(d["kind"]),
                status=str(d["status"]), area_index=int(d["area_index"]),
                degree=None if d["degree"] is None else int(d["degree"]),
                alteration=int(d["alteration"]),
                tied_attachment=bool(d["tied_attachment"]),
                to_midi=None if d["to_midi"] is None else int(d["to_midi"]),
                chromatic_before=bool(d["chromatic_before"]),
                chromatic_after=(None if d["chromatic_after"] is None
                                 else bool(d["chromatic_after"])),
                zone=d["zone"], evidence=list(d["evidence"]),
                alternatives=list(d["alternatives"]), note=d["note"],
            )
            for d in payload["decisions"]
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"malformed plan payload: {exc}") from exc

    return TransformPlan(
        version=PLAN_VERSION,
        home_tonic_pc=int(payload["home_tonic_pc"]),
        home_mode=str(payload["home_mode"]),
        target_scale_name=payload["target_scale_name"],
        target_degrees=tuple(int(d) for d in payload["target_degrees"]),
        target_root=int(payload["target_root"]),
        chromatic_policy=str(payload["chromatic_policy"]),
        subdivisions=int(payload["subdivisions"]),
        areas=areas, decisions=decisions,
        notes_total=int(payload["notes_total"]),
        notes_diatonic=int(payload["notes_diatonic"]),
        notes_chromatic=int(payload["notes_chromatic"]),
        notes_excluded=int(payload["notes_excluded"]),
        unresolved=int(payload["unresolved"]),
    )


__all__ = [
    "PLAN_VERSION",
    "AreaMap",
    "ModalTransformResult",
    "TransformApplication",
    "TransformDecision",
    "TransformPlan",
    "apply_transform_plan",
    "modal_transform",
    "plan_from_payload",
    "plan_modal_transform",
]
