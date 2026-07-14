"""Cross-part patterns (gap E slice 4 / gap C cross-voice follow-on): a schema
spanning **two or more voices moving together**, the generalization of the
single-voice melody :class:`~mts.patterns.schema.Pattern` to vertical schemata.

The marquee case is the galant **Prinner**: an upper voice descending 6-5-4-3
over a 4-3-2-1 bass, homorhythmically — a two-voice degree schema the melody
domain could only half-express (see ``data/patterns/prinner-descent.json``).

A :class:`CrossPartPattern` declares, on the same principled axes as the melody
Pattern:

- a **pitch level** — ``exact`` / ``degree`` / ``contour`` — shared by all lines;
- an **alignment** — ``homorhythmic`` (the voices share every onset over the
  matched window; the cross-part analog of the melody "free" time level — any
  spacing, but the voices move *together*). Offset/imitative alignment (call-and-
  response) is the recorded slice-4b follow-on;
- **lines** — an ordered list of element-sequences, **register order high→low**,
  all the same length. The matcher pairs any co-onset single-pitch voices by
  *register* (line 0 = the highest-sounding), not by label — a schema is
  register-relative, so it matches whatever two (or k) parts realize it.

Matching is **exact under the declared abstraction** (no tolerance knobs), degree
matching **needs a key and never infers one** (error, don't guess), non-
linearizable (chordal) voices are skipped and named, and every overlapping
occurrence is reported — the same honesty contract as the melody matcher.
"""

from __future__ import annotations

import bisect
import dataclasses
from dataclasses import dataclass
from itertools import combinations

from ..temporal import Sequence
from .matcher import _EPS, _MODE_SCALE, _UNSET, _degree_of, _lines

SCHEMA_VERSION = "cross_part.1"
DOMAIN = "schema"
PITCH_LEVELS = ("exact", "degree", "contour")
ALIGNMENTS = ("homorhythmic",)
CONTOUR_MOVES = ("up", "down", "same")


class CrossPartValidationError(ValueError):
    """Raised with the FULL list of validation errors (never just the first)."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid cross-part pattern:\n" + "\n".join(f"- {e}" for e in errors))


@dataclass(frozen=True)
class CrossPartPattern:
    """A validated multi-voice schema. ``lines`` are register-ordered high→low."""

    name: str
    version: str
    domain: str            # "schema"
    pitch_level: str       # "exact" | "degree" | "contour"
    alignment: str         # "homorhythmic"
    lines: tuple           # tuple of element-tuples (one per voice, high→low)
    description: str = ""
    schema_version: str = SCHEMA_VERSION

    @property
    def n_lines(self) -> int:
        return len(self.lines)

    @property
    def n_onsets(self) -> int:
        """Onsets per occurrence: elements are notes, except contour = moves (n+1)."""
        first = self.lines[0]
        return len(first) + 1 if self.pitch_level == "contour" else len(first)


@dataclass(frozen=True)
class CrossPartLineBinding:
    """How one register line matched: its pitches and the per-level binding."""

    midis: list[int]
    degrees: list[int] | None
    moves: list[str] | None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class CrossPartOccurrence:
    """One located occurrence: which voices realized it, when, and how each line
    (register order high→low) matched."""

    voices: list            # the participating voice labels
    start_beat: float
    end_beat: float
    onsets: list[float]
    lines: list[CrossPartLineBinding]

    def to_dict(self) -> dict:
        return {
            "voices": list(self.voices),
            "start_beat": self.start_beat,
            "end_beat": self.end_beat,
            "onsets": list(self.onsets),
            "lines": [ln.to_dict() for ln in self.lines],
        }


@dataclass(frozen=True)
class CrossPartMatches:
    """Every occurrence of one cross-part pattern (plural, evidence-carrying)."""

    pattern_name: str
    pattern_version: str
    pitch_level: str
    alignment: str
    key: tuple[int, str] | None
    count: int
    occurrences: list[CrossPartOccurrence]
    voices_skipped: list

    def to_dict(self) -> dict:
        return {
            "pattern_name": self.pattern_name,
            "pattern_version": self.pattern_version,
            "pitch_level": self.pitch_level,
            "alignment": self.alignment,
            "key": list(self.key) if self.key is not None else None,
            "count": self.count,
            "occurrences": [o.to_dict() for o in self.occurrences],
            "voices_skipped": list(self.voices_skipped),
        }


def cross_part_validation_errors(payload: object) -> list[str]:
    """Every error in *payload* as a cross-part pattern — [] iff valid (total)."""

    if not isinstance(payload, dict):
        return ["cross-part pattern must be a JSON object"]
    errors: list[str] = []

    if not isinstance(payload.get("name"), str) or not payload.get("name"):
        errors.append("name: required, a non-empty string")
    if not isinstance(payload.get("version"), str) or not payload.get("version"):
        errors.append("version: required, a non-empty string")
    if payload.get("domain") != DOMAIN:
        errors.append(f"domain: must be {DOMAIN!r}, got {payload.get('domain')!r}")

    abstraction = payload.get("abstraction")
    pitch_level = alignment = None
    if not isinstance(abstraction, dict):
        errors.append('abstraction: required, an object {"pitch": …, "alignment": …}')
    else:
        pitch_level = abstraction.get("pitch")
        alignment = abstraction.get("alignment")
        if pitch_level not in PITCH_LEVELS:
            errors.append(f"abstraction.pitch: must be one of {list(PITCH_LEVELS)}, got {pitch_level!r}")
        if alignment not in ALIGNMENTS:
            errors.append(f"abstraction.alignment: must be one of {list(ALIGNMENTS)}, got {alignment!r}")
        unknown = sorted(set(abstraction) - {"pitch", "alignment"})
        if unknown:
            errors.append(f"abstraction: unknown keys {unknown}")

    lines = payload.get("lines")
    if not isinstance(lines, list) or len(lines) < 2:
        errors.append("lines: required, a list of >= 2 voice lines (register order high→low)")
    elif pitch_level in PITCH_LEVELS:
        onset_counts = set()
        for idx, line in enumerate(lines):
            if not isinstance(line, list) or not line:
                errors.append(f"lines[{idx}]: must be a non-empty list")
                continue
            if pitch_level == "exact":
                bad = [e for e in line if not isinstance(e, int) or not 0 <= e <= 127]
                if bad:
                    errors.append(f"lines[{idx}]: pitch-exact entries must be MIDI ints 0..127, got {bad}")
                if len(line) < 2:
                    errors.append(f"lines[{idx}]: an exact/degree line needs >= 2 notes")
                onset_counts.add(len(line))
            elif pitch_level == "degree":
                bad = [e for e in line if not isinstance(e, int) or not 1 <= e <= 7]
                if bad:
                    errors.append(f"lines[{idx}]: degree entries must be ints 1..7, got {bad}")
                if len(line) < 2:
                    errors.append(f"lines[{idx}]: an exact/degree line needs >= 2 notes")
                onset_counts.add(len(line))
            else:  # contour
                bad = [e for e in line if e not in CONTOUR_MOVES]
                if bad:
                    errors.append(f"lines[{idx}]: contour entries must be in {list(CONTOUR_MOVES)}, got {bad}")
                onset_counts.add(len(line) + 1)
        if len(onset_counts) > 1:
            errors.append(f"lines: every line must span the same number of onsets, got {sorted(onset_counts)}")

    if not isinstance(payload.get("description", ""), str):
        errors.append("description: must be a string when present")

    known = {"schema_version", "name", "version", "domain", "abstraction", "lines", "description"}
    unknown = sorted(set(payload) - known)
    if unknown:
        errors.append(f"unknown keys {unknown}")
    return errors


def parse_cross_part_pattern(payload: object) -> CrossPartPattern:
    """Validate totally; return the frozen pattern or raise with the full list."""

    errors = cross_part_validation_errors(payload)
    if errors:
        raise CrossPartValidationError(errors)
    assert isinstance(payload, dict)
    abstraction = payload["abstraction"]
    return CrossPartPattern(
        name=payload["name"],
        version=payload["version"],
        domain=payload["domain"],
        pitch_level=abstraction["pitch"],
        alignment=abstraction["alignment"],
        lines=tuple(tuple(line) for line in payload["lines"]),
        description=payload.get("description", ""),
    )


def cross_part_pattern_to_payload(pattern: CrossPartPattern) -> dict:
    """The JSON payload form (round-trips through :func:`parse_cross_part_pattern`)."""

    payload: dict = {
        "schema_version": pattern.schema_version,
        "name": pattern.name,
        "version": pattern.version,
        "domain": pattern.domain,
        "abstraction": {"pitch": pattern.pitch_level, "alignment": pattern.alignment},
        "lines": [list(line) for line in pattern.lines],
    }
    if pattern.description:
        payload["description"] = pattern.description
    return payload


def _pitch_at(onsets: list[float], midis: list[int], t: float) -> int | None:
    """The pitch of the note onsetting at ~``t`` (within eps), via binary search."""

    i = bisect.bisect_left(onsets, t - _EPS)
    if i < len(onsets) and abs(onsets[i] - t) <= _EPS:
        return midis[i]
    return None


def _count_in_span(onsets: list[float], lo: float, hi: float) -> int:
    """How many onsets fall in [lo, hi] (eps-inclusive) — strict-homorhythm guard."""

    return bisect.bisect_right(onsets, hi + _EPS) - bisect.bisect_left(onsets, lo - _EPS)


def find_cross_part_pattern(
    sequence: Sequence,
    pattern: CrossPartPattern | dict,
    *,
    key: tuple[int, str] | None = None,
) -> CrossPartMatches:
    """Every occurrence of *pattern* across the voices of *sequence*.

    A match is a window of ``n_onsets`` successive **shared** onsets over which
    ``n_lines`` voices move together (strict homorhythm — no voice onsets alone in
    the window), whose register-sorted pitches (high→low) match each declared line
    under the pattern's pitch level. ``key=(tonic_pc, mode)`` is **required** for a
    degree pattern (never inferred). Chordal (non-linearizable) voices are skipped
    and named; overlapping occurrences are all reported.
    """

    if not isinstance(pattern, CrossPartPattern):
        pattern = parse_cross_part_pattern(pattern)

    tonic = scale = None
    if pattern.pitch_level == "degree":
        if key is None:
            raise ValueError(
                "a degree-level cross-part pattern needs key=(tonic_pc, mode) — the "
                "matcher never infers a key (run infer_key and pass its answer)."
            )
        tonic = int(key[0]) % 12
        scale = _MODE_SCALE.get(str(key[1]).lower())
        if scale is None:
            raise ValueError(f"degree matching supports major/minor only, got mode {key[1]!r}.")

    lines_by_voice, skipped = _lines(sequence, _UNSET)
    voices = sorted(lines_by_voice, key=lambda v: (v is None, v))
    onset_arr = {v: [e.onset for e in lines_by_voice[v]] for v in voices}
    midi_arr = {v: [e.pitch.midi for e in lines_by_voice[v]] for v in voices}

    K, N = pattern.n_lines, pattern.n_onsets
    occurrences: list[CrossPartOccurrence] = []

    for combo in combinations(voices, K):
        # shared onset grid for this k-tuple: base voice's onsets at which every
        # other voice also onsets (within eps).
        base = combo[0]
        shared: list[tuple[float, list[int]]] = []
        for t, m0 in zip(onset_arr[base], midi_arr[base]):
            pitches = [m0]
            for v in combo[1:]:
                p = _pitch_at(onset_arr[v], midi_arr[v], t)
                if p is None:
                    break
                pitches.append(p)
            if len(pitches) == K:
                shared.append((t, pitches))

        for i in range(len(shared) - N + 1):
            window = shared[i:i + N]
            lo, hi = window[0][0], window[-1][0]
            # strict homorhythm: no combo voice has an extra onset inside the window
            if any(_count_in_span(onset_arr[v], lo, hi) != N for v in combo):
                continue
            # register-sorted pitches high→low at each onset → the K lines
            reg = [sorted(pitches, reverse=True) for _, pitches in window]
            bindings = _match(pattern, reg, tonic, scale)
            if bindings is None:
                continue
            occurrences.append(CrossPartOccurrence(
                voices=list(combo),
                start_beat=lo,
                end_beat=hi,
                onsets=[t for t, _ in window],
                lines=bindings,
            ))

    return CrossPartMatches(
        pattern_name=pattern.name,
        pattern_version=pattern.version,
        pitch_level=pattern.pitch_level,
        alignment=pattern.alignment,
        key=(tonic, str(key[1]).lower()) if scale is not None else None,
        count=len(occurrences),
        occurrences=occurrences,
        voices_skipped=skipped,
    )


def _match(pattern, reg, tonic, scale) -> list[CrossPartLineBinding] | None:
    """Match the register-sorted pitch grid ``reg`` (per-onset, high→low) against
    every declared line; return per-line bindings or ``None`` on any mismatch."""

    bindings: list[CrossPartLineBinding] = []
    for li, elements in enumerate(pattern.lines):
        pitches = [reg[j][li] for j in range(len(reg))]
        degrees = moves = None
        if pattern.pitch_level == "exact":
            if tuple(pitches) != elements:
                return None
        elif pattern.pitch_level == "degree":
            degrees = [_degree_of(m, tonic, scale) for m in pitches]
            if any(d is None for d in degrees) or tuple(degrees) != elements:
                return None
        else:  # contour
            moves = ["up" if b > a else ("down" if b < a else "same")
                     for a, b in zip(pitches, pitches[1:])]
            if tuple(moves) != elements:
                return None
        bindings.append(CrossPartLineBinding(midis=pitches, degrees=degrees, moves=moves))
    return bindings


__all__ = [
    "SCHEMA_VERSION", "DOMAIN", "PITCH_LEVELS", "ALIGNMENTS", "CONTOUR_MOVES",
    "CrossPartPattern", "CrossPartValidationError",
    "CrossPartLineBinding", "CrossPartOccurrence", "CrossPartMatches",
    "cross_part_validation_errors", "parse_cross_part_pattern",
    "cross_part_pattern_to_payload", "find_cross_part_pattern",
]
