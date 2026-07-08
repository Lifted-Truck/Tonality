"""Harmonic segmentation (gap B slice-2a): note Sequence → chord stream.

Oracle: hand-built block-chord progressions in C major on a 4/4 grid. Covers the
metric-grid reduction, the salience threshold (non-harmonic tones dropped), the
error-not-guess contract (unnameable / rest windows surfaced, never faked), the
meter-aware bar helper, and the end-to-end feed into evaluate / induce.
"""

import pytest

from mts.mcp.tools import _canonical_sequence
from mts.rules import evaluate, induce_ruleset
from mts.temporal import segment_to_chords
from mts.temporal.meter import MeterChange, MeterMap, TimeSignature


def _bars(bars, base=60, dur=4.0):
    """One block chord per 4/4 bar; each pc a note of length `dur`."""
    events = []
    for bar, pcs in enumerate(bars):
        for pc in pcs:
            events.append([bar * 4.0, dur, base + pc])
    return events


CMAJ_I_IV_V_I = [[0, 4, 7], [5, 9, 12], [7, 11, 14], [0, 4, 7]]


# --- the metric-grid reduction ------------------------------------------------

def test_recovers_block_chord_progression():
    seg = segment_to_chords(_canonical_sequence(_bars(CMAJ_I_IV_V_I)))
    assert seg.key == (0, "major") and seg.key_inferred is True
    assert seg.chords == [(0, "maj"), (5, "maj"), (7, "maj"), (0, "maj")]
    assert [s.bar for s in seg.spans] == [0, 1, 2, 3]


def test_passing_tone_is_dropped_by_salience():
    # a brief D (0.25 beat) inside a bar of C-E-G must not perturb the label.
    events = _bars([[0, 4, 7]]) + [[1.0, 0.25, 62]]
    seg = segment_to_chords(_canonical_sequence(events))
    assert seg.spans[0].salient_pcs == (0, 4, 7)
    assert seg.chords == [(0, "maj")]


def test_supplied_key_is_not_inferred():
    seg = segment_to_chords(_canonical_sequence(_bars(CMAJ_I_IV_V_I)), key=(0, "major"))
    assert seg.key_inferred is False and seg.key_margin == 0.0
    assert seg.chords == [(0, "maj"), (5, "maj"), (7, "maj"), (0, "maj")]


def test_consecutive_identical_chords_collapse():
    # C major held across two bars → one stream entry, but two spans.
    seg = segment_to_chords(_canonical_sequence(_bars([[0, 4, 7], [0, 4, 7]])))
    assert seg.chords == [(0, "maj")]
    assert len(seg.spans) == 2 and all(s.quality == "maj" for s in seg.spans)


def test_rest_window_is_surfaced_not_faked():
    # bar 0 = C maj, bar 1 = silence, bar 2 = G maj. The empty bar is a recorded
    # rest with no chord — never invented.
    events = _bars([[0, 4, 7]]) + [[8.0, 4.0, 67], [8.0, 4.0, 71], [8.0, 4.0, 74]]
    seg = segment_to_chords(_canonical_sequence(events))
    assert seg.spans[1].root_pc is None and "rest" in seg.spans[1].reason
    assert seg.chords == [(0, "maj"), (7, "maj")]  # the rest is skipped in the stream


def test_unnameable_window_is_surfaced_not_faked():
    # a lone sustained pitch names no catalog chord → root_pc None + a reason.
    seg = segment_to_chords(_canonical_sequence([[0.0, 4.0, 60]]), key=(0, "major"))
    assert seg.spans[0].root_pc is None and seg.spans[0].reason is not None
    assert seg.chords == []


def test_subdivisions_splits_each_bar():
    seg = segment_to_chords(_canonical_sequence(_bars(CMAJ_I_IV_V_I)), subdivisions=2)
    assert len(seg.spans) == 8  # two windows per bar
    # each half-bar still reads the bar's chord (whole-note block), so the stream
    # still collapses to the four chords.
    assert seg.chords == [(0, "maj"), (5, "maj"), (7, "maj"), (0, "maj")]


def test_determinism():
    seq = _canonical_sequence(_bars(CMAJ_I_IV_V_I))
    assert segment_to_chords(seq).to_dict() == segment_to_chords(seq).to_dict()


def test_empty_sequence_raises():
    with pytest.raises(ValueError, match="non-empty"):
        segment_to_chords(_canonical_sequence([]))


def test_subdivisions_below_one_raises():
    with pytest.raises(ValueError, match="subdivisions"):
        segment_to_chords(_canonical_sequence(_bars(CMAJ_I_IV_V_I)), subdivisions=0)


# --- the meter-aware bar helper -----------------------------------------------

def test_bar_spans_constant_meter():
    spans = MeterMap.constant(4, 4).bar_spans(16.0)
    assert spans == [(0.0, 4.0, 0), (4.0, 8.0, 1), (8.0, 12.0, 2), (12.0, 16.0, 3)]


def test_bar_spans_clamps_final_partial_bar():
    spans = MeterMap.constant(4, 4).bar_spans(10.0)
    assert spans == [(0.0, 4.0, 0), (4.0, 8.0, 1), (8.0, 10.0, 2)]  # last bar clamped


def test_bar_spans_meter_change():
    # 2 bars of 4/4 then 3/4 — bar widths change at the meter boundary.
    meter = MeterMap((MeterChange(0, TimeSignature(4, 4)), MeterChange(2, TimeSignature(3, 4))))
    spans = meter.bar_spans(14.0)
    assert spans == [
        (0.0, 4.0, 0), (4.0, 8.0, 1),          # 4/4
        (8.0, 11.0, 2), (11.0, 14.0, 3),       # 3/4
    ]


# --- end to end: segmentation feeds the harmony family ------------------------

def test_segmented_chords_feed_evaluate():
    seg = segment_to_chords(_canonical_sequence(_bars(CMAJ_I_IV_V_I)))
    rs = {"name": "t", "version": "1", "rules": [
        {"id": "v", "family": "harmony", "where": {"role": "dominant"},
         "require": {"next_role": "tonic"}, "polarity": "hard"}]}
    report = evaluate(rs, _canonical_sequence([]), chords=seg.chords, key=seg.key)
    assert report.hard_rules_hold is True


def test_segmented_chords_feed_harmony_induction():
    # segment several progressions, mine the resulting chord corpus.
    corpus = []
    for prog in ([[0, 4, 7], [5, 9, 12], [7, 11, 14], [0, 4, 7]],
                 [[0, 4, 7], [9, 12, 16], [7, 11, 14], [0, 4, 7]]):
        seg = segment_to_chords(_canonical_sequence(_bars(prog)))
        corpus.append((seg.chords, seg.key))
    result = induce_ruleset(family="harmony", chord_corpus=corpus)
    assert result.family == "harmony" and result.pieces == 2


def test_mcp_segment_chords_matches_engine():
    from mts.mcp import tools

    events = _bars(CMAJ_I_IV_V_I) + [[1.0, 0.25, 62]]
    engine = segment_to_chords(_canonical_sequence(events)).to_dict()
    assert tools.segment_chords(events) == engine
