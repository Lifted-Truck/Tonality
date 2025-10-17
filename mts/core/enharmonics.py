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
    Choose a practical display name for a pitch class.
    Rules:
      1) Prefer naturals if present.
      2) If both flat and sharp options exist, honor preference (key_signature or 'prefer'),
         choosing single accidentals over double.
      3) If only one family exists (only flats or only sharps), prefer single accidentals.
      4) Else fall back to the first canonical name.
    """
    names = PC_TO_NAMES.get(pc % 12, [f"pc{pc%12}"])
    eff = _prefer_from_key_signature(key_signature, prefer)

    # Buckets
    naturals = [n for n in names if ("b" not in n and "#" not in n)]
    single_flats = [n for n in names if "b" in n and "bb" not in n]
    multi_flats  = [n for n in names if "bb" in n]
    single_sharps = [n for n in names if "#" in n and "##" not in n]
    multi_sharps  = [n for n in names if "##" in n]

    # 1) Naturals win when available
    if naturals:
        return naturals[0]

    # Helper pickers
    def pick_flats() -> str:
        if single_flats: return single_flats[0]
        if multi_flats:  return multi_flats[0]
        # if no flats, fall back to anything available
        if single_sharps: return single_sharps[0]
        if multi_sharps:  return multi_sharps[0]
        return names[0]

    def pick_sharps() -> str:
        if single_sharps: return single_sharps[0]
        if multi_sharps:  return multi_sharps[0]
        if single_flats:  return single_flats[0]
        if multi_flats:   return multi_flats[0]
        return names[0]

    has_flats = bool(single_flats or multi_flats)
    has_sharps = bool(single_sharps or multi_sharps)

    # 2) Both families present → honor preference
    if has_flats and has_sharps:
        return pick_flats() if eff == "flats" else pick_sharps()

    # 3) Only one family present
    if has_flats:
        return pick_flats()
    if has_sharps:
        return pick_sharps()

    # 4) Fallback
    return names[0]


# Back-compat helper (used by early code); keep but route through policy-aware function.
def primary_name(pc: int) -> str:
    return name_for_pc(pc, prefer="auto", key_signature=None)

# ---------- CLI-friendly parsing helpers ----------

# Normalize simple unicode accidentals for CLI input
_ACCENTS = {
    "♯": "#",
    "♭": "b",
    "𝄪": "##",
    "𝄫": "bb",
}

def _normalize_note_str(s: str) -> str:
    s = s.strip()
    for k, v in _ACCENTS.items():
        s = s.replace(k, v)
    return s.capitalize()  # c# -> C#

# Build a reverse map from common spellings to pitch-class integers.
_NAME_TO_PC: Dict[str, int] = {}
for pc, names in PC_TO_NAMES.items():
    for n in names:
        _NAME_TO_PC[n] = pc
# Add a few super-common fallbacks explicitly
_NAME_TO_PC.update({
    "Db": 1, "C#": 1,
    "Eb": 3, "D#": 3,
    "Gb": 6, "F#": 6,
    "Ab": 8, "G#": 8,
    "Bb": 10, "A#": 10,
})

def pc_from_name(name: str) -> int:
    """
    Parse a note name like 'C', 'Db', 'F#', 'Cb', 'E#' into a pitch class 0..11.
    Accepts unicode ♯/♭ and normalizes.
    """
    key = _normalize_note_str(name)
    if key in _NAME_TO_PC:
        return _NAME_TO_PC[key]
    raise ValueError(f"Unrecognized note name: {name!r}")