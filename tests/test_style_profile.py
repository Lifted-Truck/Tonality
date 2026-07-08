"""Style-profile bundle (Phase 4.5, gap 14 slice 2).

The container that carries a style's two halves — a ruleset (constraints) and
distributions (the spread) — plus provenance, as one versioned, round-trippable
artifact. Tests cover assembly from both halves, the round-trip, the at-least-one-
half + provenance guards, the empty-ruleset coercion, raw-payload assembly, and
MCP parity.
"""

import pytest

from mts.rules import (
    StyleProfile,
    build_style_profile,
    build_transition_matrix,
    induce_ruleset,
    parse_ruleset,
    ruleset_to_payload,
)

CMAJ = (0, "major")
CORPUS = [
    ([(0, "maj"), (5, "maj"), (7, "maj"), (0, "maj")], CMAJ),
    ([(0, "maj"), (2, "min"), (7, "maj"), (0, "maj")], CMAJ),
    ([(0, "maj"), (9, "min"), (7, "maj"), (0, "maj")], CMAJ),
]
RULESET = parse_ruleset({
    "name": "cmaj", "version": "1",
    "rules": [{"id": "v-i", "family": "harmony", "where": {"role": "dominant"},
               "require": {"next_role": "tonic"}, "polarity": "soft", "weight": 2.0}],
})


def _degree():
    return build_transition_matrix(CORPUS, state="degree", source="toy")


# --- assembly + round-trip ----------------------------------------------------

def test_bundles_both_halves():
    sp = build_style_profile(
        "toy", "1", provenance={"source": "synthetic", "method": "induced+aggregated"},
        ruleset=RULESET, distributions=[_degree(), build_transition_matrix(CORPUS, state="role")],
    )
    d = sp.to_dict()
    assert d["schema_version"] == "style-profile.1"
    assert d["ruleset"] is not None and len(d["distributions"]) == 2
    assert d["provenance"]["source"] == "synthetic"


def test_round_trips():
    sp = build_style_profile("toy", "1", ruleset=RULESET, distributions=[_degree()],
                             provenance={"source": "x"}, description="d")
    assert StyleProfile.from_dict(sp.to_dict()).to_dict() == sp.to_dict()


def test_ruleset_only_and_distribution_only():
    r = build_style_profile("r", "1", ruleset=RULESET, provenance={"source": "x"})
    assert r.ruleset is not None and r.distributions == ()
    d = build_style_profile("d", "1", distributions=[_degree()], provenance={"source": "x"})
    assert d.ruleset is None and len(d.distributions) == 1


def test_accepts_raw_payloads():
    # a ruleset DSL payload + a transition-matrix payload assemble the same as objects.
    from_objs = build_style_profile("a", "1", ruleset=RULESET, distributions=[_degree()],
                                    provenance={"source": "x"}).to_dict()
    from_raw = build_style_profile("a", "1", ruleset=ruleset_to_payload(RULESET),
                                   distributions=[_degree().to_dict()],
                                   provenance={"source": "x"}).to_dict()
    assert from_objs == from_raw


# --- the honest-bundle guards -------------------------------------------------

def test_empty_ruleset_is_treated_as_absent():
    # induction on a tiny corpus finds nothing significant → an empty ruleset,
    # which is not a constraint half and not a valid DSL payload: coerced to None.
    empty = induce_ruleset(family="harmony", chord_corpus=CORPUS).ruleset
    assert len(empty.rules) == 0
    sp = build_style_profile("d", "1", ruleset=empty, distributions=[_degree()],
                             provenance={"source": "x"})
    assert sp.ruleset is None
    assert StyleProfile.from_dict(sp.to_dict()).to_dict() == sp.to_dict()


def test_empty_profile_raises():
    with pytest.raises(ValueError, match="at least one half"):
        build_style_profile("empty", "1", provenance={"source": "x"})
    # an empty ruleset with no distributions is also empty
    empty = induce_ruleset(family="harmony", chord_corpus=CORPUS).ruleset
    with pytest.raises(ValueError, match="at least one half"):
        build_style_profile("empty", "1", ruleset=empty, provenance={"source": "x"})


def test_non_dict_provenance_raises():
    with pytest.raises(ValueError, match="provenance must be a dict"):
        build_style_profile("bad", "1", ruleset=RULESET, provenance=["not", "a", "dict"])


def test_default_provenance_is_empty_dict():
    sp = build_style_profile("p", "1", ruleset=RULESET)
    assert sp.provenance == {}


# --- MCP parity ---------------------------------------------------------------

def test_mcp_build_style_profile_matches_engine():
    from mts.mcp import tools

    engine = build_style_profile(
        "s", "1", ruleset=RULESET, distributions=[_degree()],
        provenance={"source": "x", "method": "m"},
    ).to_dict()
    tool = tools.build_style_profile(
        "s", "1", provenance={"source": "x", "method": "m"},
        ruleset=ruleset_to_payload(RULESET), distributions=[_degree().to_dict()],
    )
    assert tool == engine
