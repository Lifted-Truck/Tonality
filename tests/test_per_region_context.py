"""Gap 13: per-region analytical context in the dataset pipeline."""

from __future__ import annotations

import pytest

from mts.analysis import AnalyticalContext
from mts.core.pitch import Pitch
from mts.dataset.builders import dataset_from_sequence
from mts.io.loaders import load_scales
from mts.temporal import Event, Sequence, track_keys


def _modulating_sequence():
    """16 beats C major then 16 beats F# major (tonic pedals keep it decisive)."""
    events = []
    for base, tonic in ((0, 60), (16, 66)):
        for cycle in (0, 8):
            events.append(Event(base + cycle, 8, Pitch.from_midi(tonic - 12)))
            for offset, root in ((0, 0), (2, 5), (4, 7), (6, 0)):
                onset = base + cycle + offset
                events += [
                    Event(onset, 2, Pitch.from_midi(tonic + root + iv))
                    for iv in (0, 4, 7)
                ]
    return Sequence.from_events(events)


def test_segments_are_conditioned_on_their_local_key():
    sequence = _modulating_sequence()
    regions = track_keys(sequence)
    dataset = dataset_from_sequence(sequence, key_regions=regions)

    early = [r for r in dataset.records if r.placement.onset_beats < 12]
    late = [r for r in dataset.records if r.placement.onset_beats >= 20]
    assert early and late
    assert all(r.analytical_context.tonic_pc == 0 for r in early)
    assert all(r.analytical_context.tonic_pc == 6 for r in late)  # F# region
    # the region's confidence rides on every record's snapshot
    assert all(r.analytical_context.margin is not None for r in early + late)
    assert early[0].analytical_context.margin == pytest.approx(
        regions.regions[0].mean_margin
    )


def test_naming_follows_the_local_context():
    sequence = _modulating_sequence()
    dataset = dataset_from_sequence(sequence, key_regions=track_keys(sequence))
    # an F#-major tonic segment in the late region names with root F#, in key
    late_tonics = [
        r for r in dataset.records
        if r.placement.onset_beats >= 20 and set(r.identity.pcs) == {6, 10, 1}
    ]
    assert late_tonics
    chosen = late_tonics[0].analysis.naming.chosen.interpretation
    assert chosen.root_pc == 6
    assert late_tonics[0].analysis.naming.context.tonic_pc == 6


def test_segments_outside_regions_fall_back_to_the_global_context():
    sequence = Sequence.from_events(
        [Event(float(i * 2), 2.0, Pitch.from_midi(m)) for i, m in
         enumerate([60, 64, 67, 60])]
    )
    scales = load_scales()
    global_context = AnalyticalContext(tonic_pc=0, key=scales["Ionian"])
    regions = track_keys(_modulating_sequence())
    # hand-build a tracking result whose regions end before this material
    import dataclasses

    short = dataclasses.replace(
        regions,
        regions=[dataclasses.replace(regions.regions[0], start_beats=100.0,
                                     end_beats=200.0)],
    )
    dataset = dataset_from_sequence(
        sequence, analytical_context=global_context, key_regions=short
    )
    assert all(r.analytical_context.tonic_pc == 0 for r in dataset.records)
    assert all(r.analytical_context.margin is None for r in dataset.records)


def test_without_regions_behavior_is_unchanged():
    sequence = _modulating_sequence()
    scales = load_scales()
    global_context = AnalyticalContext(tonic_pc=0, key=scales["Ionian"])
    dataset = dataset_from_sequence(sequence, analytical_context=global_context)
    assert all(r.analytical_context.tonic_pc == 0 for r in dataset.records)
    assert all(r.analytical_context.margin is None for r in dataset.records)
