"""The no-match naming fallback (Audiology report, 2026-08-12).

Three real played chords returned `{chosen: null, alternatives: []}` and the
consumer UI honestly rendered "no suggested analyses". These tests pin the fix:
when no catalog quality matches, the result degrades to what the engine still
knows — set-class identity, maximal quality subsets, near-misses, containing
scales — instead of an empty shell. The three chords are the fixtures.
"""

from __future__ import annotations

from mts.analysis.naming import name_chord

F_C_GS_B = [5, 0, 8, 11]
D_E_F = [2, 4, 5]
D_A_F_GS = [2, 5, 8, 9]


def test_the_reported_chord_now_gets_suggested_analyses():
    n = name_chord(F_C_GS_B, None)
    assert n.chosen is None and n.unmatched is not None
    u = n.unmatched
    readings = {(s.root_pc, s.quality, tuple(s.added_pcs)) for s in u.quality_subsets}
    assert (5, "dim", (0,)) in readings           # F dim + added C
    assert (5, "min", (11,)) in readings          # F min + added B
    assert u.prime_form == [0, 1, 4, 7]
    assert any(s["name"] == "Minor Blues" and s["root_pc"] == 5
               for s in u.containing_scales)      # the blues hearing


def test_the_two_reported_tetrads_are_the_same_set_class():
    """The identity the empty shell could not even reveal: he played the same
    object twice in different keys."""
    a = name_chord(F_C_GS_B, None).unmatched
    b = name_chord(D_A_F_GS, None).unmatched
    assert a.prime_form == b.prime_form
    assert a.interval_vector == b.interval_vector
    # and the parallel readings appear at the parallel root
    assert {(s.root_pc, s.quality) for s in b.quality_subsets} == {(2, "dim"), (2, "min")}


def test_a_cluster_gets_facts_even_with_no_subset_reading():
    u = name_chord(D_E_F, None).unmatched
    assert u.quality_subsets == []                # no triad lives inside [0,1,3]
    assert u.near_quality_count > 0               # ...but one swap away, several
    assert any(n.root_pc == 2 and n.quality in ("dim", "min", "sus2")
               for n in u.near_qualities)
    assert u.containing_scale_count > 0
    assert u.prime_form == [0, 1, 3]


def test_subsets_are_maximal_and_aliases_collapsed():
    u = name_chord(F_C_GS_B, None).unmatched
    names = [s.quality for s in u.quality_subsets]
    assert "minor" not in names and "m" not in names and "o" not in names
    for s in u.quality_subsets:                   # no reported subset inside another
        assert not any(set(s.pcs) < set(t.pcs) for t in u.quality_subsets)


def test_near_misses_carry_the_swap_and_true_total():
    u = name_chord(F_C_GS_B, None).unmatched
    assert u.near_quality_count >= len(u.near_qualities)
    for n in u.near_qualities:
        assert n.swap_from_pc in F_C_GS_B and n.swap_to_pc not in F_C_GS_B
    # roots the player struck sort first
    struck = [n.root_pc in F_C_GS_B for n in u.near_qualities]
    assert struck == sorted(struck, reverse=True)


def test_matched_sets_are_unchanged():
    n = name_chord([0, 4, 7], None)
    assert n.chosen is not None and n.unmatched is None
    assert "unmatched" in n.to_dict() and n.to_dict()["unmatched"] is None


def test_context_does_not_suppress_the_fallback():
    from mts.analysis.key_induction import candidate_context
    from mts.analysis.results import KeyCandidate

    ctx = candidate_context(KeyCandidate(tonic_pc=0, mode="major", score=1.0))
    n = name_chord(D_E_F, ctx)
    assert n.chosen is None and n.unmatched is not None


def test_opt_out_for_tight_loops():
    n = name_chord(D_E_F, None, enrich_unmatched=False)
    assert n.chosen is None and n.unmatched is None
    # and segmentation uses it: spans stay lean (reason only, no enrichment)
    from mts.mcp.tools import _canonical_sequence
    from mts.temporal import segment_to_chords

    seq = _canonical_sequence([[0, 4, 60], [0, 4, 61], [0, 4, 62]])
    span = segment_to_chords(seq).spans[0]
    assert span.root_pc is None and span.reason


def test_deterministic():
    a = name_chord(F_C_GS_B, None).to_dict()
    b = name_chord(F_C_GS_B, None).to_dict()
    assert a == b


def test_mcp_parity():
    from mts.mcp import tools

    out = tools.name_pcs(pcs=F_C_GS_B)
    assert out["chosen"] is None
    u = out["unmatched"]
    assert set(u) >= {"prime_form", "quality_subsets", "near_qualities",
                      "near_quality_count", "containing_scales"}
