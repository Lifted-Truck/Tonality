"""gap 25 slice 2 — chromatic-event classification (the composite).

Pins the four pieces the slice wired together (special_function read in the
area's key, the interior-vs-boundary position test, the tonicization overlap,
the zone delimiter) and — more importantly — the contracts that keep the output
honest: plural readings, no single label inside the contested band, and no
spurious boundary at the piece's own edges.
"""

from __future__ import annotations

import pytest

from mts.mcp.tools import _canonical_sequence
from mts.temporal import classify_chromatic_events


def _tri(root_pc, beat, dur=2):
    return [[beat, dur, 60 + root_pc + i] for i in (0, 4, 7)]


def _borrowed_and_applied():
    """C major with a borrowed iv (F-A♭-C) and an applied V/V (D7 → G)."""
    ev, t = [], 0
    for r in (0, 5, 7, 0):
        ev += _tri(r, t); t += 2
    ev += [[t, 2, 65], [t, 2, 68], [t, 2, 72]]; t += 2      # F minor — borrowed iv
    ev += _tri(0, t); t += 2
    ev += [[t, 2, 62], [t, 2, 66], [t, 2, 69], [t, 2, 72]]; t += 2  # D7 = V/V
    ev += _tri(7, t); t += 2                                 # ...resolving to G
    ev += _tri(0, t); t += 2
    return _canonical_sequence(ev)


def _modulating():
    """A long C major section, then a long E♭ major one — an unrelated key."""
    ev, t = [], 0
    for r in (0, 5, 7, 0) * 3:
        ev += _tri(r, t); t += 2
    for r in (3, 8, 10, 3) * 3:
        ev += _tri(r, t); t += 2
    return _canonical_sequence(ev)


def test_borrowed_chord_is_recognized_from_the_parallel_mode():
    r = classify_chromatic_events(_borrowed_and_applied(), subdivisions=2)
    borrowed = [e for e in r.events if e.single_label == "borrowed_mixture"]
    assert borrowed, "the borrowed iv must be found"
    assert borrowed[0].foreign_pcs == [8]            # A♭, the ♭6
    assert borrowed[0].zone == "confident"


def test_special_function_is_read_in_the_area_key_not_the_global_one():
    """The seam wiring: D7 is a secondary dominant *of this area's* key."""
    r = classify_chromatic_events(_borrowed_and_applied(), subdivisions=2)
    applied = [e for e in r.events if e.function_category == "secondary_dominant"]
    assert applied, "V/V must be flagged by name_chord's special-function seam"
    assert applied[0].root_pc == 2 and applied[0].area_tonic_pc == 0


def test_the_realized_resolution_is_a_second_signal():
    """The composite's value-add: a sequential test single-chord naming can't make."""
    r = classify_chromatic_events(_borrowed_and_applied(), subdivisions=2)
    applied = next(e for e in r.events if e.function_category == "secondary_dominant")
    reading = next(x for x in applied.readings if x.label == "secondary_dominant")
    assert len(reading.signals) == 2
    assert any("realizes the predicted resolution" in s for s in reading.signals)


def test_diatonic_chords_are_not_events_but_are_counted():
    r = classify_chromatic_events(_borrowed_and_applied(), subdivisions=2)
    assert r.diatonic_chords > 0
    assert r.chords_examined == r.diatonic_chords + len(r.events)
    for e in r.events:
        assert e.foreign_pcs, "an event must have pcs outside its area's key"


def test_the_pieces_own_edges_are_not_key_area_boundaries():
    """MEASURED BUG, now pinned: scoring the outer edges as seams put a spurious
    `modulation` reading on the opening chord of every single-area piece."""
    r = classify_chromatic_events(_borrowed_and_applied(), subdivisions=2)
    assert r.events, "fixture must produce events for this test to mean anything"
    for e in r.events:
        assert e.position == "interior"
        assert e.beats_to_boundary is None      # a single-area piece has no seam
        assert all(x.label != "modulation" for x in e.readings)


def test_a_real_seam_produces_a_boundary_reading_with_its_confirmation():
    r = classify_chromatic_events(_modulating(), subdivisions=2)
    at_seam = [e for e in r.events if e.position == "boundary"]
    assert at_seam, "the C→E♭ seam must be found"
    mod = next(x for x in at_seam[0].readings if x.label == "modulation")
    assert any("cadence-confirmed in its own key" in s for s in mod.signals)


def test_competing_readings_refuse_a_single_label():
    """The honest refusal, made mechanical — the whole point of the slice."""
    r = classify_chromatic_events(_modulating(), subdivisions=2)
    contested = [e for e in r.events if e.zone == "contested"]
    assert contested
    for e in contested:
        assert e.single_label is None
        assert e.no_label_reason and "cost model" in e.no_label_reason
        assert e.contested_reasons


def test_readings_are_ordered_by_signal_count_and_are_plural():
    r = classify_chromatic_events(_modulating(), subdivisions=2)
    e = next(x for x in r.events if len(x.readings) > 1)
    counts = [len(x.signals) for x in e.readings]
    assert counts == sorted(counts, reverse=True)


def test_ambiguity_is_a_zone_not_a_label():
    """`genuinely_ambiguous` must never appear beside a real hypothesis."""
    for seq in (_borrowed_and_applied(), _modulating()):
        r = classify_chromatic_events(seq, subdivisions=2)
        for e in r.events:
            labels = {x.label for x in e.readings}
            assert "genuinely_ambiguous" not in labels
            assert "ambiguous" not in labels


def test_the_zone_cites_its_coordinates_and_the_versioned_prior():
    r = classify_chromatic_events(_modulating(), subdivisions=2)
    e = r.events[0]
    coords = e.zone_coordinates
    assert coords["prior_version"] == r.prior_version
    for field in ("readings", "boundary_threshold_beats", "area_duration_beats",
                  "min_modulation_beats", "floor_tolerance_beats"):
        assert field in coords


def test_the_knife_edge_floor_contests_on_its_own():
    """A stated policy knob, not a discovered one: widen it and the zone flips."""
    seq = _borrowed_and_applied()
    wide = classify_chromatic_events(seq, subdivisions=2, floor_tolerance_beats=100.0)
    assert wide.contested_events == len(wide.events)
    for e in wide.events:
        assert any("knife edge" in reason for reason in e.contested_reasons)
        assert e.single_label is None
    narrow = classify_chromatic_events(seq, subdivisions=2)
    assert narrow.confident_events > 0        # the same music, the stated band


def test_tallies_partition_the_events():
    r = classify_chromatic_events(_modulating(), subdivisions=2)
    assert r.confident_events + r.contested_events == len(r.events)


def test_empty_sequence_raises():
    with pytest.raises(ValueError, match="non-empty"):
        classify_chromatic_events(_canonical_sequence([]))


def test_deterministic():
    seq = _modulating()
    assert (classify_chromatic_events(seq, subdivisions=2).to_dict()
            == classify_chromatic_events(seq, subdivisions=2).to_dict())


def test_reusing_upstream_results_gives_the_same_answer():
    from mts.temporal import confirm_key_areas, reduce_to_structural_keys

    seq = _modulating()
    structural = reduce_to_structural_keys(seq)
    confirmation = confirm_key_areas(seq, structural=structural, subdivisions=2)
    a = classify_chromatic_events(seq, subdivisions=2)
    b = classify_chromatic_events(
        seq, structural=structural, confirmation=confirmation, subdivisions=2
    )
    assert a.to_dict() == b.to_dict()


def test_mcp_parity():
    from mts.mcp import tools

    ev, t = [], 0
    for r in (0, 5, 7, 0):
        ev += _tri(r, t); t += 2
    ev += [[t, 2, 65], [t, 2, 68], [t, 2, 72]]; t += 2
    ev += _tri(0, t); t += 2
    out = tools.classify_chromatic_events(events=[list(e) for e in ev], subdivisions=2)
    assert out["events"]
    assert set(out["events"][0]) >= {
        "readings", "zone", "single_label", "zone_coordinates", "foreign_pcs"
    }
