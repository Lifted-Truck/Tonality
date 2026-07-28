"""Drum-pattern analysis: per-role onset grids and named-pattern matching.

Reads a percussion part and answers two questions exactly: **what is playing**
(GM note → drum role) and **which named rhythmic patterns does it realize**
(four-on-the-floor, backbeat, tresillo…). Both are measurements, not judgments:

- **Roles come from a versioned prior** (``gm-percussion.1``,
  ``data/gm_percussion.json`` — the published General MIDI Level-1 percussion
  key map). A pitch outside the map has **no** drum meaning here and is reported
  in ``unmapped_pitches`` rather than guessed at.
- **A named pattern is an exact per-bar predicate**: "this role has an onset at
  each of these beat positions in this bar". Matching is **required-only** — a
  four-on-the-floor bar with extra kicks still is one — and the result is a
  **coverage rate** (``bars_matched / bars_total``) with the matching bars
  itemized, never a bare boolean. Several patterns can match at once and all are
  reported (e.g. eighth-note hats necessarily also satisfy offbeat hats); the
  caller reads the set.

**Facts, never a verdict** (the gap-E doctrine, applied to rhythm): this module
emits roles, grids and coverages. It never concludes "this is house" — genre is
not a function of a drum pattern (four-on-the-floor spans disco, house, techno
and half of pop), so a genre *label* would be fabricated confidence. Genre
*affinities* as a cited, plural, versioned prior are a recorded follow-on;
genre *classification* belongs to the learned sibling (ROADMAP Decision 15).

Which events are drums? MIDI channel 10 (0-indexed 9) is the GM percussion
channel, and ingestion labels voices ``t{n}c{n}`` — so by default this selects
voices ending ``c9``. When no such voice exists the caller's selection is used
as-is and ``channel_10_detected`` is ``False``, so a mapping applied to
non-percussion material is visible rather than silent.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from ..io.loaders import load_gm_percussion
from .sequence import Sequence

_EPS = 1e-6


@dataclass(frozen=True)
class RoleOnsets:
    """Every onset of one drum role, with its metric placement."""

    role: str
    count: int
    onsets: list[float]          # absolute beats
    beats_in_bar: list[float]    # position within the bar of each onset
    pitches: list[int]           # the distinct GM notes that produced this role

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class DrumPatternMatch:
    """How well one named pattern is realized — a coverage rate, with evidence."""

    name: str
    version: str
    role: str
    required_beats: list[float]
    bars_matched: int
    bars_considered: int
    coverage: float              # bars_matched / bars_considered
    matched_bars: list[int]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class DrumPatternAnalysis:
    """What the kit plays, and which named patterns it realizes."""

    channel_10_detected: bool
    voices_analyzed: list
    bars_considered: int
    roles: list[RoleOnsets]
    unmapped_pitches: list[int]  # pitches with no GM percussion meaning
    matches: list[DrumPatternMatch]
    map_version: str

    def to_dict(self) -> dict:
        return {
            "channel_10_detected": self.channel_10_detected,
            "voices_analyzed": list(self.voices_analyzed),
            "bars_considered": self.bars_considered,
            "roles": [r.to_dict() for r in self.roles],
            "unmapped_pitches": list(self.unmapped_pitches),
            "matches": [m.to_dict() for m in self.matches],
            "map_version": self.map_version,
        }


def _percussion_voices(sequence: Sequence) -> tuple[list, bool]:
    """Voices on MIDI channel 10 (label ``…c9``); else every voice, flagged."""

    voices = list(sequence.voices()) or [None]
    channel_10 = [v for v in voices if isinstance(v, str) and v.endswith("c9")]
    if channel_10:
        return channel_10, True
    return voices, False


def drum_pattern_analysis(
    sequence: Sequence,
    *,
    voice=None,
    patterns=None,
) -> DrumPatternAnalysis:
    """Per-role onset grid + named-pattern coverage for a percussion part.

    ``voice`` restricts to one part; by default the MIDI-channel-10 voices are
    used (or every voice, with ``channel_10_detected=False``, when none exist).
    ``patterns`` overrides the shipped named library (a list of payload dicts).
    Raises on an empty sequence — no material, no analysis.
    """

    if not sequence.events:
        raise ValueError("drum_pattern_analysis needs a non-empty sequence.")

    if voice is not None:
        selected, detected = [voice], (isinstance(voice, str) and voice.endswith("c9"))
    else:
        selected, detected = _percussion_voices(sequence)

    gm = load_gm_percussion()
    events = [e for e in sequence.events if e.voice in selected]

    by_role: dict[str, list] = {}
    role_pitches: dict[str, set] = {}
    unmapped: set[int] = set()
    for event in events:
        role = gm.role_of(event.pitch.midi)
        if role is None:
            unmapped.add(event.pitch.midi)
            continue
        by_role.setdefault(role, []).append(event)
        role_pitches.setdefault(role, set()).add(event.pitch.midi)

    # metric placement for every kept onset
    # role -> (bar, beat_in_bar, onset, (numerator, denominator))
    placement: dict[str, list[tuple[int, float, float, tuple]]] = {}
    bar_meter: dict[int, tuple] = {}
    for role, evs in by_role.items():
        rows = []
        for e in sorted(evs, key=lambda e: e.onset):
            pos = sequence.metric_position(e.onset)
            sig = (pos.signature.numerator, pos.signature.denominator)
            bar_meter[pos.bar] = sig
            rows.append((pos.bar, round(pos.beat_in_bar, 9), e.onset, sig))
        placement[role] = rows

    bars = sorted(bar_meter)
    bars_considered = len(bars)

    roles = [
        RoleOnsets(
            role=role,
            count=len(rows),
            onsets=[o for _b, _bb, o, _s in rows],
            beats_in_bar=[bb for _b, bb, _o, _s in rows],
            pitches=sorted(role_pitches[role]),
        )
        for role, rows in sorted(placement.items())
    ]

    library = patterns if patterns is not None else _load_named_drum_patterns()
    matches = [
        m for m in (_match(p, placement, bars, bar_meter) for p in library) if m is not None
    ]
    matches.sort(key=lambda m: (-m.coverage, m.name))

    return DrumPatternAnalysis(
        channel_10_detected=detected,
        voices_analyzed=list(selected),
        bars_considered=bars_considered,
        roles=roles,
        unmapped_pitches=sorted(unmapped),
        matches=matches,
        map_version=gm.version,
    )


def _match(payload: dict, placement: dict, bars: list[int], bar_meter: dict):
    """Coverage of one named pattern, or ``None`` when it cannot apply here."""

    role = payload["role"]
    rows = placement.get(role)
    if not rows or not bars:
        return None  # the role never sounds — no claim, not a zero
    required = [float(b) for b in payload["required_beats"]]

    # A pattern declares the meter it is defined in; bars in any other meter are
    # NOT considered (a 4/4 backbeat makes no claim about a 3/4 bar) — so
    # coverage is always "of the bars this pattern could apply to".
    want = tuple(int(x) for x in payload.get("meter", ()))
    considered, matched = [], []
    for bar in bars:
        if want and bar_meter.get(bar) != want:
            continue
        considered.append(bar)
        struck = {bb for b, bb, _o, _s in rows if b == bar}
        if all(any(abs(bb - r) <= _EPS for bb in struck) for r in required):
            matched.append(bar)
    if not considered:
        return None  # no bar in the pattern's meter — no claim

    return DrumPatternMatch(
        name=payload["name"],
        version=payload.get("version", "1"),
        role=role,
        required_beats=required,
        bars_matched=len(matched),
        bars_considered=len(considered),
        coverage=round(len(matched) / len(considered), 9),
        matched_bars=matched,
    )


def _load_named_drum_patterns() -> list[dict]:
    from ..io.loaders import load_named_drum_patterns

    return load_named_drum_patterns()


__all__ = [
    "RoleOnsets", "DrumPatternMatch", "DrumPatternAnalysis", "drum_pattern_analysis",
]
