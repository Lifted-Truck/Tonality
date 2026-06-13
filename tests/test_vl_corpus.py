"""The Solve et Coagula gap-6 voice-leading corpus, adopted into the suite.

Delivered via ``integrations/solve-coagula/brief-2.md`` (2026-06-12) per the
offer recorded in ROADMAP gap 6: 286 five-voice ``realize()`` transitions —
258 replayed from their golden chronicles, 28 synthetic edge cases — with
doubling and register-clamp coverage. ``sortedDisplacement`` is the optimal
non-crossing pairing distance for equal 5→5 multisets, i.e. exactly what
``voice_leading_realized`` must return; their ``greedyCost`` is their
engine's internal pre-clamp scoring and is deliberately NOT asserted here
(it is not a metric on the resulting pair — see the brief).

The corpus is regression-grade external evidence: it pins our metric against
an independent implementation's verified-golden output. If this file fails,
either the metric changed (a versioned-policy event — `doubling.1`) or the
corpus artifact was modified; both deserve a human look.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mts.analysis import voice_leading_realized
from mts.core.pitch import Pitch
from mts.core.realization import Realization

CORPUS_PATH = (
    Path(__file__).parent.parent / "integrations" / "solve-coagula" / "vl-corpus.json"
)


@pytest.fixture(scope="module")
def corpus():
    return json.loads(CORPUS_PATH.read_text())


def _realization(midis):
    return Realization(tuple(Pitch.from_midi(m) for m in midis), root_pc=None)


def test_corpus_artifact_is_the_pinned_version(corpus):
    assert corpus["schema"] == "solve-coagula.vl-corpus/1"
    assert len(corpus["cases"]) == 286
    flags: dict[str, int] = {}
    for case in corpus["cases"]:
        for flag in case["flags"]:
            flags[flag] = flags.get(flag, 0) + 1
    # the brief's stated coverage, pinned
    assert flags == {"clampMin": 8, "clampMax": 6, "pcDoubling": 141, "midiDoubling": 9}


def test_every_transition_agrees_with_voice_leading_realized(corpus):
    checked = 0
    for case in corpus["cases"]:
        if case["from"] is None:
            continue  # the opening chord has no transition
        result = voice_leading_realized(
            _realization(case["from"]), _realization(case["realized"])
        )
        assert result.distance == case["sortedDisplacement"], (
            f"{case['id']}: engine {result.distance} != "
            f"corpus {case['sortedDisplacement']} (flags: {case['flags']})"
        )
        assert result.policy == "doubling.1"
        checked += 1
    assert checked == 285  # 286 cases minus the single from-null opener
