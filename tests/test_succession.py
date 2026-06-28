"""Next-chord recommendation (gap 14, slice 1): ranked, tagged candidates.

Decision 7 applied to succession — plural, evidenced, reproducible. The signals
are all computable today (functional roles + root motion + voice-leading + DFT
color); the historical/corpus tags are a deferred follow-on.
"""

from __future__ import annotations

import pytest

from mts.analysis import recommend_next_chord, tag_transition
from mts.io.loaders import load_succession_weights


def _by_chord(rec, root_pc, quality):
    for c in rec.candidates:
        if c.root_pc == root_pc and c.quality == quality:
            return c
    return None


# --- the flagship case: V7 in C major ---------------------------------------------------


def test_dominant_resolves_to_tonic_on_top():
    rec = recommend_next_chord((7, "7"), tonic_pc=0, mode="major")
    top = rec.candidates[0]
    assert top.root_pc == 0  # I
    assert {"authentic", "dominant_resolution", "descending_fifth"} <= set(top.tags)
    assert top.cadence == "authentic"
    assert rec.current_roman == "V7" and rec.current_role == "dominant"


def test_deceptive_is_tagged_and_ranks_below_authentic():
    rec = recommend_next_chord((7, "7"), tonic_pc=0, mode="major")
    vi = _by_chord(rec, 9, "min")
    one = _by_chord(rec, 0, "maj")
    assert vi is not None and vi.cadence == "deceptive"
    assert "deceptive" in vi.tags
    assert one.score > vi.score  # authentic resolution outranks deception


def test_every_candidate_is_ranked_and_evidenced():
    rec = recommend_next_chord((7, "7"), tonic_pc=0, mode="major")
    assert [c.rank for c in rec.candidates] == list(range(1, len(rec.candidates) + 1))
    assert all(c.evidence for c in rec.candidates)
    assert rec.weights_version == "succession.1"


# --- functional-succession tag definitions ----------------------------------------------


def test_descending_fifth_fires_only_on_root_interval_five():
    rec = recommend_next_chord((0, "maj"), tonic_pc=0, mode="major")
    for c in rec.candidates:
        assert ("descending_fifth" in c.tags) == (c.root_interval == 5)


def test_prolongation_requires_same_role():
    # Current I (tonic): vi (also tonic-function) is a prolongation; V is not.
    rec = recommend_next_chord((0, "maj"), tonic_pc=0, mode="major")
    vi = _by_chord(rec, 9, "min")
    five = _by_chord(rec, 7, "maj")
    assert "prolongation" in vi.tags
    assert "prolongation" not in five.tags


def test_retrogression_dominant_to_predominant():
    # Current V → ii (predominant): the textbook retrogression, scored negatively.
    t = tag_transition((7, "maj"), (2, "min"), tonic_pc=0, mode="major")
    assert "retrogression" in t.tags
    assert any(e.signal == "retrogression" and e.weight < 0 for e in t.evidence)


# --- voice-leading tags -----------------------------------------------------------------


def test_parsimonious_with_plr_detail():
    # C major → A minor: relative (R), 2 common tones, distance 2.
    t = tag_transition((0, "maj"), (9, "min"), tonic_pc=0, mode="major")
    assert "parsimonious" in t.tags
    assert t.common_tones == 2
    detail = next(e.detail for e in t.evidence if e.signal == "parsimonious")
    assert detail.startswith("R")


def test_chromatic_mediant_fires_on_same_quality_third_apart():
    # C major → E major: root a major third up, 1 common tone, same quality.
    t = tag_transition((0, "maj"), (4, "maj"), tonic_pc=0, mode="major")
    assert "chromatic_mediant" in t.tags
    assert t.common_tones == 1
    assert t.modal_label is None  # out of the diatonic vocabulary


def test_common_tone_weight_scales_with_count():
    t = tag_transition((0, "maj"), (0, "maj7"), tonic_pc=0, mode="major")
    ct = next(e for e in t.evidence if e.signal == "common_tone")
    assert ct.weight == pytest.approx(load_succession_weights().weights["common_tone"] * t.common_tones)


# --- color is reported but not scored ---------------------------------------------------


def test_color_shift_is_reported_and_unscored():
    rec = recommend_next_chord((7, "7"), tonic_pc=0, mode="major")
    assert all(c.color_shift >= 0.0 for c in rec.candidates)
    # color_shift never appears as a scored evidence signal under succession.1
    assert all(
        all(e.signal != "color_shift" for e in c.evidence) for c in rec.candidates
    )


# --- borrowed (minor) -------------------------------------------------------------------


def test_borrowed_candidate_carries_the_tag_in_minor():
    rec = recommend_next_chord((0, "min"), tonic_pc=0, mode="minor")
    v7 = _by_chord(rec, 7, "7")  # the harmonic-minor dominant
    assert v7 is not None
    assert "borrowed" in v7.tags


# --- applied dominant -------------------------------------------------------------------


def test_applied_dominant_resolves_down_a_fifth_to_a_diatonic_degree():
    # D7 (V/V) in C major: a secondary-dominant-shaped chord onto G (degree 7).
    t = tag_transition((0, "maj"), (2, "7"), tonic_pc=0, mode="major")
    assert "applied_dominant" in t.tags


# --- vocabulary override ----------------------------------------------------------------


def test_qualities_override_widens_the_vocabulary():
    core = recommend_next_chord((0, "maj"), tonic_pc=0, mode="major")
    wide = recommend_next_chord(
        (0, "maj"), tonic_pc=0, mode="major",
        qualities=["maj", "min", "dim", "maj6", "maj7", "min7", "7", "maj9"],
    )
    assert len(wide.candidates) > len(core.candidates)
    assert any(c.quality == "maj6" for c in wide.candidates)


# --- guards + determinism ---------------------------------------------------------------


def test_modal_key_raises():
    with pytest.raises(ValueError, match="major/minor only"):
        recommend_next_chord((0, "maj"), tonic_pc=0, mode="dorian")


def test_tonic_out_of_range_raises():
    with pytest.raises(ValueError, match="out of range"):
        recommend_next_chord((0, "maj"), tonic_pc=12, mode="major")


def test_deterministic_ordering():
    a = recommend_next_chord((7, "7"), tonic_pc=0, mode="major")
    b = recommend_next_chord((7, "7"), tonic_pc=0, mode="major")
    assert [(c.root_pc, c.quality, c.score, c.rank) for c in a.candidates] == [
        (c.root_pc, c.quality, c.score, c.rank) for c in b.candidates
    ]


# --- VL-neighbour candidate generation (gap 14 follow-on) -----------------------


def test_vl_neighbours_surface_chromatic_mediants():
    # In C major, E major is a chromatic mediant — outside the diatonic functional
    # vocabulary, so it never arises as a default candidate; vl_neighbours generates
    # it (reachable by smooth voice-leading) and the chromatic_mediant tag fires.
    base = recommend_next_chord((0, "maj"), tonic_pc=0, mode="major")
    assert not any((c.root_pc, c.quality) == (4, "maj") for c in base.candidates)

    rec = recommend_next_chord((0, "maj"), tonic_pc=0, mode="major", vl_neighbours=True)
    e_major = [c for c in rec.candidates if (c.root_pc, c.quality) == (4, "maj")]
    assert len(e_major) == 1
    c = e_major[0]
    assert "vl_neighbour" in c.tags          # provenance
    assert "chromatic_mediant" in c.tags     # the tag that now fires
    assert c.vl_distance <= 3
    assert c.role is None and c.modal_label is None  # out-of-vocabulary, named honestly


def test_vl_neighbour_provenance_tag_does_not_score():
    # vl_neighbour is informational (weight 0) — it must not change a candidate's
    # score vs. the same transition tagged via the functional path.
    rec = recommend_next_chord((0, "maj"), tonic_pc=0, mode="major", vl_neighbours=True)
    e_major = next(c for c in rec.candidates if (c.root_pc, c.quality) == (4, "maj"))
    vln_ev = [e for e in e_major.evidence if e.signal == "vl_neighbour"]
    assert len(vln_ev) == 1 and vln_ev[0].weight == 0.0


def test_vl_neighbours_default_off_is_unchanged():
    a = recommend_next_chord((0, "maj"), tonic_pc=0, mode="major")
    b = recommend_next_chord((0, "maj"), tonic_pc=0, mode="major", vl_neighbours=False)
    assert a.to_dict() == b.to_dict()


def test_vl_max_distance_bounds_the_neighbourhood():
    # A tighter bound yields fewer (or equal) generated candidates; a looser one more.
    tight = recommend_next_chord((0, "maj"), tonic_pc=0, mode="major",
                                 vl_neighbours=True, vl_max_distance=1)
    loose = recommend_next_chord((0, "maj"), tonic_pc=0, mode="major",
                                 vl_neighbours=True, vl_max_distance=4)
    assert len(tight.candidates) <= len(loose.candidates)


def test_vl_neighbours_deterministic():
    a = recommend_next_chord((0, "maj"), tonic_pc=0, mode="major", vl_neighbours=True)
    b = recommend_next_chord((0, "maj"), tonic_pc=0, mode="major", vl_neighbours=True)
    assert a.to_dict() == b.to_dict()
