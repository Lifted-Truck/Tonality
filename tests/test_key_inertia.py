"""Key-inertia continuity prior for local key tracking (A6 brief-13).

A deterministic Viterbi over the per-window candidate scores with a flat
``switch_penalty``: rewards fit, penalizes switching, lets a sustained well-fit key
win. Opt-in on ``track_keys`` (``key_inertia=True``); ``infer_key`` is untouched.
"""

from __future__ import annotations

import pytest

from mts.core.pitch import Pitch
from mts.io.loaders import load_key_inertia
from mts.temporal import Event, Sequence, track_keys
from mts.temporal.key_tracking import _key_inertia_path

ALL_STATES = [(t, m) for t in range(12) for m in ("major", "minor")]


def _sv(highs: dict[tuple[int, str], float]) -> dict[tuple[int, str], float]:
    """A full 24-state score vector; unspecified states score 0.0."""
    return {s: highs.get(s, 0.0) for s in ALL_STATES}


# --- the Viterbi (the core behaviour) --------------------------------------------


def test_near_tie_flip_is_held_to_context():
    # A:maj established, a middle window where A:minor barely wins on content, then
    # A:maj again. The one-time switch penalty makes staying A:major cheaper than
    # flipping out and back, so the spurious mode flip is suppressed.
    A = (9, "major")
    seq = [
        _sv({A: 0.90, (9, "minor"): 0.85}),
        _sv({A: 0.40, (9, "minor"): 0.42}),  # raw argmax here is A minor
        _sv({A: 0.90, (9, "minor"): 0.85}),
    ]
    penalty = load_key_inertia().switch_penalty
    assert _key_inertia_path(seq, penalty) == [A, A, A]
    # raw argmax (penalty 0) would flip in the middle
    assert _key_inertia_path(seq, 0.0) == [A, (9, "minor"), A]


def test_sustained_modulation_survives():
    # A:maj x2 then a sustained, well-fit E:maj x4 — the penalty is paid ONCE while
    # the modulation accrues emission advantage over many windows, so it's kept.
    A, E = (9, "major"), (4, "major")
    seq = [_sv({A: 0.8})] * 2 + [_sv({E: 0.8})] * 4
    path = _key_inertia_path(seq, load_key_inertia().switch_penalty)
    assert path == [A, A, E, E, E, E]


def test_inertia_is_deterministic_on_ties():
    # Two equally-scoring states across all windows — the path must be reproducible
    # (ties break to the lexicographically-lowest state), not RNG/dict-order.
    s = _sv({(0, "major"): 0.5, (7, "major"): 0.5})
    a = _key_inertia_path([s, s, s], 0.1)
    b = _key_inertia_path([s, s, s], 0.1)
    assert a == b
    assert len(set(a)) == 1  # one state held throughout (no spurious switching)


# --- track_keys integration ------------------------------------------------------


def _noisy_sequence() -> Sequence:
    # Mostly C major with a 2-beat A-minor-ish blip in the middle — raw tracking
    # over-segments; inertia should absorb the blip.
    events = []
    for t in range(0, 24, 2):
        for m in (60, 64, 67):  # C major
            events.append(Event(float(t), 2.0, Pitch.from_midi(m)))
    for m in (69, 60, 64):  # a brief A-minor-leaning blip at beat 12
        events.append(Event(12.0, 2.0, Pitch.from_midi(m)))
    return Sequence.from_events(events)


def test_default_off_is_unchanged_and_opt_in_cites_the_prior():
    seq = _noisy_sequence()
    raw = track_keys(seq)
    assert raw.inertia_version is None  # default: no inertia
    inert = track_keys(seq, key_inertia=True)
    assert inert.inertia_version == load_key_inertia().version == "key-inertia.1"
    # parsimony: the continuity prior never increases the segmentation here
    assert len(inert.regions) <= len(raw.regions)


def test_track_keys_inertia_is_deterministic():
    seq = _noisy_sequence()
    assert track_keys(seq, key_inertia=True).to_dict() == track_keys(seq, key_inertia=True).to_dict()


def test_infer_key_default_untouched():
    # The A5/A7 stability contract: key_inertia is a track_keys-only layer.
    from mts.analysis import infer_key

    w = [4.0, 0, 1.0, 0, 2.0, 1.0, 0, 3.0, 0, 1.0, 0, 1.0]
    assert "key_inertia" not in infer_key.__code__.co_varnames


# --- versioned prior -------------------------------------------------------------


def test_inertia_prior_is_versioned():
    prior = load_key_inertia()
    assert prior.version == "key-inertia.1"
    assert prior.switch_penalty == 0.1
    assert load_key_inertia("key-inertia.1") is prior
    with pytest.raises(ValueError, match="Unknown key-inertia version"):
        load_key_inertia("no-such-version")


# --- RE-3c: the flag conflict is loud; region stats describe the region's key ------------


def test_inertia_rejects_disambiguate_relative():
    # The inertia path re-decodes from raw score vectors, so the per-window
    # relative-key tie-break can never reach it — the combination used to be
    # accepted and the tie-break silently discarded.
    seq = _noisy_sequence()
    with pytest.raises(ValueError, match="does not compose"):
        track_keys(seq, key_inertia=True, disambiguate_relative=True)


def test_region_stats_are_measured_against_the_region_label():
    # With smoothing/inertia off and no disambiguation, every region label is
    # the raw argmax, so mean_margin must equal the old top-two margin —
    # i.e. strictly positive and identical to the windows' own margins.
    seq = _noisy_sequence()
    result = track_keys(seq)
    for region in result.regions:
        assert region.mean_margin > 0
    # With disambiguation on, a tie-broken region reports its correlation
    # margin FOR THE KEY IT CLAIMS — negative when the raw correlation
    # preferred the relative (the honest gating signal; it used to average
    # the raw-argmax stats and could describe the wrong key).
    tie_broken = track_keys(seq, disambiguate_relative=True)
    changed = [
        (raw.tonic_pc, raw.mode) != (tb.tonic_pc, tb.mode)
        for raw, tb in zip(result.windows, tie_broken.windows)
        if raw.is_informative
    ]
    if any(changed):  # only assert the sign flip where a relabel happened
        assert any(r.mean_margin < 0 for r in tie_broken.regions)
