"""Tests for melodic tendency (gap 19): anchoring attraction over frozen tables.

Every strength oracle is hand-computable from the formula
``(s_target/s_source)/d**2`` with the melodic-tendency.1 stability values
(frozen from kk-1982.1): major C=6.35 D=3.48 E=4.38 F=4.09 G=5.19 A=3.66
B=2.88 F#=2.52 Bb=2.29 C#=2.23; minor C=6.33 Eb=5.38 G=4.75 Bb=3.34 B=3.17
F=3.53. The pedagogy the numbers must reproduce is stated on each test.
"""

import pytest

from mts.analysis import melodic_tendency


# --- the pedagogy oracles ------------------------------------------------------

def test_leading_tone_resolves_up_strongest():
    # ti -> do is the canonical tendency: (6.35/2.88)/1 = 2.2049.
    result = melodic_tendency(11, tonic_pc=0, mode="major")
    top = result.resolutions[0]
    assert (top.target_pc, top.strength) == (0, 2.2049)
    assert result.source_degree == 7
    # ...and ti barely wants to fall: (3.66/2.88)/4 = 0.3177.
    assert result.resolutions[1].target_pc == 9
    assert result.resolutions[1].strength == 0.3177


def test_ti_do_tops_in_every_major_key():
    # Transposition covariance: the leading tone pulls to the tonic everywhere.
    for tonic in range(12):
        result = melodic_tendency(degree=7, tonic_pc=tonic, mode="major")
        assert result.resolutions[0].target_pc == tonic
        assert result.resolutions[0].strength == 2.2049


def test_fa_falls_to_mi_more_than_it_rises_to_sol():
    # The 4-3 sigh: (4.38/4.09)/1 = 1.0709 vs (5.19/4.09)/4 = 0.3172.
    result = melodic_tendency(5, tonic_pc=0, mode="major")
    strengths = {r.target_pc: r.strength for r in result.resolutions}
    assert strengths[4] == 1.0709
    assert strengths[7] == 0.3172
    assert result.resolutions[0].target_pc == 4


def test_stable_tones_barely_tend():
    # sol's strongest pull is weaker than any tendency tone's top pull.
    sol = melodic_tendency(7, tonic_pc=0, mode="major")
    ti = melodic_tendency(11, tonic_pc=0, mode="major")
    fa = melodic_tendency(5, tonic_pc=0, mode="major")
    assert sol.resolutions[0].strength < fa.resolutions[0].strength
    assert sol.resolutions[0].strength < ti.resolutions[0].strength


def test_minor_mode_reorders_the_third():
    # In C minor, fa's top resolution flips to me (Eb): (5.38/3.53)/4 = 0.381
    # beats sol (4.75/3.53)/4 = 0.3364 — the profile knows minor's third is heavy.
    result = melodic_tendency(5, tonic_pc=0, mode="minor")
    assert result.resolutions[0].target_pc == 3
    assert result.resolutions[0].strength == 0.381


def test_harmonic_minor_leading_tone_is_a_strong_chromatic_source():
    # B is chromatic in C natural minor, but pulls hard to C: (6.33/3.17)/1 = 1.9968.
    result = melodic_tendency(11, tonic_pc=0, mode="minor")
    assert result.source_degree is None  # chromatic source
    assert result.resolutions[0].target_pc == 0
    assert result.resolutions[0].strength == 1.9968


# --- the stability table (the root>third replacement) ---------------------------

def test_stability_table_is_complete_and_descending():
    result = melodic_tendency(7, tonic_pc=0, mode="major")
    assert len(result.stability) == 12
    values = [e.value for e in result.stability]
    assert values == sorted(values, reverse=True)
    # C > G > E > F heads the major table; chromatic pcs carry degree None.
    assert [e.pc for e in result.stability[:4]] == [0, 7, 4, 5]
    assert all(e.degree is None for e in result.stability if not e.in_key)


def test_stability_tops_the_tonic_in_both_modes():
    for mode in ("major", "minor"):
        result = melodic_tendency(degree=5, tonic_pc=4, mode=mode)  # key of E
        assert result.stability[0].pc == 4
        assert result.stability[0].degree == 1


# --- chord anchoring (fork C) ----------------------------------------------------

def test_chord_tone_targets_boost_by_exactly_the_prior_factor():
    plain = melodic_tendency(2, tonic_pc=0, mode="major")
    boosted = melodic_tendency(2, tonic_pc=0, mode="major", chord_pcs=[0, 4, 7])
    p = {r.target_pc: r.strength for r in plain.resolutions}
    b = {r.target_pc: r.strength for r in boosted.resolutions}
    # D is not a chord tone; C and E are: both pulls scale by 1.5.
    assert b[0] == pytest.approx(p[0] * 1.5, abs=2e-4)
    assert b[4] == pytest.approx(p[4] * 1.5, abs=2e-4)


def test_chord_tone_source_is_more_settled():
    # E is a chord tone: its own stability rises, so its pulls weaken by 1/1.5.
    plain = melodic_tendency(4, tonic_pc=0, mode="major")
    over_chord = melodic_tendency(4, tonic_pc=0, mode="major", chord_pcs=[0, 4, 7])
    p = {r.target_pc: r.strength for r in plain.resolutions}
    b = {r.target_pc: r.strength for r in over_chord.resolutions}
    assert b[5] == pytest.approx(p[5] / 1.5, abs=2e-4)  # E->F, F not a chord tone


def test_chord_flags_appear_only_with_chord_context():
    plain = melodic_tendency(2, tonic_pc=0, mode="major")
    assert all(r.is_chord_tone is None for r in plain.resolutions)
    boosted = melodic_tendency(2, tonic_pc=0, mode="major", chord_pcs=[0, 4, 7])
    flags = {r.target_pc: r.is_chord_tone for r in boosted.resolutions}
    assert flags[0] is True and flags[4] is True


# --- target policies (fork B: parameterized, diatonic default) --------------------

def test_default_policy_excludes_chromatic_targets():
    result = melodic_tendency(11, tonic_pc=0, mode="major")
    assert result.targets == "diatonic_steps"
    assert all(r.in_key for r in result.resolutions)


def test_chromatic_steps_policy_adds_out_of_key_neighbors():
    # B under chromatic_steps gains Bb (2.29/2.88 = 0.7951) and C# (0.1936),
    # both flagged in_key=False; the diatonic ranking is undisturbed.
    result = melodic_tendency(11, tonic_pc=0, mode="major", targets="chromatic_steps")
    by_pc = {r.target_pc: r for r in result.resolutions}
    assert by_pc[10].strength == 0.7951 and by_pc[10].in_key is False
    assert by_pc[1].strength == 0.1936 and by_pc[1].in_key is False
    assert result.resolutions[0].target_pc == 0  # ti->do still tops


def test_chromatic_source_resolves_to_adjacent_scale_members():
    # F# in C major: G (5.19/2.52 = 2.0595) then F (4.09/2.52 = 1.623).
    result = melodic_tendency(6, tonic_pc=0, mode="major")
    assert [(r.target_pc, r.strength) for r in result.resolutions[:2]] == [
        (7, 2.0595), (5, 1.623),
    ]


# --- inputs & validation -----------------------------------------------------------

def test_degree_and_pc_inputs_agree():
    by_pc = melodic_tendency(11, tonic_pc=0, mode="major")
    by_degree = melodic_tendency(degree=7, tonic_pc=0, mode="major")
    assert by_pc == by_degree


def test_exactly_one_of_pc_or_degree():
    with pytest.raises(ValueError, match="exactly one"):
        melodic_tendency(11, degree=7, tonic_pc=0, mode="major")
    with pytest.raises(ValueError, match="exactly one"):
        melodic_tendency(tonic_pc=0, mode="major")


def test_unsupported_mode_and_policy_raise_actionably():
    with pytest.raises(ValueError, match="Unsupported mode"):
        melodic_tendency(0, tonic_pc=0, mode="dorian")
    with pytest.raises(ValueError, match="target policy"):
        melodic_tendency(0, tonic_pc=0, mode="major", targets="leaps")


def test_degree_range_and_prior_version():
    with pytest.raises(ValueError, match="degree out of range"):
        melodic_tendency(degree=8, tonic_pc=0, mode="major")
    with pytest.raises(ValueError, match="Unknown melodic-tendency version"):
        melodic_tendency(0, tonic_pc=0, mode="major", prior_version="nope.9")
    result = melodic_tendency(0, tonic_pc=0, mode="major")
    assert result.prior_version == "melodic-tendency.1"


def test_evidence_is_present_and_named():
    result = melodic_tendency(11, tonic_pc=0, mode="major", chord_pcs=[0, 4, 7])
    top = result.resolutions[0]
    joined = " | ".join(top.evidence)
    assert "semitone" in joined and "tonic" in joined and "anchor boost" in joined


# --- MCP parity ---------------------------------------------------------------------

def test_mcp_tool_matches_engine():
    from mts.mcp import tools

    engine = melodic_tendency(
        2, tonic_pc=0, mode="major", chord_pcs=[0, 4, 7]
    ).to_dict()
    tool = tools.melodic_tendency(pc="D", tonic="C", mode="major", chord_pcs=[0, 4, 7])
    assert tool == engine
    assert tools.melodic_tendency in tools.TOOLS
