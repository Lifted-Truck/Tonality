from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional

from .push3 import Push3Layout
from ..core.bitmask import validate_pc, mask_from_pcs
from ..core.enharmonics import name_for_pc  # <— use centralized policy

DegreeStyle = Literal["names", "degrees"]
SpellingPref = Literal["auto", "sharps", "flats"]
LayoutPreset = Literal["fourths", "thirds", "sequential"]
LayoutMode = Literal["chromatic", "in_scale"]
AnchorMode = Literal["fixed_C", "fixed_root"]
Origin = Literal["upper", "lower"]  # NEW

_BASE_DEGREE = {
    0: "1", 1: "b2", 2: "2", 3: "b3", 4: "3",
    5: "4", 6: "#4", 7: "5", 8: "b6", 9: "6",
    10: "b7", 11: "7",
}

def _degree_for_pc(pc: int, tonic_pc: int) -> str:
    rel = (pc - (tonic_pc % 12)) % 12
    return _BASE_DEGREE[rel]

def _pad2_names(s: str) -> str:
    """Pad to 2 chars for NAME labels only (C -> 'C-'), but NOT for degrees."""
    return s if len(s) >= 2 else s + "-"

def _row_offset_for(preset: LayoutPreset) -> int:
    return {"fourths": 5, "thirds": 4, "sequential": 1}[preset]

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
    key_signature: Optional[int]            # NEW: pass into naming
    layout_mode: LayoutMode                 # "chromatic" | "in_scale"
    hide_out_of_key: bool = False

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

    def render(self) -> str:
        # For 'in_scale + hide_out_of_key', we now ELIDE out-of-key pads upstream (grid level).
        # So rendering here retains fixed width for every token.
        # Label (no dash for degree-style)
        if self.degree_style == "degrees":
            token = _degree_for_pc(self.pc, self.tonic_pc)
        else:
            token = _pad2_names(name_for_pc(self.pc, prefer=self.spelling, key_signature=self.key_signature))

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
    anchor: AnchorMode = "fixed_C"
    root_pc: int = 0
    origin: Origin = "lower"                # NEW default

    # musical context
    tonic_pc: int = 0
    scale_degrees_rel: Optional[List[int]] = None
    chord_pcs_abs: Optional[List[int]] = None

    # display policy
    layout_mode: LayoutMode = "chromatic"
    hide_out_of_key: bool = False
    degree_style: DegreeStyle = "names"
    spelling: SpellingPref = "auto"
    key_signature: Optional[int] = None     # NEW

    # internal
    cells: List[List[PushCell]] = field(init=False)

    def __post_init__(self) -> None:
        self.rebuild()

    # Public toggles (unchanged signatures + a couple new)
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

    def set_origin(self, origin: Origin) -> None:
        self.origin = origin
        self.rebuild()

    def set_key_signature(self, sig: Optional[int]) -> None:
        self.key_signature = sig
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

    # ---- internal helpers for row construction ----

    def _pc_at(self, row: int, col: int, anchor_pc: int) -> int:
        """
        For fourths/thirds: standard isomorphic math.
        For sequential: continue strictly across rows so 64 positions are distinct.
        """
        if self.preset == "sequential":
            # Start at anchor; advance 1 semitone per step across the entire 8x8 surface.
            idx = row * 8 + col
            return (anchor_pc + idx) % 12
        # isomorphic rows: right = +1 semitone; up = +row_offset semitones
        return (anchor_pc + col + row * _row_offset_for(self.preset)) % 12

    def _build_row_pcs(self, row: int, anchor_pc: int) -> List[int]:
        """Return the 8 PCs for a row, honoring in-scale elision when requested."""
        # seed more than 8 so we can elide out-of-scale and still fill 8
        # 8 cols + up to 12 extras to find enough in-scale notes
        base = [self._pc_at(row, c, anchor_pc) for c in range(8)]
        if self.layout_mode == "in_scale" and self.hide_out_of_key and self.scale_degrees_rel is not None:
            relset = set(self.scale_degrees_rel)
            # extend search horizon to ensure we collect 8 in-scale
            c = 8
            while len([p for p in base if ((p - self.tonic_pc) % 12) in relset]) < 8 and c < 8 + 24:
                base.append(self._pc_at(row, c, anchor_pc))
                c += 1
            # filter to in-scale and take first 8
            filtered = [p for p in base if ((p - self.tonic_pc) % 12) in relset][:8]
            return filtered
        return base[:8]

    # ---- build & render ----
    def rebuild(self) -> None:
        anchor_pc = 0 if self.anchor == "fixed_C" else self.root_pc
        # Build row-wise pcs first (so we can elide non-scale pads)
        rows = list(range(8))
        if self.origin == "lower":
            rows = list(reversed(rows))  # bottom-first visual order

        rel_set = None if self.scale_degrees_rel is None else set(self.scale_degrees_rel)
        chord_set = None if self.chord_pcs_abs is None else set(self.chord_pcs_abs)

        self.cells = []
        for ridx, r in enumerate(rows):
            pcs_row = self._build_row_pcs(r, anchor_pc)
            line: List[PushCell] = []
            for c, pc in enumerate(pcs_row):
                line.append(PushCell(
                    row=ridx, col=c, pc=pc,
                    tonic_pc=self.tonic_pc,
                    scale_degrees_rel=rel_set,
                    chord_pcs_abs=chord_set,
                    degree_style=self.degree_style,
                    spelling=self.spelling,
                    key_signature=self.key_signature,  # NEW
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
