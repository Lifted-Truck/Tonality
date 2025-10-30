"""Specification helpers for user-defined musical objects."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Iterable, Literal, Mapping, Sequence, Tuple

from ..core.enharmonics import name_for_pc
from ..core.pitch import Pitch, parse_pitch_token, ParsedPitch
from ..core.quality import ChordQuality

ScopeLiteral = Literal["abstract", "note", "absolute"]


@dataclass(frozen=True)
class ChordSpec:
    """Concrete description of a chord as provided by the user."""

    label: str | None
    scope: ScopeLiteral
    intervals: tuple[int, ...]
    tokens: tuple[str, ...] = ()
    absolute: tuple[Pitch, ...] = ()
    tensions: tuple[int, ...] = ()
    voicing: tuple[int, ...] = ()
    quality_name: str | None = None
    quality_matches: tuple[str, ...] = ()
    quality_subsets: tuple["QualityVariant", ...] = ()
    quality_supersets: tuple["QualityVariant", ...] = ()
    quality_cousins: tuple["QualityVariant", ...] = ()

    def with_quality(
        self,
        name: str,
        *,
        matches: Iterable[str] | None = None,
    ) -> "ChordSpec":
        """Return a copy annotated with the resolved quality metadata."""

        match_names: Tuple[str, ...] = tuple(matches or ())
        return replace(self, quality_name=name, quality_matches=match_names)

    @property
    def absolute_midi(self) -> tuple[int, ...]:
        """Return MIDI numbers for any absolute pitches captured in the spec."""

        return tuple(p.midi for p in self.absolute)


@dataclass(frozen=True)
class ChordParseResult:
    """Composite output describing the parsed chord input."""

    spec: ChordSpec
    root_pc: int | None = None
    root_pitch: Pitch | None = None


@dataclass(frozen=True)
class QualityVariant:
    """Describes the relationship between a chord and a catalog quality."""

    name: str
    missing: tuple[int, ...] = ()
    extra: tuple[int, ...] = ()
    distance: int = 0


def parse_chord_spec(
    text: str,
    *,
    catalog: Mapping[str, ChordQuality] | None = None,
) -> ChordParseResult:
    """
    Parse rich chord expressions into a ChordSpec.

    Supported forms:
      - [0,3,7], [P1,m3,P5]             # interval lists (may exceed 12 for voicings)
      - (1,b3,5)                        # degree lists relative to the root
      - [C,E,G], [C3,E3,G3]             # note tokens (with or without octaves)
      - {60,63,67}                      # explicit MIDI pitches
      - myChord (requires catalog match)
      - min, C:min, C3:min (requires catalog match)
      - C3[0,3,7], C3(1,b3,5), 60{0,4,7}, etc.
      - inline aliasing via `=label` (e.g., C3[0,3,7]=myChord)
    """

    if catalog is None:
        from ..io.loaders import load_chord_qualities

        catalog = load_chord_qualities()

    core, label = _split_alias(text.strip())
    if not core:
        raise ValueError("Empty chord expression.")

    bracket_match = re.search(r"([\[\(\{])", core)
    if bracket_match:
        delimiter = bracket_match.group(1)
        closing = _BRACKET_PAIRS[delimiter]
        if closing not in core:
            raise ValueError(f"Missing closing bracket {closing!r} in chord expression.")
        prefix, payload = _split_bracket_payload(core, delimiter, closing)
        root_pc, root_pitch = _parse_root_token(prefix)
        seq = _parse_sequence(payload, delimiter, root_pc=root_pc, root_pitch=root_pitch)
        spec = ChordSpec(
            label=label or seq.label,
            scope=seq.scope,
            intervals=seq.intervals,
            tokens=seq.tokens,
            absolute=seq.absolute,
            voicing=seq.voicing,
        )
        spec = _annotate_spec(spec, catalog)
        return ChordParseResult(
            spec=spec,
            root_pc=seq.root_pc if seq.root_pc is not None else root_pc,
            root_pitch=seq.root_pitch if seq.root_pitch is not None else root_pitch,
        )

    if ":" in core:
        root_token, quality_token = core.split(":", 1)
        quality = _resolve_quality(quality_token.strip(), catalog)
        root_pc, root_pitch = _parse_root_token(root_token.strip())
        spec = _spec_from_quality(quality, label=label)
        spec, root_pc, root_pitch = _apply_root(spec, root_pc, root_pitch)
        spec = _annotate_spec(spec, catalog)
        return ChordParseResult(spec=spec, root_pc=root_pc, root_pitch=root_pitch)

    # bare quality name or alias referencing catalog
    quality = _resolve_quality(core, catalog)
    spec = _spec_from_quality(quality, label=label)
    spec = _annotate_spec(spec, catalog)
    return ChordParseResult(spec=spec, root_pc=None, root_pitch=None)


# ---------------------------------------------------------------------------
# internal helpers


_INTERVAL_RE = re.compile(r"^(?P<quality>[PMAmd])(?P<number>\d{1,2})$")
_DEGREE_RE = re.compile(r"^(?P<acc>bb|b|##|#)?(?P<number>\d+)$")
_BRACKET_PAIRS = {"[": "]", "(": ")", "{": "}"}


@dataclass
class _ParsedSequence:
    intervals: tuple[int, ...]
    tokens: tuple[str, ...]
    absolute: tuple[Pitch, ...]
    scope: ScopeLiteral
    root_pc: int | None = None
    root_pitch: Pitch | None = None
    label: str | None = None
    quality_name: str | None = None
    voicing: tuple[int, ...] = ()


def _split_alias(expr: str) -> tuple[str, str | None]:
    if "=" not in expr:
        return expr, None
    core, alias = expr.split("=", 1)
    alias = alias.strip() or None
    return core.strip(), alias


def _split_bracket_payload(expr: str, delimiter: str, closing: str) -> tuple[str, str]:
    left = expr.index(delimiter)
    right = expr.rindex(closing)
    prefix = expr[:left].strip()
    payload = expr[left + 1 : right].strip()
    return prefix, payload


def _parse_root_token(token: str) -> tuple[int | None, Pitch | None]:
    token = token.strip()
    if not token:
        return None, None
    parsed = parse_pitch_token(token)
    return parsed.pc, parsed.pitch


def _parse_sequence(
    payload: str,
    delimiter: str,
    *,
    root_pc: int | None,
    root_pitch: Pitch | None,
) -> _ParsedSequence:
    parts = [item.strip() for item in payload.split(",") if item.strip()]
    if not parts:
        raise ValueError("Chord definition requires at least one element inside brackets.")

    if delimiter == "{":
        values = [_parse_int_token(item) for item in parts]
        pitches = tuple(Pitch.from_midi(value) for value in values)
        base_pitch = root_pitch or pitches[0]
        intervals, voicing = _intervals_from_absolute(pitches, base_pitch)
        return _ParsedSequence(
            intervals=intervals,
            tokens=tuple(parts),
            absolute=pitches,
            scope="absolute",
            root_pc=base_pitch.pc,
            root_pitch=base_pitch,
            voicing=voicing,
        )

    if delimiter == "(":
        pcs: list[int] = []
        raws: list[int] = []
        for item in parts:
            pc, raw = _degree_to_values(item)
            pcs.append(pc)
            raws.append(raw)
        intervals = tuple(sorted({pc % 12 for pc in pcs}))
        voicing = tuple(raws)
        spec = _ParsedSequence(
            intervals=intervals,
            tokens=tuple(parts),
            absolute=tuple(),
            scope="abstract",
            root_pc=root_pc,
            root_pitch=root_pitch,
            voicing=voicing,
        )
        if root_pitch or root_pc is not None:
            return _apply_root_to_sequence(spec, root_pc, root_pitch)
        return spec

    # default: "[" ... "]"
    if _all_int(parts):
        values = [_parse_int_token(item) for item in parts]
        intervals = tuple(sorted({value % 12 for value in values}))
        voicing = tuple(values)
        spec = _ParsedSequence(
            intervals=intervals,
            tokens=tuple(parts),
            absolute=tuple(),
            scope="abstract",
            root_pc=root_pc,
            root_pitch=root_pitch,
            voicing=voicing,
        )
        if root_pitch or root_pc is not None:
            return _apply_root_to_sequence(spec, root_pc, root_pitch)
        return spec

    if all(_INTERVAL_RE.match(item) for item in parts):
        values = [_interval_from_name(item) for item in parts]
        intervals = tuple(sorted({value % 12 for value in values}))
        voicing = tuple(values)
        spec = _ParsedSequence(
            intervals=intervals,
            tokens=tuple(parts),
            absolute=tuple(),
            scope="abstract",
            root_pc=root_pc,
            root_pitch=root_pitch,
            voicing=voicing,
        )
        if root_pitch or root_pc is not None:
            return _apply_root_to_sequence(spec, root_pc, root_pitch)
        return spec

    if all(_DEGREE_RE.match(item) for item in parts):
        pcs: list[int] = []
        raws: list[int] = []
        for token in parts:
            pc, raw = _degree_to_values(token)
            pcs.append(pc)
            raws.append(raw)
        intervals = tuple(sorted({pc % 12 for pc in pcs}))
        voicing = tuple(raws)
        spec = _ParsedSequence(
            intervals=intervals,
            tokens=tuple(parts),
            absolute=tuple(),
            scope="abstract",
            root_pc=root_pc,
            root_pitch=root_pitch,
            voicing=voicing,
        )
        if root_pitch or root_pc is not None:
            return _apply_root_to_sequence(spec, root_pc, root_pitch)
        return spec

    parsed = [_parse_note_token(item) for item in parts]
    if any(item.pitch is not None for item in parsed):
        if any(item.pitch is None for item in parsed):
            raise ValueError("Mixing absolute and note-only tokens in the same list is not supported.")
        pitches = tuple(item.pitch for item in parsed if item.pitch is not None)
        base_pitch = root_pitch or pitches[0]
        intervals, voicing = _intervals_from_absolute(pitches, base_pitch)
        return _ParsedSequence(
            intervals=intervals,
            tokens=tuple(item.token for item in parsed),
            absolute=pitches,
            scope="absolute",
            root_pc=base_pitch.pc,
            root_pitch=base_pitch,
            voicing=voicing,
        )

    pcs = [item.pc for item in parsed]
    base_pc = root_pc if root_pc is not None else pcs[0]
    intervals = tuple(sorted({(pc - base_pc) % 12 for pc in pcs}))
    tokens = tuple(item.token for item in parsed)
    return _ParsedSequence(
        intervals=intervals,
        tokens=tokens,
        absolute=tuple(),
        scope="note",
        root_pc=base_pc,
        root_pitch=root_pitch,
        voicing=tuple(),
    )


def _apply_root_to_sequence(
    sequence: _ParsedSequence,
    root_pc: int | None,
    root_pitch: Pitch | None,
) -> _ParsedSequence:
    if sequence.scope != "abstract":
        return sequence
    if root_pitch is not None:
        if sequence.voicing:
            offsets = sequence.voicing
        else:
            offsets = tuple(sorted(sequence.intervals))
        absolute = tuple(Pitch.from_midi(root_pitch.midi + offset) for offset in offsets)
        intervals = tuple(sorted({offset % 12 for offset in offsets}))
        return _ParsedSequence(
            intervals=intervals,
            tokens=tuple(_format_pitch_token(pitch) for pitch in absolute),
            absolute=absolute,
            scope="absolute",
            root_pc=root_pitch.pc,
            root_pitch=root_pitch,
            voicing=offsets,
        )
    if root_pc is not None:
        if sequence.voicing:
            offsets = tuple(offset % 12 for offset in sequence.voicing)
        else:
            offsets = tuple(sorted(sequence.intervals))
        tokens = tuple(name_for_pc((root_pc + offset) % 12) for offset in offsets)
        return _ParsedSequence(
            intervals=tuple(sorted({offset % 12 for offset in offsets})),
            tokens=tokens,
            absolute=tuple(),
            scope="note",
            root_pc=root_pc,
            root_pitch=None,
            voicing=sequence.voicing,
        )
    return sequence


def _resolve_quality(name: str, catalog: Mapping[str, ChordQuality] | None) -> ChordQuality:
    key = name.strip()
    if key not in catalog:
        raise ValueError(f"Unknown chord quality {name!r}.")
    return catalog[key]


def _spec_from_quality(quality: ChordQuality, *, label: str | None) -> ChordSpec:
    intervals = tuple(sorted({int(iv) % 12 for iv in quality.intervals}))
    tensions = tuple(int(tv) % 12 for tv in getattr(quality, "tensions", ()) or ())
    voicing = tuple(sorted({int(iv) % 12 for iv in quality.intervals}))
    spec = ChordSpec(label=label, scope="abstract", intervals=intervals, tensions=tensions, voicing=voicing)
    return spec.with_quality(quality.name, matches=(quality.name,))


def _apply_root(
    spec: ChordSpec,
    root_pc: int | None,
    root_pitch: Pitch | None,
) -> tuple[ChordSpec, int | None, Pitch | None]:
    if spec.scope != "abstract":
        return spec, root_pc, root_pitch
    if root_pitch is not None:
        if spec.voicing:
            offsets = spec.voicing
        else:
            offsets = tuple(sorted(spec.intervals))
        absolute = tuple(Pitch.from_midi(root_pitch.midi + offset) for offset in offsets)
        tokens = tuple(_format_pitch_token(p) for p in absolute)
        intervals = tuple(sorted({offset % 12 for offset in offsets}))
        spec = replace(spec, scope="absolute", absolute=absolute, tokens=tokens, intervals=intervals, voicing=offsets)
        return spec, root_pitch.pc, root_pitch
    if root_pc is not None:
        if spec.voicing:
            offsets = tuple(offset % 12 for offset in spec.voicing)
        else:
            offsets = tuple(sorted(spec.intervals))
        tokens = tuple(name_for_pc((root_pc + offset) % 12) for offset in offsets)
        intervals = tuple(sorted({offset % 12 for offset in offsets}))
        spec = replace(spec, scope="note", tokens=tokens, intervals=intervals)
    return spec, root_pc, root_pitch


def _intervals_from_absolute(pitches: Sequence[Pitch], base: Pitch) -> tuple[tuple[int, ...], tuple[int, ...]]:
    raw = tuple(pitch.midi - base.midi for pitch in pitches)
    normalized = tuple(sorted({value % 12 for value in raw}))
    return normalized, raw


def _parse_note_token(token: str) -> ParsedPitch:
    try:
        return parse_pitch_token(token)
    except ValueError as exc:
        raise ValueError(f"Unrecognized chord token {token!r}.") from exc


def _all_int(parts: Sequence[str]) -> bool:
    try:
        for item in parts:
            int(item)
    except ValueError:
        return False
    return True


def _interval_from_name(token: str) -> int:
    match = _INTERVAL_RE.match(token)
    if not match:
        raise ValueError(f"Invalid interval token {token!r}.")
    quality = match.group("quality")
    number = int(match.group("number"))
    base = _major_scale_semitones((number - 1) % 7 + 1)
    octaves = (number - 1) // 7
    semitone = base + 12 * octaves
    return _adjust_semitone(semitone, quality, number)


def _major_scale_semitones(step: int) -> int:
    return {
        1: 0,
        2: 2,
        3: 4,
        4: 5,
        5: 7,
        6: 9,
        7: 11,
    }[step]


def _adjust_semitone(semitone: int, quality: str, number: int) -> int:
    perfect = number in {1, 4, 5, 8, 11, 12}
    if quality == "P":
        return semitone
    if quality == "M":
        if perfect:
            raise ValueError(f"Quality 'M' invalid for perfect interval number {number}.")
        return semitone
    if quality == "m":
        if perfect:
            raise ValueError(f"Quality 'm' invalid for perfect interval number {number}.")
        return semitone - 1
    if quality == "A":
        return semitone + 1
    if quality == "d":
        return semitone - 1 if perfect else semitone - 2
    raise ValueError(f"Unsupported interval quality {quality!r}.")


def _degree_to_values(token: str) -> tuple[int, int]:
    match = _DEGREE_RE.match(token)
    if not match:
        raise ValueError(f"Invalid scale-degree token {token!r}.")
    acc = match.group("acc") or ""
    number = int(match.group("number"))
    base = _major_scale_semitones((number - 1) % 7 + 1)
    octaves = (number - 1) // 7
    semitone = base + 12 * octaves
    adjustment = 0
    if acc:
        if "b" in acc:
            adjustment -= len(acc)
        if "#" in acc:
            adjustment += len(acc)
    value = semitone + adjustment
    return value % 12, value


def _format_pitch_token(pitch: Pitch) -> str:
    name = name_for_pc(pitch.pc)
    return f"{name}{pitch.octave}"


def _parse_int_token(token: str) -> int:
    try:
        return int(token)
    except ValueError as exc:
        raise ValueError(f"Expected integer token, got {token!r}.") from exc


def _annotate_spec(spec: ChordSpec, catalog: Mapping[str, ChordQuality]) -> ChordSpec:
    if not catalog:
        return spec
    classification = _classify_qualities(spec.intervals, catalog)

    existing_matches = set(spec.quality_matches)
    if spec.quality_name:
        existing_matches.add(spec.quality_name)
    existing_matches.update(classification["exact"])
    ordered_matches = tuple(sorted(existing_matches))

    primary = spec.quality_name
    if not primary and ordered_matches:
        primary = ordered_matches[0]

    return replace(
        spec,
        quality_name=primary,
        quality_matches=ordered_matches,
        quality_subsets=classification["subsets"],
        quality_supersets=classification["supersets"],
        quality_cousins=classification["cousins"],
    )


def _classify_qualities(intervals: Iterable[int], catalog: Mapping[str, ChordQuality]) -> dict[str, tuple]:
    chord_set = {int(iv) % 12 for iv in intervals}
    limit = 6
    exact: list[str] = []
    subsets: list[QualityVariant] = []
    supersets: list[QualityVariant] = []
    cousins: list[QualityVariant] = []

    for name, quality in catalog.items():
        quality_set = {int(iv) % 12 for iv in quality.intervals}
        missing = tuple(sorted(quality_set - chord_set))
        extra = tuple(sorted(chord_set - quality_set))
        if not missing and not extra:
            exact.append(name)
            continue
        distance = len(missing) + len(extra)
        variant = QualityVariant(name=name, missing=missing, extra=extra, distance=distance)
        if missing and not extra:
            subsets.append(variant)
        elif extra and not missing:
            supersets.append(variant)
        else:
            cousins.append(variant)

    subsets.sort(key=lambda v: (v.distance, v.name))
    supersets.sort(key=lambda v: (v.distance, v.name))
    cousins.sort(key=lambda v: (v.distance, v.name))

    return {
        "exact": tuple(sorted(exact))[:limit],
        "subsets": tuple(subsets[:limit]),
        "supersets": tuple(supersets[:limit]),
        "cousins": tuple(cousins[:limit]),
    }


__all__ = ["ChordParseResult", "ChordSpec", "ScopeLiteral", "QualityVariant", "parse_chord_spec"]
