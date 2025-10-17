from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional, Tuple

from .push3 import Push3Layout
from ..core.bitmask import validate_pc, mask_from_pcs
from ..core.enharmonics import PC_TO_NAMES

DegreeStyle = Literal["names", "degrees"]
SpellingPref = Literal["auto", "sharps", "flats"]
LayoutPreset = Literal["fourths", "thirds", "sequential"]
LayoutMode = Literal["chromatic", "in_scale"]
AnchorMode = Literal["fixed_C", "fixed_root"]


# ---------- helpers ----------

_BASE_DEGREE = {
    0: "1", 1: "b2", 2: "2", 3: "b3", 4: "3",
    5: "4", 6: "#4", 7: "5", 8: "b6", 9: "6",
    10: "b7", 11: "7",
}

def _name_for_pc(pc: int, prefer: SpellingPref = "auto") -> str:
    names = PC_TO_NAMES.get(pc % 12, [f"pc{pc%12}"])
    if prefer == "sharps":
        for n in names:
            if "b" not in n:
                return n
    if prefer == "flats":
        for n in names:
            if "b" in n and "bb" not in n:
                return n
    return names[0]

def _degree_for_pc(pc: int, tonic_pc: int) -> str:
    rel = (pc - (tonic_pc % 12)) % 12
    return _BASE_DEGREE[rel]

def _pad2(s: str) -> str:
    return s if len(s) >= 2 else s + "-"

def _row_offset_for(preset: LayoutPreset) -> int:
    return {"fourths": 5, "thirds": 4, "sequential": 1}[preset]


# ---------- Cell object ----------

@dataclass
class PushCell:
    row: int
    col: int
    pc: int                                 # absolute pc shown on this pad
    tonic_pc: int                           # context tonic for degrees/marking
    scale_degrees_rel: Optional[set[int]]   # relative-to-tonic pcs in key
    chord_pcs_abs: Optional[set[int]]       # absolute pcs in chord
    degree_style: DegreeStyle               # "names" | "degrees"
    spelling: SpellingPref                  # "auto" | "sharps" | "flats"
    layout_mode: LayoutMode                 # "chromatic" | "in_scale"
    hide_out_of_key: bool = False

    # cached fields set on init/update
    in_key: bool = field(init=False)
    is_tonic: bool = field(init=False)
    in_chord: bool = field(init=False)

    def __post_init__(self) -> None:
        validate_pc(self.pc)
        validate_pc(self.tonic_pc)
        rel = (self.pc - self.tonic_pc) % 12
        self.in_key = (self.scale_degrees_rel is None) or (rel in self.scale_degrees_rel)
        self.is_tonic = (self.pc % 12) == (self.tonic_pc % 12)
        self.in_chord = bool(self.chord_pcs_abs) and ((self.pc % 12) in self.chord_pcs_abs)

    # — render token like:  [{C-}*]  [(D-)-]  [[D#]-]
    def render(self) -> str:
        if self.layout_mode == "in_scale" and self.hide_out_of_key and not self.in_key:
            return "[     ]"  # fixed width spacer (7 chars)

        # core 2-char label
        if self.degree_style == "degrees":
            token = _pad2(_degree_for_pc(self.pc, self.tonic_pc))
        else:
            token = _pad2(_name_for_pc(self.pc, self.spelling))

        # inner brackets: tonic { }, in-key ( ), out-of-key [ ]
        if self.is_tonic:
            inner = "{%s}" % token
        else:
            inner = f"({token})" if self.in_key else f"[{token}]"

        # external mark: * if in chord else -
        mark = "*" if self.in_chord else "-"

        return f"[{inner}{mark}]"


# ---------- Grid object ----------

@dataclass
class PushGrid:
    # layout & anchoring
    preset: LayoutPreset = "fourths"
    anchor: AnchorMode = "fixed_C"     # fixed_C | fixed_root
    root_pc: int = 0                   # used when anchor=fixed_root

    # musical context
    tonic_pc: int = 0
    scale_degrees_rel: Optional[List[int]] = None   # relative-to-tonic [0..11]
    chord_pcs_abs: Optional[List[int]] = None       # absolute pcs [0..11]

    # display policy
    layout_mode: LayoutMode = "chromatic"
    hide_out_of_key: bool = False
    degree_style: DegreeStyle = "names"
    spelling: SpellingPref = "auto"

    # internal
    cells: List[List[PushCell]] = field(init=False)

    def __post_init__(self) -> None:
        self.rebuild()

    # ----- public toggles -----
    def set_key(self, tonic_pc: int, scale_degrees_rel: Optional[List[int]]) -> None:
        self.tonic_pc = tonic_pc % 12
        self.scale_degrees_rel = None if scale_degrees_rel is None else [d % 12 for d in scale_degrees_rel]
        self.rebuild()

    def set_chord(self, chord_pcs_abs: Optional[List[int]]) -> None:
        self.chord_pcs_abs = None if chord_pcs_abs is None else [p % 12 for p in chord_pcs_abs]
        self.rebuild()

    def set_preset(self, preset: LayoutPreset) -> None:
        self.preset = preset
        self.rebuild()

    def set_anchor(self, anchor: AnchorMode, root_pc: Optional[int] = None) -> None:
        self.anchor = anchor
        if root_pc is not None:
            self.root_pc = root_pc % 12
        self.rebuild()

    def set_display(self,
                    layout_mode: Optional[LayoutMode] = None,
                    hide_out_of_key: Optional[bool] = None,
                    degree_style: Optional[DegreeStyle] = None,
                    spelling: Optional[SpellingPref] = None) -> None:
        if layout_mode: self.layout_mode = layout_mode
        if hide_out_of_key is not None: self.hide_out_of_key = hide_out_of_key
        if degree_style: self.degree_style = degree_style
        if spelling: self.spelling = spelling
        self.rebuild()

    # ----- build & render -----
    def rebuild(self) -> None:
        anchor_pc = 0 if self.anchor == "fixed_C" else self.root_pc
        layout = Push3Layout(row_offset=_row_offset_for(self.preset), root_pc=anchor_pc)
        rel_set = None if self.scale_degrees_rel is None else set(self.scale_degrees_rel)
        chord_set = None if self.chord_pcs_abs is None else set(self.chord_pcs_abs)
        self.cells = []
        for r, row in enumerate(layout.grid()):
            line: List[PushCell] = []
            for c, pc in enumerate(row):
                line.append(PushCell(
                    row=r, col=c, pc=pc,
                    tonic_pc=self.tonic_pc,
                    scale_degrees_rel=rel_set,
                    chord_pcs_abs=chord_set,
                    degree_style=self.degree_style,
                    spelling=self.spelling,
                    layout_mode=self.layout_mode,
                    hide_out_of_key=self.hide_out_of_key,
                ))
            self.cells.append(line)

    def render_lines(self) -> List[str]:
        return [" ".join(cell.render() for cell in row) for row in self.cells]

    # convenience: compute chord/scale masks if needed elsewhere
    @staticmethod
    def chord_mask_from(root_pc: int, intervals: List[int]) -> int:
        pcs = [((root_pc + i) % 12) for i in intervals]
        return mask_from_pcs(pcs)
