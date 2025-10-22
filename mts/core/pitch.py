"""Absolute pitch helpers."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import NamedTuple

from .enharmonics import pc_from_name

_NOTE_RE = re.compile(r"^([A-Ga-g][#b]{0,2})(-?\d+)?$")


@dataclass(frozen=True)
class Pitch:
    """Absolute pitch with optional performance metadata."""

    midi: int
    pc: int
    octave: int
    velocity: int | None = None
    channel: int | None = None

    @classmethod
    def from_midi(
        cls,
        midi: int,
        *,
        velocity: int | None = None,
        channel: int | None = None,
    ) -> "Pitch":
        midi_int = int(midi)
        pc = midi_int % 12
        octave = midi_int // 12 - 1  # MIDI octave convention (C4 == 60)
        return cls(
            midi=midi_int,
            pc=pc,
            octave=octave,
            velocity=velocity,
            channel=channel,
        )

    @classmethod
    def from_components(
        cls,
        *,
        pc: int,
        octave: int,
        velocity: int | None = None,
        channel: int | None = None,
    ) -> "Pitch":
        pc_norm = int(pc) % 12
        midi = pc_norm + 12 * (int(octave) + 1)
        return cls.from_midi(midi, velocity=velocity, channel=channel)


class ParsedPitch(NamedTuple):
    pc: int
    pitch: Pitch | None
    token: str
    is_note_token: bool


def parse_pitch_token(token: str) -> ParsedPitch:
    """Parse a token into a pitch-class with optional absolute pitch."""

    stripped = token.strip()
    if not stripped:
        raise ValueError("Empty pitch token.")

    # First attempt integer parsing
    try:
        value = int(stripped)
    except ValueError:
        value = None
    if value is not None:
        if value <= 11:
            return ParsedPitch(pc=value % 12, pitch=None, token=stripped, is_note_token=False)
        pitch = Pitch.from_midi(value)
        return ParsedPitch(pc=pitch.pc, pitch=pitch, token=stripped, is_note_token=False)

    # Match note name with optional octave
    match = _NOTE_RE.match(stripped)
    if not match:
        raise ValueError(f"Unrecognized pitch token {token!r}.")
    note_name, octave_text = match.groups()
    pc = pc_from_name(note_name)
    pitch = None
    if octave_text is not None:
        octave = int(octave_text)
        pitch = Pitch.from_components(pc=pc, octave=octave)
    return ParsedPitch(pc=pc, pitch=pitch, token=stripped, is_note_token=True)

