"""Degree-transition distributions (Phase 4.5, gap 14): the *sampleable* half of
a style profile.

A ruleset says what a style **forbids** (constraints); a transition distribution
says what it **does** (the spread). This builds the second from a chord-stream
corpus — a first-order, degree-keyed, row-normalized transition matrix over the
harmony atom vocabulary — the same corpus interface harmony induction reads. The
two are representations of one style; the style-profile *bundle* that carries both
is the recorded slice-2 follow-on (ROADMAP gap 14).

**Sampleable, deterministically.** The matrix exposes row-normalized
probabilities and a **seeded** ``sample`` / ``walk`` — generation is a client act
(the Wend-wont division), but a seeded, reproducible walk is a legitimate engine
convenience: no wall-clock, no unseeded RNG (the AI/deterministic boundary).

**Smoothing is a cited, selectable knob** (Julian's call, 2026-07-08):
``"laplace"`` (default, add-α — no hard zeros, right for sampling a rare-but-
possible transition) or ``"none"`` (raw empirical — honest to the corpus, exact
zeros). **Raw integer counts are preserved either way**, so a caller can
re-normalize; α is a versioned prior (``distribution.1``) cited on the result.

State keying is a parameter over the atom vocabulary: ``"degree"`` (default —
scale degrees 1..7, non-diatonic roots bucketed as ``"chromatic"``), ``"role"``
(tonic/predominant/dominant/none), ``"quality"``, or ``"roman"``.
"""

from __future__ import annotations

import dataclasses
import random
from dataclasses import dataclass

from .harmony_stream import build_harmony_stream

# The versioned smoothing prior: an engineering default (pending corpus
# calibration), cited on every result. add-0.5 (Krichevsky–Trofimov) is a gentler
# floor than add-1 on small corpora, while still killing hard zeros.
_PRIOR_VERSION = "distribution.1"
_DEFAULT_ALPHA = 0.5

_STATE_FIELDS = ("degree", "role", "quality", "roman")


def _state_of(item, which: str) -> str:
    """The (string) state label for one harmony atom under the chosen keying."""

    if which == "degree":
        return str(item.degree) if item.degree is not None else "chromatic"
    if which == "role":
        return item.role if item.role is not None else "none"
    if which == "roman":
        return item.roman if item.roman is not None else "none"
    return item.quality  # "quality" — always present


@dataclass(frozen=True)
class TransitionMatrix:
    """A first-order transition distribution over one atom-state keying.

    ``counts`` are the raw observed transitions (always exact); ``probabilities``
    are ``counts`` row-normalized under ``smoothing``. ``states`` is the sorted
    observed vocabulary (rows and columns share it). Provenance follows the
    versioned-prior discipline: ``source`` (caller-supplied), ``prior_version``,
    ``alpha``, ``n_transitions``, ``n_pieces``.
    """

    state: str                              # which atom field keys the matrix
    states: tuple[str, ...]                 # sorted observed state vocabulary
    counts: dict[str, dict[str, int]]       # raw transition counts [from][to]
    probabilities: dict[str, dict[str, float]]  # row-normalized under smoothing
    smoothing: str                          # "laplace" | "none"
    alpha: float                            # additive constant (0.0 when "none")
    prior_version: str
    n_transitions: int
    n_pieces: int
    source: str | None                      # caller provenance (e.g. corpus name)

    def row(self, from_state: str) -> dict[str, float]:
        """The outgoing probability distribution from ``from_state``."""
        if from_state not in self.probabilities:
            raise ValueError(
                f"unknown from-state {from_state!r} (states: {list(self.states)})"
            )
        return self.probabilities[from_state]

    def sample(self, from_state: str, *, seed: int) -> str:
        """One deterministic draw of the next state given ``from_state``.

        Seeded (reproducible) — the generative act stays client-side, but the
        draw is exact given ``seed``. Raises if ``from_state`` has no outgoing
        distribution (only possible under ``smoothing="none"`` for a state never
        seen as a source).
        """
        row = self.row(from_state)
        total = sum(row.values())
        if total <= 0.0:
            raise ValueError(
                f"no outgoing distribution from {from_state!r} "
                "(never a source under smoothing='none')"
            )
        r = random.Random(seed).random() * total
        cumulative = 0.0
        for state in self.states:            # canonical order → deterministic
            cumulative += row.get(state, 0.0)
            if r < cumulative:
                return state
        return self.states[-1]               # float-guard: last state

    def walk(self, start_state: str, length: int, *, seed: int) -> list[str]:
        """A deterministic ``length``-state walk from ``start_state``.

        One seeded RNG threads the whole walk, so the sequence is reproducible.
        """
        if length < 1:
            raise ValueError(f"length must be >= 1, got {length}.")
        rng = random.Random(seed)
        current = start_state
        out = [current]
        for _ in range(length - 1):
            row = self.row(current)
            total = sum(row.values())
            if total <= 0.0:
                raise ValueError(
                    f"walk stalled at {current!r}: no outgoing distribution "
                    "(smoothing='none' dead end)"
                )
            r = rng.random() * total
            cumulative = 0.0
            nxt = self.states[-1]
            for state in self.states:
                cumulative += row.get(state, 0.0)
                if r < cumulative:
                    nxt = state
                    break
            out.append(nxt)
            current = nxt
        return out

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "states": list(self.states),
            "counts": {f: dict(t) for f, t in self.counts.items()},
            "probabilities": {f: dict(t) for f, t in self.probabilities.items()},
            "smoothing": self.smoothing,
            "alpha": self.alpha,
            "prior_version": self.prior_version,
            "n_transitions": self.n_transitions,
            "n_pieces": self.n_pieces,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TransitionMatrix":
        return cls(
            state=data["state"],
            states=tuple(data["states"]),
            counts={f: dict(t) for f, t in data["counts"].items()},
            probabilities={f: dict(t) for f, t in data["probabilities"].items()},
            smoothing=data["smoothing"],
            alpha=data["alpha"],
            prior_version=data["prior_version"],
            n_transitions=data["n_transitions"],
            n_pieces=data["n_pieces"],
            source=data.get("source"),
        )


def _normalize(
    counts: dict[str, dict[str, int]], states: tuple[str, ...], smoothing: str, alpha: float
) -> dict[str, dict[str, float]]:
    """Row-normalize the raw counts under the chosen smoothing."""

    n_states = len(states)
    probs: dict[str, dict[str, float]] = {}
    for src in states:
        row = counts.get(src, {})
        row_total = sum(row.values())
        denom = row_total + (alpha * n_states if smoothing == "laplace" else 0.0)
        if denom <= 0.0:
            # A state never seen as a source, smoothing='none': no distribution.
            probs[src] = {}
            continue
        probs[src] = {
            dst: (row.get(dst, 0) + (alpha if smoothing == "laplace" else 0.0)) / denom
            for dst in states
        }
    return probs


def build_transition_matrix(
    chord_corpus: list[tuple[list[tuple[int, str]], tuple[int, str]]],
    *,
    state: str = "degree",
    smoothing: str = "laplace",
    alpha: float | None = None,
    source: str | None = None,
    session=None,
) -> TransitionMatrix:
    """Aggregate a chord-stream corpus into a first-order transition distribution.

    ``chord_corpus`` is ``[(chords, key), …]`` — the same input harmony induction
    reads: ``chords = [(root_pc, quality), …]`` and ``key = (tonic_pc, mode)``.
    Each progression contributes its consecutive within-piece state transitions.

    ``state`` keys the matrix over the atom vocabulary (``"degree"`` default;
    ``"role"`` / ``"quality"`` / ``"roman"``). ``smoothing`` is ``"laplace"``
    (default, add-``alpha``, no hard zeros) or ``"none"`` (raw empirical); ``alpha``
    defaults to the versioned ``distribution.1`` prior. ``source`` records
    provenance. An unknown chord quality raises (via ``build_harmony_stream`` —
    error, not guess); a modal-key piece yields no atoms and contributes nothing.
    """

    if state not in _STATE_FIELDS:
        raise ValueError(f"state must be one of {_STATE_FIELDS}, got {state!r}.")
    if smoothing not in ("laplace", "none"):
        raise ValueError(f"smoothing must be 'laplace' or 'none', got {smoothing!r}.")
    a = _DEFAULT_ALPHA if alpha is None else float(alpha)
    if a < 0.0:
        raise ValueError(f"alpha must be >= 0, got {a}.")

    counts: dict[str, dict[str, int]] = {}
    observed: set[str] = set()
    n_transitions = 0
    n_pieces = 0
    for chords, key in chord_corpus:
        items, _reason = build_harmony_stream(list(chords), key[0], key[1], session=session)
        if not items:
            continue
        n_pieces += 1
        labels = [_state_of(item, state) for item, _loc in items]
        observed.update(labels)
        for cur, nxt in zip(labels, labels[1:]):
            counts.setdefault(cur, {})
            counts[cur][nxt] = counts[cur].get(nxt, 0) + 1
            n_transitions += 1

    states = tuple(sorted(observed))
    probabilities = _normalize(counts, states, smoothing, a)
    return TransitionMatrix(
        state=state,
        states=states,
        counts={f: dict(t) for f, t in counts.items()},
        probabilities=probabilities,
        smoothing=smoothing,
        alpha=(a if smoothing == "laplace" else 0.0),
        prior_version=_PRIOR_VERSION,
        n_transitions=n_transitions,
        n_pieces=n_pieces,
        source=source,
    )


__all__ = ["TransitionMatrix", "build_transition_matrix"]
