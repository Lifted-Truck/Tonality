"""Enharmonic naming utilities."""

from __future__ import annotations

from typing import Dict, List, Optional, Literal


SpellingPref = Literal["auto", "sharps", "flats"]

PC_TO_NAMES: Dict[int, List[str]] = {
    0: ["C", "B#", "Dbb"],
    1: ["C#", "Db"],
    2: ["D", "C##", "Ebb"],
    3: ["D#", "Eb", "Fbb"],
    4: ["E", "Fb", "D##"],
    5: ["F", "E#", "Gbb"],
    6: ["F#", "Gb", "E##"],
    7: ["G", "F##", "Abb"],
    8: ["G#", "Ab"],
    9: ["A", "G##", "Bbb"],
    10: ["A#", "Bb", "Cbb"],
    11: ["B", "Cb", "A##"],
}

def _prefer_from_key_signature(sig: Optional[int], fallback: SpellingPref) -> SpellingPref:
    """
    Circle-of-fifths index to preference: -7..+7 (F=-1, Bb=-2, ..., G=+1, D=+2, ...).
    None -> fallback; +N -> sharps; -N -> flats; 0 -> fallback.
    """
    if sig is None:
        return fallback
    if sig > 0:
        return "sharps"
    if sig < 0:
        return "flats"
    return fallback

def name_for_pc(pc: int, *, prefer: SpellingPref = "auto", key_signature: Optional[int] = None) -> str:
    """
    Pick a display name for a pitch class using sharps/flats preference and optional key signature hint.
    """
    names = PC_TO_NAMES.get(pc % 12, [f"pc{pc%12}"])
    eff = _prefer_from_key_signature(key_signature, prefer)

    if eff == "sharps":
        # Prefer names without 'b' (rough but effective)
        for n in names:
            if "b" not in n:
                return n
    if eff == "flats":
        for n in names:
            # Prefer single-flat spellings first when available
            if "b" in n and "bb" not in n:
                return n
        # fall back to any flat if only double-flats exist
        for n in names:
            if "b" in n:
                return n
    # default: first canonical
    return names[0]

# Back-compat helper (used by early code); keep but route through policy-aware function.
def primary_name(pc: int) -> str:
    return name_for_pc(pc, prefer="auto", key_signature=None)