"""gap 26 slice 2 — modal_transform: analyze → plan → apply.

Pins the feature's contracts: a timeline of per-area maps (never one global
key), tonic-interval-preserving area targets with per-area overrides, drums
excluded visibly, chromatic rhetoric with classifier evidence, the strict
policy's honest hold, plan purity (apply reads nothing but the plan), and the
edit-then-apply override path.
"""

from __future__ import annotations

import json

import pytest

from mts.generate import (
    apply_transform_plan,
    modal_transform,
    plan_from_payload,
    plan_modal_transform,
)
from mts.mcp.tools import _canonical_sequence

MINOR = "Natural Minor"


def _tri(r, b, d=2):
    return [[b, d, 60 + r + i, 90, "m"] for i in (0, 4, 7)]


def _modulating(extra=()):
    """C major x3 rounds, then G major x3 — two structural areas."""
    ev, t = [], 0
    for r in (0, 5, 7, 0) * 3:
        ev += _tri(r, t); t += 2
    for r in (7, 0, 2, 7) * 3:
        ev += _tri(r, t); t += 2
    return _canonical_sequence(ev + list(extra))


def test_each_area_gets_its_own_map_tonic_interval_preserved():
    p = plan_modal_transform(_modulating(), MINOR, subdivisions=2)
    assert [(a.source_tonic_pc, a.target_root) for a in p.areas] == [(0, 0), (7, 7)]
    assert all(not a.overridden for a in p.areas)


def test_the_transform_is_per_area_not_one_global_key():
    """The failure mode every surveyed DAW ships, asserted against: the same
    source pitch maps differently depending on WHICH AREA it falls in."""
    r = modal_transform(_modulating(), MINOR, subdivisions=2)
    by = {}
    for d in r.plan.decisions:
        by.setdefault((d.area_index, d.from_midi % 12), d.to_midi % 12)
    # B: leading tone in the C area -> Bb; degree 3 in the G area -> Bb too...
    # use F#: chromatic in C area (stays F# under rhetoric), diatonic degree 7
    # of G major -> F in G minor.
    assert by[(1, 6)] == 5                       # F# -> F inside the G area
    # E: degree 3 in C area -> Eb; degree 6 in G area -> Eb (b6 of G minor)
    assert by[(0, 4)] == 3 and by[(1, 4)] == 3


def test_percussion_is_excluded_visibly_never_transformed():
    drums = [[0.0, 0.5, 36, 110, "t2c9"], [2.0, 0.5, 38, 100, "t2c9"]]
    r = modal_transform(_modulating(extra=drums), MINOR, subdivisions=2)
    excluded = [d for d in r.plan.decisions if d.kind == "excluded"]
    assert len(excluded) == 2
    for d in excluded:
        assert d.to_midi == d.from_midi and "percussion" in d.note
    assert r.application.notes_excluded == 2
    out_drums = [e for e in r.application.events if e[4] == "t2c9"]
    assert [e[2] for e in out_drums] == [36, 38]


def test_chromatic_note_carries_classifier_evidence_and_alternative():
    p = plan_modal_transform(
        _modulating(extra=[[3.0, 1, 61, 80, "m"]]), MINOR, subdivisions=2)
    d = next(x for x in p.decisions if x.from_midi == 61)
    assert d.kind == "chromatic" and d.chromatic_before
    assert d.tied_attachment and d.alternatives
    assert d.alternatives[0]["to_midi"] is not None
    assert d.zone in ("confident", "contested")


def test_strict_holds_contested_notes_and_apply_refuses():
    seq = _modulating(extra=[[3.0, 1, 61, 80, "m"]])
    p = plan_modal_transform(seq, MINOR, chromatic="strict", subdivisions=2)
    held = [d for d in p.decisions if d.status == "unresolved"]
    assert p.unresolved == len(held) >= 1
    for d in held:
        assert d.to_midi is None and d.zone == "contested"
        assert "refuses to guess" in d.note
    with pytest.raises(ValueError, match="unresolved"):
        apply_transform_plan(seq, p)
    with pytest.raises(ValueError, match="unresolved"):
        modal_transform(seq, MINOR, chromatic="strict", subdivisions=2)


def test_editing_the_plan_is_the_override_path():
    seq = _modulating(extra=[[3.0, 1, 61, 80, "m"]])
    p = plan_modal_transform(seq, MINOR, chromatic="strict", subdivisions=2)
    payload = json.loads(json.dumps(p.to_dict()))     # a real JSON round-trip
    for d in payload["decisions"]:
        if d["status"] == "unresolved":
            d["status"], d["to_midi"], d["chromatic_after"] = "resolved", 60, False
    app = apply_transform_plan(seq, payload)
    edited = next(e for e in app.events if e[0] == 3.0 and e[1] == 1)
    assert edited[2] == 60                            # the human's call, applied


def test_apply_is_pure_reads_nothing_but_the_plan():
    seq = _modulating()
    p = plan_modal_transform(seq, MINOR, subdivisions=2)
    a = apply_transform_plan(seq, p)
    b = apply_transform_plan(seq, plan_from_payload(json.loads(json.dumps(p.to_dict()))))
    assert a.to_dict() == b.to_dict()
    one_shot = modal_transform(seq, MINOR, subdivisions=2)
    assert one_shot.application.to_dict() == a.to_dict()


def test_apply_rejects_a_plan_for_a_different_piece():
    seq = _modulating()
    p = plan_modal_transform(seq, MINOR, subdivisions=2)
    other = _modulating(extra=[[99.0, 1, 60, 90, "m"]])
    with pytest.raises(ValueError, match="different piece"):
        apply_transform_plan(other, p)
    # same count, different content
    shifted = _canonical_sequence(
        [[d.onset, 1, d.from_midi + 1, 90, "m"] for d in p.decisions])
    with pytest.raises(ValueError, match="different piece"):
        apply_transform_plan(shifted, p)


def test_area_targets_override_and_bad_index_errors():
    seq = _modulating()
    p = plan_modal_transform(seq, MINOR, area_targets={1: (3, "Lydian")},
                             subdivisions=2)
    assert p.areas[1].overridden and p.areas[1].target_root == 3
    assert p.areas[1].map.target_name == "Lydian"
    assert not p.areas[0].overridden
    with pytest.raises(ValueError, match="area indices"):
        plan_modal_transform(seq, MINOR, area_targets={9: (0, MINOR)})


def test_wrong_cardinality_target_errors():
    with pytest.raises(ValueError, match="equal cardinality"):
        plan_modal_transform(_modulating(), "Major Pentatonic")


def test_preservation_and_registration_contract():
    seq = _modulating(extra=[[3.0, 1, 61, 80, "m"]])
    r = modal_transform(seq, MINOR, subdivisions=2)
    assert len(r.application.events) == r.plan.notes_total
    for src, out in zip(seq.events, r.application.events):
        assert out[0] == src.onset and out[1] == src.duration
        assert out[3] == src.pitch.velocity and out[4] == src.voice
        assert abs(out[2] - src.pitch.midi) <= 6


def test_markedness_is_tracked_and_absorption_tallied():
    # Eb over a C-major-only piece: chromatic before; in C minor it is diatonic
    ev, t = [], 0
    for r in (0, 5, 7, 0) * 2:
        ev += _tri(r, t); t += 2
    seq = _canonical_sequence(ev + [[3.0, 1, 63, 80, "m"]])
    r = modal_transform(seq, MINOR)
    d = next(x for x in r.plan.decisions if x.from_midi == 63)
    assert d.chromatic_before and d.chromatic_after is False
    assert r.application.absorbed_alterations == 1


def test_plan_versioning_is_enforced():
    seq = _modulating()
    payload = plan_modal_transform(seq, MINOR).to_dict()
    payload["version"] = "modal-transform-plan.999"
    with pytest.raises(ValueError, match="unknown plan version"):
        apply_transform_plan(seq, payload)


def test_deterministic():
    seq = _modulating(extra=[[3.0, 1, 61, 80, "m"]])
    a = modal_transform(seq, MINOR, subdivisions=2).to_dict()
    b = modal_transform(seq, MINOR, subdivisions=2).to_dict()
    assert a == b


def test_empty_and_bad_policy_error():
    with pytest.raises(ValueError, match="non-empty"):
        plan_modal_transform(_canonical_sequence([]), MINOR)
    with pytest.raises(ValueError, match="chromatic must be"):
        plan_modal_transform(_modulating(), MINOR, chromatic="vibes")


def test_mcp_parity_all_three_tools():
    from mts.mcp import tools

    ev = []
    t = 0
    for r in (0, 5, 7, 0) * 2:
        ev += [[t, 2, 60 + r + i, 90, "m"] for i in (0, 4, 7)]; t += 2
    plan = tools.plan_modal_transform(events=ev, target_scale=MINOR)
    assert plan["version"] == "modal-transform-plan.1" and plan["decisions"]
    applied = tools.apply_modal_transform_plan(events=ev, plan=plan)
    assert applied["notes_changed"] > 0
    one = tools.modal_transform(events=ev, target_scale=MINOR)
    assert one["application"]["events"] == applied["events"]


# --- the round-trip ratchet (audit #286) ----------------------------------------
#
# #286: `range_corrected` was added to TransformDecision (audit #275) and never
# added to the hand-written parser, so it survived to_dict() and was silently
# dropped on the way back in. The existing round-trip test PASSED throughout —
# its fixture never produced a boundary flip, so the field was always at its
# default on both sides. A round-trip test is only as good as the non-default
# values its fixture happens to exercise (HYPERSAW-002: "the test that covers
# the fix is itself uncovered").
#
# So this does not depend on a fixture reaching a path. It MUTATES every field
# of every serialized dataclass to a non-default value and asserts the parser
# carries it back. The value table is explicit and must cover every field:
# adding a field to the dataclass without adding a row here FAILS, which forces
# whoever adds it to look at the parser in the same change.

import dataclasses as _dc

from mts.generate.modal import AreaMap, TransformDecision, TransformPlan

_DECISION_MUTATIONS = {
    "index": 7, "voice": "mutated-voice", "onset": 9.5, "from_midi": 61,
    "kind": "chromatic", "status": "unresolved", "area_index": 3, "degree": 5,
    "alteration": -2, "tied_attachment": True, "to_midi": 58,
    "chromatic_before": True, "chromatic_after": True, "zone": "contested",
    "evidence": [{"label": "sentinel"}], "alternatives": [{"to_midi": 1}],
    "note": "sentinel-note", "range_corrected": True,
}
_AREA_MUTATIONS = {
    "area_index": 4, "start_beats": 1.5, "end_beats": 99.5,
    "source_tonic_pc": 5, "source_mode": "minor", "target_root": 11,
    "target_degrees": (0, 1, 3, 5, 7, 8, 10), "overridden": True,
    "map": None,   # nested dataclass — covered by the InterscalarMap equality below
}
_PLAN_MUTATIONS = {
    "version": None,  # pinned: the parser REJECTS any other version, by design
    "home_tonic_pc": 9, "home_mode": "minor", "target_scale_name": "Dorian",
    "target_degrees": (0, 2, 3, 5, 7, 9, 10), "target_root": 2,
    "chromatic_policy": "strict", "subdivisions": 4, "areas": None,
    "decisions": None, "notes_total": 101, "notes_diatonic": 50,
    "notes_chromatic": 40, "notes_excluded": 11, "unresolved": 3,
}


def _plan_payload():
    ev = [[0, 1, 2, 90, "m"], [1, 1, 60, 90, "m"], [2, 1, 64, 90, "m"]]
    return plan_modal_transform(_canonical_sequence(ev), "Ionian",
                                target_root=6).to_dict()


def test_mutation_tables_cover_every_serialized_field():
    """Adding a field without a mutation row fails HERE, loudly — not silently
    in production the way range_corrected did."""
    for cls, table in ((TransformDecision, _DECISION_MUTATIONS),
                       (AreaMap, _AREA_MUTATIONS),
                       (TransformPlan, _PLAN_MUTATIONS)):
        missing = {f.name for f in _dc.fields(cls)} - set(table)
        assert not missing, (
            f"{cls.__name__} gained field(s) {sorted(missing)} with no mutation "
            "row — add one, and check plan_from_payload parses it (audit #286)")


def test_every_decision_field_survives_the_round_trip():
    for name, value in _DECISION_MUTATIONS.items():
        payload = _plan_payload()
        payload["decisions"][0][name] = list(value) if isinstance(value, tuple) else value
        parsed = plan_from_payload(payload).decisions[0]
        assert getattr(parsed, name) == value, f"TransformDecision.{name} was dropped"


def test_every_area_field_survives_the_round_trip():
    for name, value in _AREA_MUTATIONS.items():
        if value is None:
            continue
        payload = _plan_payload()
        payload["areas"][0][name] = list(value) if isinstance(value, tuple) else value
        parsed = plan_from_payload(payload).areas[0]
        assert getattr(parsed, name) == value, f"AreaMap.{name} was dropped"
    base = _plan_payload()
    assert plan_from_payload(base).areas[0].map.to_dict() == base["areas"][0]["map"]


def test_every_plan_field_survives_the_round_trip():
    for name, value in _PLAN_MUTATIONS.items():
        if value is None:
            continue
        payload = _plan_payload()
        payload[name] = list(value) if isinstance(value, tuple) else value
        parsed = plan_from_payload(payload)
        assert getattr(parsed, name) == value, f"TransformPlan.{name} was dropped"


def test_the_reported_regression_round_trips():
    """#286 verbatim: [True, False, False] in must be [True, False, False] out."""
    payload = _plan_payload()
    before = [d["range_corrected"] for d in payload["decisions"]]
    assert before == [True, False, False]
    after = [d.range_corrected for d in plan_from_payload(payload).decisions]
    assert after == before


def test_a_pre_275_plan_without_the_field_still_parses():
    """Back-compat: plans serialized before the field existed must load."""
    payload = _plan_payload()
    for d in payload["decisions"]:
        del d["range_corrected"]
    parsed = plan_from_payload(payload)
    assert all(d.range_corrected is False for d in parsed.decisions)
