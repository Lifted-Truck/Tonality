"""Analytical context: the tonal frame a pitch-class object is heard in.

This is the **analytical** counterpart to the display-edge ``DisplayContext``
(``mts/context/``). Where ``DisplayContext`` carries presentation choices (spelling,
label style), :class:`AnalyticalContext` carries *analytical* facts — a tonal
center and an optional operative key (scale/mode) — from which key-relative
analysis (scale-degree membership, diatonic vs chromatic, interval from tonic) is
derived. It is the seed of context-sensitive naming (which name a chord warrants in
a key) and of the enriched dataset record.

Everything here is numeric/identity-level (mod-12); spelling stays at the edge.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from ..core.bitmask import validate_pc
from ..core.chord import Chord
from ..core.scale import Scale


@dataclass(frozen=True)
class AnalyticalContext:
    """The analytical frame: a tonal center (``tonic_pc``) and an optional key.

    ``key`` is the operative scale/mode whose root is the tonal center; its
    ``degrees`` are intervals above ``tonic_pc``. Frozen and hashable.
    """

    tonic_pc: int | None = None
    key: Scale | None = None

    def __post_init__(self) -> None:
        if self.tonic_pc is not None:
            validate_pc(self.tonic_pc)

    @property
    def has_tonic(self) -> bool:
        return self.tonic_pc is not None

    @property
    def has_key(self) -> bool:
        """True when both a key and a tonal center are set."""
        return self.key is not None and self.tonic_pc is not None

    def interval_from_tonic(self, pc: int) -> int | None:
        """``(pc - tonic) % 12``, or ``None`` if no tonal center is set."""
        if self.tonic_pc is None:
            return None
        return (pc - self.tonic_pc) % 12

    def in_key(self, pc: int) -> bool | None:
        """Is ``pc`` diatonic to the key? ``None`` if no key/tonic is set."""
        if not self.has_key:
            return None
        return ((pc - self.tonic_pc) % 12) in set(self.key.degrees)

    def degree_of(self, pc: int) -> int | None:
        """0-based scale-degree index of ``pc`` in the key, or ``None`` if chromatic
        / no key set."""
        if not self.has_key:
            return None
        rel = (pc - self.tonic_pc) % 12
        degrees = list(self.key.degrees)
        return degrees.index(rel) if rel in degrees else None


@dataclass(frozen=True)
class ChordInKey:
    """A chord's structural placement within an :class:`AnalyticalContext`.

    Numeric/analytical only — scale degrees and key membership, not spelling and
    not (yet) functional role (tonic/dominant) or roman-numeral case, which are
    later/edge concerns.
    """

    tonic_pc: int
    key_name: str | None
    root_interval_from_tonic: int
    root_degree: int | None          # 0-based degree of the chord root in the key
    is_diatonic: bool                # every chord tone is in the key
    tone_degrees: list[int | None]   # per chord tone (in chord PC order)
    in_key: list[bool]               # per chord tone
    chromatic_pcs: list[int]         # chord tones not in the key

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def contextualize_chord(chord: Chord, context: AnalyticalContext) -> ChordInKey:
    """Place ``chord`` within the analytical frame.

    Requires a tonal center (the minimum frame); raises ``ValueError`` otherwise —
    analytical placement is not invented from nothing. With no ``key`` set, degree
    / membership fields are ``None`` / ``False`` but intervals-from-tonic are still
    computed.
    """

    if context.tonic_pc is None:
        raise ValueError(
            "contextualize_chord requires a tonal center (AnalyticalContext.tonic_pc)."
        )

    tone_degrees = [context.degree_of(pc) for pc in chord.pcs]
    in_key = [bool(context.in_key(pc)) for pc in chord.pcs]
    chromatic = [pc for pc, ok in zip(chord.pcs, in_key) if not ok] if context.has_key else []
    return ChordInKey(
        tonic_pc=context.tonic_pc,
        key_name=context.key.name if context.key is not None else None,
        root_interval_from_tonic=(chord.root_pc - context.tonic_pc) % 12,
        root_degree=context.degree_of(chord.root_pc),
        is_diatonic=context.has_key and all(in_key),
        tone_degrees=tone_degrees,
        in_key=in_key,
        chromatic_pcs=chromatic,
    )


__all__ = ["AnalyticalContext", "ChordInKey", "contextualize_chord"]
