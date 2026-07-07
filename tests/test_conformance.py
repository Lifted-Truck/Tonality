"""Golden-file conformance harness (Decision 10 — the C++ port's executable spec).

Replays a curated call against every MCP tool and compares the full JSON
result to a committed golden file, with float tolerance. Two jobs:

1. **Today**: regression armor. Any change to engine output — intended or
   not — fails here first. An *intended* change (e.g. a new prior version)
   regenerates the goldens in the same PR, making output changes reviewable
   as diffs.
2. **For the migration**: the goldens are language-neutral. A C++ engine
   that reproduces these files (within the same tolerances) is conformant —
   the suite is the spec, per Decision 10.

Regenerate with (from the repo root):

    PYTHONPATH=. .venv/bin/python3.13 tests/test_conformance.py --regenerate

No exclusions (RE-4b): the two pipeline tools run over a committed fixture
MIDI (``golden/fixtures/pipeline.mid``) referenced via a ``$FIXTURES``
placeholder — the golden stores the placeholder, never a machine path, and
the results embed no paths (the old exclusion reason had gone stale). The
coverage ratchet is therefore total: a new tool without a case fails the
suite, full stop.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from mts.mcp import tools

GOLDEN_PATH = Path(__file__).parent / "golden" / "conformance.json"

# RE-4b: no exclusions — the two pipeline tools are covered via a committed
# fixture MIDI, referenced with a machine-independent $FIXTURES placeholder
# (resolved at call time; the golden stores the placeholder, and the results
# embed no paths — verified when the exclusion was retired).
EXCLUDED_TOOLS: set[str] = set()
FIXTURES_DIR = Path(__file__).parent / "golden" / "fixtures"

REL_TOL = 1e-9
ABS_TOL = 1e-12


def _modulating_events():
    events = []
    for base, tonic in ((0, 60), (16, 66)):  # C major, then F# major
        for cycle in (0, 8):
            events.append([base + cycle, 8, tonic - 12])  # tonic pedal
            for offset, chord_root in ((0, 0), (2, 5), (4, 7), (6, 0)):
                onset = base + cycle + offset
                events += [[onset, 2, tonic + chord_root + iv] for iv in (0, 4, 7)]
    return events


def _satb_events():
    return [
        [0, 2, 48, "bass"], [2, 2, 50, "bass"],
        [0, 2, 55, "tenor"], [2, 2, 57, "tenor"],
        [0, 2, 64, "alto"], [2, 2, 62, "alto"],
        [0, 2, 72, "soprano"], [2, 2, 69, "soprano"],
    ]


def _swung_events():
    events = []
    for b in range(4):
        events += [[b, 2 / 3, 60], [b + 2 / 3, 1 / 3, 62]]
    return events


def _induction_corpus():
    # Hand-built, language-neutral (no RNG): 6 identical 2-voice pieces whose
    # transitions induction mines into a small soft ruleset (Phase 4.6).
    moments = [(60, 64), (62, 66), (64, 68), (62, 69), (60, 64)]
    piece = []
    for i, (a, b) in enumerate(moments):
        piece += [[float(i), 1.0, a, "v0"], [float(i), 1.0, b, "v1"]]
    return [list(piece) for _ in range(6)]


def _induction_merge_corpus():
    # Parallel thirds + non-parallel landings on the octave (ic 0) and fifth
    # (ic 7) — triggers the disjunction (`in`) merge pass. RNG-free.
    moments = [
        (60, 64), (62, 66), (64, 68), (62, 62), (64, 68),
        (62, 69), (60, 64), (62, 66), (64, 68), (62, 62), (64, 68), (62, 69), (60, 64),
    ]
    piece = []
    for i, (a, b) in enumerate(moments):
        piece += [[float(i), 1.0, a, "v0"], [float(i), 1.0, b, "v1"]]
    return [list(piece) for _ in range(8)]


def _meter_change_events():
    # 8 bars of 4/4 then 8 bars of 3/4 (accented); the local tracker splits them.
    events = []
    t = 0.0
    for _ in range(8):
        for beat, vel in enumerate((110, 50, 70, 50)):
            events.append([t + beat, 0.5, 60, vel])
        t += 4
    for _ in range(8):
        for beat, vel in enumerate((110, 50, 70)):
            events.append([t + beat, 0.5, 60, vel])
        t += 3
    return events


def _groove_loop():
    # Swung, accented loop: [onset, dur, midi, velocity] (groove event format).
    events = []
    for b in range(2):
        events += [[b, 0.5, 60, 100], [b + 0.58, 0.5, 62, 64]]
    return events


def _groove_template():
    return tools.extract_groove(_groove_loop(), base_unit_beats=0.5, loop_length_beats=2.0)


def _quantized_groove_loop():
    return [[i * 0.5, 0.5, 60 + (i % 2) * 2, 80] for i in range(4)]


# One deterministic call per tool (a tool may have several). Inputs chosen to
# exercise rich output paths: ambiguity, evidence lists, compound meters, etc.
CASES: list[tuple[str, dict]] = [
    ("list_scales", {}),
    ("list_chord_qualities", {}),
    ("parse_chord", {"text": "C3[0,4,7]"}),
    ("chord_analysis", {"root": "C", "quality": "maj7", "tonic": "C"}),
    ("scale_analysis", {"scale_name": "Dorian", "tonic": 2}),
    ("set_class_info", {"pcs": [0, 4, 7, 10]}),
    ("interpretations", {"pcs": [0, 4, 7, 9]}),
    ("catalog_containment", {"pcs": [0, 4, 7]}),
    (
        "search_identities",
        {"constraints": {"cardinality": 7, "contains": [0, 4, 7],
                         "no_consecutive_semitones": True}},
    ),
    ("chord_in_key", {"root": "D", "quality": "min7", "tonic": "C", "key_name": "Ionian"}),
    (
        "name_pcs",
        {"pcs": [0, 4, 7, 9], "tonic": "A", "key_name": "Aeolian",
         "realization_midi": [45, 60, 64, 67]},
    ),
    # default profile is now tkp-cbms.1 (A6 brief-10 flip).
    ("key_induction", {"pc_weights": [4.0, 0, 1.0, 0, 2.0, 1.0, 0, 3.0, 0, 1.0, 0, 1.0]}),
    # the legacy kk-1982.1 profile, pinned for parity (A5/A7 can still select it).
    ("key_induction", {"pc_weights": [4.0, 0, 1.0, 0, 2.0, 1.0, 0, 3.0, 0, 1.0, 0, 1.0],
                       "profile_version": "kk-1982.1"}),
    # 3/4 accent content tagged 4/4 — estimation ranks 3/4 and flags disagreement.
    (
        "meter_estimation",
        {"events": [[b * 3 + o, 0.5, 60, v]
                    for b in range(8) for o, v in ((0, 100), (1, 40), (2, 40))],
         "numerator": 4, "denominator": 4},
    ),
    # local meter tracking: a 4/4 → 3/4 change split into regions (gap 11 follow-on).
    ("meter_tracking", {"events": _meter_change_events(), "window_beats": 12.0, "hop_beats": 3.0}),
    # Eb-major-solo shape (Audiology brief-3 case): a relative near-tie the
    # tonal-hierarchy signals resolve to Eb major.
    ("relative_key", {"pc_weights": [2.0, 0, 2.0, 4.0, 0, 1.0, 0, 3.0, 1.0, 0, 3.0, 0]}),
    (
        "name_pcs_in_inferred_keys",
        {"pcs": [0, 4, 7, 9],
         "pc_weights": [4.0, 0, 1.0, 0, 2.0, 1.0, 0, 3.0, 0, 1.0, 0, 1.0]},
    ),
    ("key_tracking", {"events": _modulating_events()}),
    # key-inertia continuity prior on the same modulating track (A6 brief-13).
    ("key_tracking", {"events": _modulating_events(), "key_inertia": True}),
    # structural reduction of the same modulating track (C → F#); default anchor
    # is frame_weighted (A6 brief-8).
    ("structural_keys", {"events": _modulating_events()}),
    # the legacy most_prevalent_region anchor, pinned for parity.
    ("structural_keys", {"events": _modulating_events(), "anchor_method": "most_prevalent_region"}),
    # Relative-key tie-breaker on: a window the bare argmax reads as C major but
    # the G# leading tone flips to A minor (Audiology brief-3 follow-on).
    (
        "key_tracking",
        {"events": [[0.0, 3.3, 60], [0.0, 2.3, 64], [0.0, 2.0, 67], [0.0, 2.0, 69],
                    [0.0, 2.0, 68], [0.0, 1.0, 62], [0.0, 1.0, 65], [0.0, 1.0, 71]],
         "window_beats": 4.0, "hop_beats": 2.0, "disambiguate_relative": True},
    ),
    # Smoothing on: a weak 1-window foreign blip between C-major spans is absorbed
    # (Audiology brief-3, Finding C). Non-overlapping windows for an exact blip.
    (
        "key_tracking",
        {"events": (
            [[float(t), 2.0, m] for t in range(0, 16, 2) for m in (60, 64, 67)]
            + [[16.0, 2.0, m] for m in (62, 65, 71)] + [[18.0, 2.0, m] for m in (62, 65, 71)]
            + [[float(t), 2.0, m] for t in range(20, 36, 2) for m in (60, 64, 67)]
         ),
         "window_beats": 4.0, "hop_beats": 4.0, "smoothing": True},
    ),
    (
        "cadences",
        {"chords": [[2, "min"], [7, "maj"], [0, "maj"]], "tonic": "C", "mode": "major"},
    ),
    (
        "next_chord",
        {"current": ["G", "7"], "tonic": "C", "mode": "major",
         "history": [["D", "min"]]},
    ),
    # vl_neighbours on: chromatic mediants etc. surface as candidates (gap 14).
    (
        "next_chord",
        {"current": ["C", "maj"], "tonic": "C", "mode": "major", "vl_neighbours": True},
    ),
    ("voice_leading_distance", {"source_pcs": [0, 4, 7], "target_pcs": [5, 9, 0]}),
    ("realized_voice_leading", {"source_midi": [60, 64, 67], "target_midi": [59, 62, 67]}),
    ("voice_pair_motion", {"events": _satb_events()}),
    (
        "melodic_analysis",
        {"events": [[0, 1, 60], [1, 1, 64], [2, 1, 62], [3, 1, 60], [4, 1, 59], [5, 1, 60]],
         "harmony": [[0, 6, [0, 4, 7]]]},
    ),
    ("rhythmic_analysis", {"events": [[0, 1.5, 60], [1.5, 2.5, 62], [4, 1, 64]]}),
    ("rhythmic_analysis", {"events": [[1.5, 0.5, 60], [3.0, 1.5, 62], [4.5, 0.75, 64]],
                           "numerator": 6, "denominator": 8}),
    ("swing_analysis", {"events": _swung_events()}),
    (
        "coalesce_events",
        {"events": [[0, 2, 60], [0.013, 1.99, 64], [0.021, 1.98, 67],
                    [2, 2, 65], [2.008, 1.99, 69], [2.017, 1.98, 72]],
         "onset_window_beats": 0.05},
    ),
    ("extract_groove", {"events": _groove_loop(), "base_unit_beats": 0.5,
                        "loop_length_beats": 2.0}),
    (
        "apply_groove",
        {"events": _quantized_groove_loop(), "template": _groove_template(),
         "quantize": 1.0, "timing": 1.0, "random": 0.0, "velocity": 1.0,
         "amount": 1.0},
    ),
    (
        "validate_ruleset",
        {"ruleset": {"name": "x", "version": "1",
                     "rules": [{"id": "r", "family": "nope", "forbid": {"x": 1}}]}},
    ),
    (
        "evaluate_ruleset",
        {
            "ruleset": {
                "name": "counterpoint-smoke", "version": "t.1",
                "rules": [
                    {"id": "no-parallel-perfects", "family": "voice_motion",
                     "where": {"motion": "parallel"},
                     "forbid": {"interval_class_to": {"in": [0, 7]}},
                     "polarity": "hard"},
                    {"id": "leaps-resolve-by-step", "family": "melody",
                     "where": {"approach_class": "leap"},
                     "require": {"departure_class": {"in": ["step", "unison"]}},
                     "polarity": "soft", "weight": 2.0},
                ],
            },
            "events": _satb_events(),
        },
    ),
    ("induce_rules", {"corpus": _induction_corpus(), "family": "voice_motion"}),
    ("induce_rules", {"corpus": _induction_merge_corpus(), "family": "voice_motion"}),
    (
        "combine_rulesets",
        {"rulesets": [
            {"name": "a", "version": "1", "rules": [
                {"id": "no-parallel", "family": "voice_motion",
                 "forbid": {"motion": "parallel"}, "polarity": "hard"}]},
            {"name": "b", "version": "1", "rules": [
                {"id": "no-syncopation", "family": "rhythm",
                 "forbid": {"is_syncopated": True}, "polarity": "hard"}]},
        ], "name": "cp", "version": "1"},
    ),
    (
        "specialize_ruleset",
        {"base": {"name": "a", "version": "1", "rules": [
            {"id": "prefer-steps", "family": "melody",
             "require": {"departure_class": {"in": ["step", "unison"]}},
             "polarity": "soft", "weight": 2.0}]},
         "overlay": {"name": "b", "version": "1", "rules": [
            {"id": "no-syncopation", "family": "rhythm",
             "forbid": {"is_syncopated": True}, "polarity": "hard"}]},
         "name": "strict", "version": "1"},
    ),
    (
        "compare_rulesets",
        {"ruleset_a": {"name": "a", "version": "1", "rules": [
            {"id": "no-parallel", "family": "voice_motion",
             "forbid": {"motion": "parallel"}, "polarity": "hard"}]},
         "ruleset_b": {"name": "b", "version": "1", "rules": [
            {"id": "must-parallel", "family": "voice_motion",
             "require": {"motion": "parallel"}, "polarity": "hard"}]}},
    ),
    (
        "keyboard_view",
        {"low_midi": 60, "high_midi": 72, "tonic": "D", "scale_name": "Dorian",
         "active_midi": [62, 65, 69]},
    ),
    (
        "bracelet_view",
        {"pcs": [0, 4, 7], "tonic": "C", "scale_name": "Ionian"},
    ),
    ("tonnetz_view", {"pcs": [0, 3, 6, 9]}),  # dim7 — symmetric, many edges
    ("colour_content_view", {"pcs": [0, 4, 7]}),  # brief-15 colour resultants
    # brief-17 voicing-continuous tonal orientation (register-aware, bass-weighted).
    ("tonal_orientation_view", {"midi_notes": [60, 64, 67], "octave_decay": 0.5}),
    (
        "chord_network",
        {"chords": [["C", "maj"], ["C", "aug"], ["C", "min"], ["E", "min"], ["A", "min"]],
         "max_distance": 1},
    ),
    ("voicing_analysis", {"midi_notes": [48, 64, 67, 72], "root": "C"}),
    ("voicing_suggestions", {"root": "C", "quality": "maj7"}),
    ("quality_comparison", {"quality_a": "maj7", "quality_b": "min7"}),
    ("quality_brief", {"quality": "maj7"}),
    # RE-4b: the two pipeline tools, over the committed fixture (the golden
    # stores the $FIXTURES placeholder, never a machine path).
    (
        "midi_file_analysis",
        {"path": "$FIXTURES/pipeline.mid", "include_meter_regions": True},
    ),
    ("piano_roll_view", {"path": "$FIXTURES/pipeline.mid"}),
]


def _run_case(tool_name: str, kwargs: dict):
    resolved = {
        key: value.replace("$FIXTURES", str(FIXTURES_DIR))
        if isinstance(value, str) and value.startswith("$FIXTURES")
        else value
        for key, value in kwargs.items()
    }
    return getattr(tools, tool_name)(**resolved)


def _assert_matches(expected, actual, path=""):
    if isinstance(expected, float) or isinstance(actual, float):
        assert isinstance(actual, (int, float)) and isinstance(expected, (int, float)), (
            f"{path}: type mismatch ({type(expected).__name__} vs {type(actual).__name__})"
        )
        assert math.isclose(float(expected), float(actual), rel_tol=REL_TOL, abs_tol=ABS_TOL), (
            f"{path}: {expected!r} != {actual!r}"
        )
    elif isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: expected dict, got {type(actual).__name__}"
        assert set(expected) == set(actual), (
            f"{path}: key mismatch (missing {set(expected) - set(actual)}, "
            f"extra {set(actual) - set(expected)})"
        )
        for key in expected:
            _assert_matches(expected[key], actual[key], f"{path}.{key}")
    elif isinstance(expected, (list, tuple)):
        assert isinstance(actual, (list, tuple)), f"{path}: expected list"
        assert len(expected) == len(actual), (
            f"{path}: length {len(expected)} != {len(actual)}"
        )
        for i, (e, a) in enumerate(zip(expected, actual)):
            _assert_matches(e, a, f"{path}[{i}]")
    else:
        assert expected == actual, f"{path}: {expected!r} != {actual!r}"


def _load_golden() -> list[dict]:
    if not GOLDEN_PATH.exists():
        pytest.fail(
            f"Golden file missing: {GOLDEN_PATH}. Generate it with "
            "`python tests/test_conformance.py --regenerate`."
        )
    return json.loads(GOLDEN_PATH.read_text())["cases"]


def test_every_tool_has_a_conformance_case():
    covered = {name for name, _ in CASES}
    expected = {fn.__name__ for fn in tools.TOOLS} - EXCLUDED_TOOLS
    assert expected <= covered, f"Tools missing conformance cases: {expected - covered}"


def test_golden_file_matches_case_list():
    golden = _load_golden()
    assert [(g["tool"], g["kwargs"]) for g in golden] == [
        (name, json.loads(json.dumps(kwargs))) for name, kwargs in CASES
    ], "Golden file is out of date with CASES — regenerate."


@pytest.mark.parametrize(
    "index,case", list(enumerate(CASES)), ids=[f"{i:02d}-{n}" for i, (n, _) in enumerate(CASES)]
)
def test_conformance(index, case):
    tool_name, kwargs = case
    golden = _load_golden()
    expected = golden[index]["result"]
    actual = json.loads(json.dumps(_run_case(tool_name, kwargs)))
    _assert_matches(expected, actual, path=tool_name)


def _regenerate() -> None:
    GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "description": (
            "Golden conformance outputs for the MCP tool surface (Decision 10). "
            "Language-neutral spec: any engine reproducing these (floats within "
            "rel 1e-9 / abs 1e-12) is conformant. Regenerate ONLY for intended "
            "output changes, in the same PR, so diffs are reviewable."
        ),
        "float_rel_tol": REL_TOL,
        "float_abs_tol": ABS_TOL,
        "cases": [
            {
                "tool": name,
                "kwargs": kwargs,
                "result": json.loads(json.dumps(_run_case(name, kwargs))),
            }
            for name, kwargs in CASES
        ],
    }
    GOLDEN_PATH.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(f"Wrote {len(CASES)} cases to {GOLDEN_PATH}")


if __name__ == "__main__":
    import sys

    if "--regenerate" in sys.argv:
        _regenerate()
    else:
        print(__doc__)
