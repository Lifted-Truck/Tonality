"""Manual scale/chord builder scaffolding + per-session catalog.

``SessionCatalog`` encapsulates all mutable session state so that
multiple independent ``Workspace`` instances can coexist without
sharing global registries.

There is no module-level default session (RE-6b): every caller owns an
explicit ``SessionCatalog``. ``load_scales`` / ``load_chord_qualities`` with
no ``session`` return the base catalog only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count
from pathlib import Path
import json
import os
import sys
from typing import Iterable, Mapping, Sequence, cast

from .core.bitmask import mask_from_pcs, pcs_from_mask
from .core.enharmonics import pc_from_name
from .core.pitch import Pitch
from .core.scale import Scale
from .core.quality import ChordQuality
from .notation import ChordSpec, ScopeLiteral


# ---------------------------------------------------------------------------
# SessionCatalog
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SessionLoadReport:
    """What a session-file load actually did — losses itemized (RE-3g).

    A corrupt file or a bad entry used to be swallowed silently, so a user's
    registered scales/chords could vanish between sessions with no trace.
    ``file_error`` is set when the file existed but could not be parsed
    (nothing loaded); ``skipped`` itemizes per-entry failures
    (``{"kind", "name", "reason"}``).
    """

    path: str
    file_found: bool
    file_error: str | None
    scales_loaded: int
    chords_loaded: int
    skipped: list[dict]

    def to_dict(self) -> dict:
        import dataclasses

        return dataclasses.asdict(self)

@dataclass
class SessionCatalog:
    """Mutable registry for user-defined scales and chords within a session.

    Each ``Workspace`` owns one ``SessionCatalog`` so that multiple
    independent workspaces can coexist without sharing global state.
    """

    scales: dict[str, Scale] = field(default_factory=dict)
    chords: dict[str, ChordQuality] = field(default_factory=dict)
    scale_context: dict[str, dict[str, object]] = field(default_factory=dict)
    chord_context: dict[str, dict[str, object]] = field(default_factory=dict)
    chord_specs: dict[str, ChordSpec] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> "SessionCatalog":
        """Return a fresh, empty catalog (no disk auto-load)."""
        return cls()

    def is_scale(self, name: str) -> bool:
        return name in self.scales

    def is_chord(self, name: str) -> bool:
        return name in self.chords

    def clear(self) -> None:
        self.scales.clear()
        self.chords.clear()
        self.scale_context.clear()
        self.chord_context.clear()
        self.chord_specs.clear()

    # --- Persistence --------------------------------------------------------

    def load(self, path: Path) -> SessionLoadReport:
        """Populate this catalog from a JSON session file.

        Returns a :class:`SessionLoadReport` — a corrupt file or a bad entry
        is never swallowed silently (RE-3g); everything skipped is itemized.
        """
        skipped: list[dict] = []
        scales_loaded = 0
        chords_loaded = 0

        def report(file_found: bool, file_error: str | None) -> SessionLoadReport:
            return SessionLoadReport(
                path=str(path),
                file_found=file_found,
                file_error=file_error,
                scales_loaded=scales_loaded,
                chords_loaded=chords_loaded,
                skipped=skipped,
            )

        if not path.exists():
            return report(False, None)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return report(True, f"unreadable session file: {exc}")
        if not isinstance(data, dict):
            return report(True, f"session file is not a JSON object: {type(data).__name__}")
        for entry in data.get("scales", []):
            name = entry.get("name")
            degrees = entry.get("degrees", [])
            if not name:
                skipped.append({"kind": "scale", "name": None, "reason": "entry has no name"})
                continue
            try:
                scale_builder = ManualScaleBuilder(name=name, degrees=list(degrees))
                scale = scale_builder.to_scale()
            except Exception as exc:
                skipped.append({"kind": "scale", "name": name, "reason": str(exc)})
                continue
            self.scales[scale.name] = scale
            scales_loaded += 1
            context_payload: dict[str, object] = {
                "scope": entry.get("context", "abstract"),
                "tokens": entry.get("tokens", []),
            }
            absolute_midi = entry.get("absolute_midi", [])
            if absolute_midi:
                context_payload["absolute_midi"] = list(absolute_midi)
            self.scale_context[scale.name] = context_payload
        for entry in data.get("chords", []):
            name = entry.get("name")
            intervals = entry.get("intervals", [])
            tensions = entry.get("tensions", [])
            if not name:
                skipped.append({"kind": "chord", "name": None, "reason": "entry has no name"})
                continue
            try:
                chord_builder = ManualChordBuilder(
                    name=name,
                    intervals=list(intervals),
                    tensions=tuple(tensions),
                )
                quality = chord_builder.to_quality()
            except Exception as exc:
                skipped.append({"kind": "chord", "name": name, "reason": str(exc)})
                continue
            self.chords[quality.name] = quality
            chords_loaded += 1
            context_payload = {
                "scope": entry.get("context", "abstract"),
                "tokens": entry.get("tokens", []),
            }
            absolute_midi = entry.get("absolute_midi", [])
            if absolute_midi:
                context_payload["absolute_midi"] = list(absolute_midi)
            self.chord_context[quality.name] = context_payload
            scope = context_payload.get("scope", "abstract")
            tokens = tuple(context_payload.get("tokens", []))
            absolute_pitches = (
                tuple(Pitch.from_midi(midi) for midi in absolute_midi)
                if absolute_midi
                else ()
            )
            if absolute_pitches:
                base_midi = absolute_pitches[0].midi
                voicing = tuple(p.midi - base_midi for p in absolute_pitches)
            else:
                voicing = tuple(quality.intervals)
            spec = ChordSpec(
                label=name,
                scope=cast(ScopeLiteral, scope),
                intervals=tuple(quality.intervals),
                tokens=tokens,
                absolute=absolute_pitches,
                tensions=tuple(getattr(quality, "tensions", ()) or ()),
                voicing=voicing,
            ).with_quality(quality.name, matches=[quality.name])
            self.chord_specs[quality.name] = spec
        return report(True, None)

    def save(self, path: Path) -> None:
        """Persist this catalog to disk as JSON."""
        payload = {
            "scales": [
                {
                    "name": scale.name,
                    "degrees": list(scale.degrees),
                    "context": self.scale_context.get(scale.name, {}).get("scope", "abstract"),
                    "tokens": self.scale_context.get(scale.name, {}).get("tokens", []),
                    "absolute_midi": self.scale_context.get(scale.name, {}).get("absolute_midi", []),
                }
                for scale in self.scales.values()
            ],
            "chords": [
                {
                    "name": quality.name,
                    "intervals": list(quality.intervals),
                    "tensions": list(getattr(quality, "tensions", ()) or ()),
                    "context": self.chord_context.get(quality.name, {}).get("scope", "abstract"),
                    "tokens": self.chord_context.get(quality.name, {}).get("tokens", []),
                    "absolute_midi": self.chord_context.get(quality.name, {}).get("absolute_midi", []),
                }
                for quality in self.chords.values()
            ],
        }
        global _SAVE_SESSION_ERROR_REPORTED
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        except Exception:
            if not _SAVE_SESSION_ERROR_REPORTED:
                print("Warning: Unable to persist session catalog.", file=sys.stderr)
                _SAVE_SESSION_ERROR_REPORTED = True


# ---------------------------------------------------------------------------
# Default session-file location (a convenience path; sessions are owned by
# callers — there is no module-level default session, RE-6b).
# ---------------------------------------------------------------------------

DEFAULT_SESSION_PATH = Path(__file__).resolve().parents[1] / ".tonality_session.json"
SESSION_FILE = Path(os.environ.get("TONALITY_SESSION_FILE", DEFAULT_SESSION_PATH))
_SAVE_SESSION_ERROR_REPORTED = False


# ---------------------------------------------------------------------------
# Builder dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ManualScaleBuilder:
    name: str | None
    degrees: Sequence[int | str]
    tags: tuple[str, ...] = ()
    context: str = "abstract"
    tokens: tuple[str, ...] = ()
    absolute: tuple[Pitch, ...] = ()

    def to_scale(self) -> Scale:
        # 12-TET only; the tuning substrate is renegotiated in ROADMAP Phase 6.
        normalized = _normalize_degrees(self.degrees)
        # Placeholder naming uses an empty registry; register_scale handles
        # collision checking against the active session and catalog.
        name = self.name or _placeholder_name("ManualScale", {}, ())
        return Scale.from_degrees(name, normalized)


@dataclass
class ManualChordBuilder:
    name: str | None
    intervals: Sequence[int | str]
    tensions: Sequence[int | str] = ()
    context: str = "abstract"
    tokens: tuple[str, ...] = ()
    absolute: tuple[Pitch, ...] = ()

    def to_quality(self) -> ChordQuality:
        # 12-TET only; arbitrary tunings are ROADMAP Phase 6.
        normalized_intervals = _normalize_intervals(self.intervals)
        normalized_tensions = tuple(_normalize_degrees(self.tensions)) if self.tensions else ()
        # Placeholder naming uses an empty registry; register_chord handles
        # collision checking against the active session and catalog.
        name = self.name or _placeholder_name("ManualChord", {}, ())
        return ChordQuality.from_intervals(name, normalized_intervals, normalized_tensions)

    def to_spec(self) -> ChordSpec:
        normalized_intervals = tuple(_normalize_intervals(self.intervals))
        normalized_tensions = tuple(_normalize_degrees(self.tensions)) if self.tensions else ()
        tokens, scope = _chord_builder_tokens_and_scope(self)
        absolute_filtered = tuple(p for p in self.absolute if p is not None)
        if absolute_filtered:
            base_midi = absolute_filtered[0].midi
            voicing = tuple(p.midi - base_midi for p in absolute_filtered)
        else:
            voicing = normalized_intervals
        return ChordSpec(
            label=self.name,
            scope=scope,
            intervals=normalized_intervals,
            tokens=tokens,
            absolute=absolute_filtered,
            tensions=normalized_tensions,
            voicing=voicing,
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _placeholder_name(stem: str, registry: Mapping[str, object], existing: Iterable[str]) -> str:
    taken = set(registry.keys()) | set(existing)
    for idx in count(1):
        candidate = f"{stem}-{idx}"
        if candidate not in taken:
            return candidate
    return stem


def _builder_context_payload(builder) -> dict[str, object]:
    scope = getattr(builder, "context", "abstract") or "abstract"
    tokens_attr = tuple(getattr(builder, "tokens", ()) or ())
    absolute_attr = tuple(getattr(builder, "absolute", ()) if hasattr(builder, "absolute") else ())
    absolute = [pitch.midi for pitch in absolute_attr if pitch is not None]

    if isinstance(builder, ManualChordBuilder):
        inferred_tokens, scope = _chord_builder_tokens_and_scope(builder)
        tokens = list(inferred_tokens)
    else:
        tokens = list(tokens_attr)
    payload: dict[str, object] = {"scope": scope}
    if tokens:
        payload["tokens"] = tokens
    if absolute:
        payload["absolute_midi"] = absolute
    return payload


def _chord_builder_tokens_and_scope(builder: ManualChordBuilder) -> tuple[tuple[str, ...], ScopeLiteral]:
    scope = cast(ScopeLiteral, (builder.context or "abstract"))
    tokens: tuple[str, ...] = tuple(builder.tokens or ())
    absolute_filtered = tuple(p for p in builder.absolute if p is not None)

    if absolute_filtered:
        return tokens, cast(ScopeLiteral, "absolute")

    if tokens:
        return tokens, scope

    string_tokens = tuple(value for value in builder.intervals if isinstance(value, str))
    if string_tokens:
        inferred_scope = scope if scope != "abstract" else cast(ScopeLiteral, "note")
        return string_tokens, inferred_scope

    return (), scope


def _normalize_degrees(degrees: Iterable[int | str]) -> list[int]:
    normalized: set[int] = set()
    for value in degrees:
        if isinstance(value, str):
            normalized.add(pc_from_name(value))
        else:
            normalized.add(int(value) % 12)
    return sorted(normalized)


def _normalize_intervals(intervals: Iterable[int | str]) -> list[int]:
    normalized: set[int] = set()
    for value in intervals:
        if isinstance(value, str):
            normalized.add(pc_from_name(value))
        else:
            normalized.add(int(value) % 12)
    return sorted(normalized)


# ---------------------------------------------------------------------------
# Public catalog functions
# ---------------------------------------------------------------------------

def match_scale(degrees: Iterable[int], catalog: Mapping[str, Scale]) -> list[Scale]:
    target = _normalize_degrees(degrees)
    target_mask = mask_from_pcs(target)
    matches: list[Scale] = []
    seen: set[str] = set()
    for scale in catalog.values():
        if mask_from_pcs(scale.degrees) == target_mask:
            if scale.name not in seen:
                seen.add(scale.name)
                matches.append(scale)
    return matches


def match_chord(intervals: Iterable[int], catalog: Mapping[str, ChordQuality]) -> list[ChordQuality]:
    target = _normalize_intervals(intervals)
    matches: list[ChordQuality] = []
    seen: set[str] = set()
    for quality in catalog.values():
        if _normalize_intervals(quality.intervals) == target:
            if quality.name not in seen:
                seen.add(quality.name)
                matches.append(quality)
    return matches


def register_scale(
    builder: ManualScaleBuilder,
    *,
    catalog: Mapping[str, Scale] | None = None,
    session: SessionCatalog | None = None,
    auto_placeholder: bool = True,
    persist: bool = False,
    session_path: Path | None = None,
) -> dict[str, object]:
    """Register a scale in *session* (required — each ``Workspace`` owns one)."""
    if session is None:
        raise ValueError(
            "register_scale requires an explicit session (the module-level "
            "default was retired, RE-6b). Pass session=SessionCatalog()."
        )
    _session = session
    catalog = catalog or {}
    context_payload = _builder_context_payload(builder)
    matches = match_scale(builder.degrees, catalog)
    if matches:
        scale = matches[0]
        _session.scales[scale.name] = scale
        _session.scale_context[scale.name] = context_payload
        if persist:
            _session.save(session_path or SESSION_FILE)
        return {"scale": scale, "match": matches, "context": context_payload}

    scale = builder.to_scale()
    if auto_placeholder and (scale.name in catalog or scale.name in _session.scales):
        placeholder = _placeholder_name("ManualScale", _session.scales, catalog.keys())
        scale = Scale.from_degrees(placeholder, scale.degrees)
    _session.scales[scale.name] = scale
    _session.scale_context[scale.name] = context_payload
    if persist:
        _session.save(session_path or SESSION_FILE)
    return {"scale": scale, "match": [], "context": context_payload}


def register_chord(
    builder: ManualChordBuilder,
    *,
    catalog: Mapping[str, ChordQuality] | None = None,
    session: SessionCatalog | None = None,
    auto_placeholder: bool = True,
    persist: bool = False,
    session_path: Path | None = None,
) -> dict[str, object]:
    """Register a chord quality in *session* (required — each ``Workspace`` owns one)."""
    if session is None:
        raise ValueError(
            "register_chord requires an explicit session (the module-level "
            "default was retired, RE-6b). Pass session=SessionCatalog()."
        )
    _session = session
    catalog = catalog or {}
    context_payload = _builder_context_payload(builder)
    base_spec = builder.to_spec()
    matches = match_chord(builder.intervals, catalog)
    if matches:
        quality = matches[0]
        _session.chords[quality.name] = quality
        _session.chord_context[quality.name] = context_payload
        spec = base_spec.with_quality(
            quality.name,
            matches=[match.name for match in matches],
        )
        _session.chord_specs[quality.name] = spec
        if persist:
            _session.save(session_path or SESSION_FILE)
        return {"quality": quality, "match": matches, "context": context_payload, "spec": spec}

    quality = builder.to_quality()
    if auto_placeholder and (quality.name in catalog or quality.name in _session.chords):
        placeholder = _placeholder_name("ManualChord", _session.chords, catalog.keys())
        quality = ChordQuality.from_intervals(placeholder, quality.intervals, quality.tensions)
    _session.chords[quality.name] = quality
    _session.chord_context[quality.name] = context_payload
    spec = base_spec.with_quality(
        quality.name,
        matches=[match.name for match in matches],
    )
    _session.chord_specs[quality.name] = spec
    if persist:
        _session.save(session_path or SESSION_FILE)
    return {"quality": quality, "match": [], "context": context_payload, "spec": spec}


def degrees_from_mask(mask: int) -> list[int]:
    """Convert a pitch-class mask into normalized degrees."""
    return pcs_from_mask(mask)


def mask_from_text(text: str) -> int:
    """Parse a decimal or binary mask string — without guessing.

    Binary is read from a ``0b`` prefix or a full 12-character 0/1 string
    (unambiguous: a decimal mask never has 12 digits). A shorter 0/1-only
    string like ``"10"`` is ambiguous (binary 2 or decimal 10?) and raises
    instead of silently picking one; write ``0b10`` or a non-0/1 decimal.
    Values above 4095 raise instead of being silently truncated to 12 bits.
    """
    stripped = text.strip().lower()
    if stripped.startswith("0b"):
        value = int(stripped[2:], 2)
    elif stripped and set(stripped) <= {"0", "1"}:
        if len(stripped) == 12:
            value = int(stripped, 2)
        else:
            raise ValueError(
                f"Ambiguous mask text {text!r}: could be binary or decimal. "
                "Use a '0b' prefix for binary (e.g. '0b10') or a full "
                "12-character bit string."
            )
    else:
        value = int(stripped, 10)
    if not 0 <= value < (1 << 12):
        raise ValueError(f"Mask out of range: {value} (must be 0..4095).")
    return value


# ---------------------------------------------------------------------------
# Session helpers — the caller owns the session (no module-level default, RE-6b)
# ---------------------------------------------------------------------------

def load_session_catalog(
    session: SessionCatalog, path: Path | None = None
) -> SessionLoadReport:
    """Load a session JSON file into *session*.

    Returns the itemized :class:`SessionLoadReport` (RE-3g)."""
    return session.load(path or SESSION_FILE)


def save_session_catalog(session: SessionCatalog, path: Path | None = None) -> None:
    """Persist *session* to disk."""
    session.save(path or SESSION_FILE)
