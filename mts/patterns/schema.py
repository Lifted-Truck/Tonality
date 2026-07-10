"""The Pattern object (gap C slice 1): a sequential template with a declared
abstraction level.

Rules say what is *forbidden/required*; patterns say what is **characteristic**.
A pattern is a serializable, versioned object — like a ruleset — describing a
short sequential template plus a **declared abstraction** on two independent
axes (the identity-lattice idea at pattern grain; ROADMAP gap C):

- **pitch axis** — ``"exact"`` (literal MIDI pitches; transposition-sensitive) ·
  ``"degree"`` (scale degrees 1..7; key-relative, transposition-free) ·
  ``"contour"`` (Parsons directions ``up``/``down``/``same``; interval-free).
- **time axis** — ``"exact"`` (declared inter-onset intervals in beats, matched
  exactly) · ``"free"`` (any spacing; the matcher reports the actual IOIs).

Matching is **exact under the declared abstraction** — the lattice *is* the
principled fuzziness (a contour pattern makes no pitch claims; a rhythm-free
pattern makes no timing claims); there are no tolerance knobs in v1. Validation
is **total** (collects every error, the blind-agent contract shared with the
ruleset DSL). Slice-1 domain is ``"melody"`` — one voice line, contiguous notes;
the harmonic-schema and rhythmic-template domains are recorded follow-ons.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

SCHEMA_VERSION = "pattern.1"

PITCH_LEVELS = ("exact", "degree", "contour")
TIME_LEVELS = ("exact", "free")
DOMAINS = ("melody",)  # harmonic schema + rhythmic template = recorded follow-ons
CONTOUR_MOVES = ("up", "down", "same")


class PatternValidationError(ValueError):
    """Raised with the FULL list of validation errors (never just the first)."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid pattern:\n" + "\n".join(f"- {e}" for e in errors))


@dataclass(frozen=True)
class Pattern:
    """A validated sequential template. ``n_notes`` is the matched-window size."""

    name: str
    version: str
    domain: str
    pitch_level: str            # "exact" | "degree" | "contour"
    time_level: str             # "exact" | "free"
    elements: tuple             # midis | degrees | contour moves, per pitch_level
    iois: tuple[float, ...]     # inter-onset intervals; only when time_level=="exact"
    description: str = ""
    schema_version: str = SCHEMA_VERSION

    @property
    def n_notes(self) -> int:
        """Notes per occurrence: elements are notes, except contour = moves (n+1)."""
        return len(self.elements) + 1 if self.pitch_level == "contour" else len(self.elements)


def pattern_validation_errors(payload: object) -> list[str]:
    """Every error in *payload* as a pattern — [] iff valid. Total, never partial."""

    if not isinstance(payload, dict):
        return ["pattern must be a JSON object"]
    errors: list[str] = []

    name = payload.get("name")
    if not isinstance(name, str) or not name:
        errors.append("name: required, a non-empty string")
    version = payload.get("version")
    if not isinstance(version, str) or not version:
        errors.append("version: required, a non-empty string")

    domain = payload.get("domain")
    if domain not in DOMAINS:
        errors.append(f"domain: must be one of {list(DOMAINS)}, got {domain!r}")

    abstraction = payload.get("abstraction")
    pitch_level = time_level = None
    if not isinstance(abstraction, dict):
        errors.append('abstraction: required, an object {"pitch": …, "time": …}')
    else:
        pitch_level = abstraction.get("pitch")
        time_level = abstraction.get("time")
        if pitch_level not in PITCH_LEVELS:
            errors.append(
                f"abstraction.pitch: must be one of {list(PITCH_LEVELS)}, got {pitch_level!r}"
            )
        if time_level not in TIME_LEVELS:
            errors.append(
                f"abstraction.time: must be one of {list(TIME_LEVELS)}, got {time_level!r}"
            )
        unknown = sorted(set(abstraction) - {"pitch", "time"})
        if unknown:
            errors.append(f"abstraction: unknown keys {unknown}")

    elements = payload.get("elements")
    n_notes = None
    if not isinstance(elements, list) or not elements:
        errors.append("elements: required, a non-empty list")
    elif pitch_level == "exact":
        if len(elements) < 2:
            errors.append("elements: a pitch-exact pattern needs >= 2 notes")
        bad = [e for e in elements if not isinstance(e, int) or not 0 <= e <= 127]
        if bad:
            errors.append(f"elements: pitch-exact entries must be MIDI ints 0..127, got {bad}")
        n_notes = len(elements)
    elif pitch_level == "degree":
        if len(elements) < 2:
            errors.append("elements: a degree pattern needs >= 2 notes")
        bad = [e for e in elements if not isinstance(e, int) or not 1 <= e <= 7]
        if bad:
            errors.append(f"elements: degree entries must be ints 1..7, got {bad}")
        n_notes = len(elements)
    elif pitch_level == "contour":
        bad = [e for e in elements if e not in CONTOUR_MOVES]
        if bad:
            errors.append(f"elements: contour entries must be in {list(CONTOUR_MOVES)}, got {bad}")
        n_notes = len(elements) + 1

    iois = payload.get("iois")
    if time_level == "exact":
        if not isinstance(iois, list) or not iois:
            errors.append('iois: required for abstraction.time == "exact" (beats between notes)')
        else:
            bad = [x for x in iois if not isinstance(x, (int, float)) or x <= 0]
            if bad:
                errors.append(f"iois: entries must be positive numbers, got {bad}")
            if n_notes is not None and len(iois) != n_notes - 1:
                errors.append(
                    f"iois: needs exactly n_notes-1 = {n_notes - 1} entries, got {len(iois)}"
                )
    elif iois is not None:
        errors.append('iois: only allowed when abstraction.time == "exact"')

    description = payload.get("description", "")
    if not isinstance(description, str):
        errors.append("description: must be a string when present")

    known = {"schema_version", "name", "version", "domain", "abstraction",
             "elements", "iois", "description"}
    unknown = sorted(set(payload) - known)
    if unknown:
        errors.append(f"unknown keys {unknown}")
    return errors


def parse_pattern(payload: object) -> Pattern:
    """Validate *payload* totally; return the frozen :class:`Pattern` or raise
    :class:`PatternValidationError` with the full error list."""

    errors = pattern_validation_errors(payload)
    if errors:
        raise PatternValidationError(errors)
    assert isinstance(payload, dict)
    abstraction = payload["abstraction"]
    return Pattern(
        name=payload["name"],
        version=payload["version"],
        domain=payload["domain"],
        pitch_level=abstraction["pitch"],
        time_level=abstraction["time"],
        elements=tuple(payload["elements"]),
        iois=tuple(float(x) for x in payload.get("iois") or ()),
        description=payload.get("description", ""),
    )


def pattern_to_payload(pattern: Pattern) -> dict:
    """The JSON payload form (round-trips through :func:`parse_pattern`)."""

    payload: dict = {
        "schema_version": pattern.schema_version,
        "name": pattern.name,
        "version": pattern.version,
        "domain": pattern.domain,
        "abstraction": {"pitch": pattern.pitch_level, "time": pattern.time_level},
        "elements": list(pattern.elements),
    }
    if pattern.time_level == "exact":
        payload["iois"] = list(pattern.iois)
    if pattern.description:
        payload["description"] = pattern.description
    return payload


__all__ = [
    "SCHEMA_VERSION", "PITCH_LEVELS", "TIME_LEVELS", "DOMAINS", "CONTOUR_MOVES",
    "Pattern", "PatternValidationError",
    "pattern_validation_errors", "parse_pattern", "pattern_to_payload",
]
