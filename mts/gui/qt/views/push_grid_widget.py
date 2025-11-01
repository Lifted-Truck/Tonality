"""
Qt widget that renders a simple Ableton Push-style grid for the current chord.

The widget leverages the existing `PushGrid` model to determine which pads are
in-scale, part of the active chord, or the tonic/root.  Rendering uses a
straightforward grid of `QLabel`s so we can iterate quickly before investing in
custom painting.
"""

from __future__ import annotations

from typing import Optional, Sequence

try:  # pragma: no cover - import guard
    from PySide6.QtCore import Qt  # type: ignore
    from PySide6.QtGui import QColor, QPalette  # type: ignore
    from PySide6.QtWidgets import QLabel, QGridLayout, QWidget  # type: ignore
except ImportError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "PushGridWidget requires PySide6. Install the 'tonality[qt]' extra."
    ) from exc

from ....layouts.push_grid import PushGrid, PushCell
from ..presenters import ScaleSummary, ChordSummary
from ....core.enharmonics import name_for_pc, pc_from_name
from ....analysis import parse_pitch_token


_GRID_ROWS = 8
_GRID_COLS = 8
_INTERVAL_LABELS = {
    0: "P1",
    1: "m2",
    2: "M2",
    3: "m3",
    4: "M3",
    5: "P4",
    6: "TT",
    7: "P5",
    8: "m6",
    9: "M6",
    10: "m7",
    11: "M7",
}


class PushGridWidget(QWidget):
    """Minimal grid renderer highlighting the active chord."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._grid = PushGrid(
            preset="fourths",
            anchor="fixed_C",
            origin="lower",
            degree_style="names",
            spelling="auto",
        )
        self._layout = QGridLayout(self)
        self._layout.setSpacing(4)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._labels: list[list[QLabel]] = []
        for row in range(_GRID_ROWS):
            row_labels: list[QLabel] = []
            for col in range(_GRID_COLS):
                label = QLabel("--", self)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setAutoFillBackground(True)
                label.setMinimumSize(36, 28)
                palette = label.palette()
                palette.setColor(QPalette.Window, QColor("#2b2d42"))
                palette.setColor(QPalette.WindowText, QColor("#edf2f4"))
                label.setPalette(palette)
                self._layout.addWidget(label, row, col)
                row_labels.append(label)
            self._labels.append(row_labels)

        self._tonic_pc: Optional[int] = None
        self._scale_degrees: Optional[Sequence[int]] = None
        self._current_chord_root: Optional[int] = None
        self._selected_root_pc: int = 0
        self._label_mode: str = "names"  # names | degrees | intervals
        self._layout_mode: str = "chromatic"
        self._anchor_mode: str = "fixed_C"  # fixed_C | tonic | chord
        self._hide_out_of_key: bool = False
        self._current_spelling: str = "auto"
        self._refresh()

    # --- Public API -------------------------------------------------------

    def set_scale(self, summary: ScaleSummary | None) -> None:
        if summary:
            tonic = summary.tonic_pc
            if tonic is None:
                tonic = self._resolve_tonic(summary)
            if tonic is not None:
                self._tonic_pc = tonic % 12
            elif self._tonic_pc is None:
                self._tonic_pc = 0
            self._scale_degrees = tuple(summary.degrees)
        else:
            self._scale_degrees = None
            if self._anchor_mode == "fixed_C":
                self._tonic_pc = 0
            else:
                self._tonic_pc = None
        degrees_list = list(self._scale_degrees) if self._scale_degrees else None
        tonic = self._tonic_pc if self._tonic_pc is not None else 0
        self._grid.set_key(tonic, degrees_list)
        self._apply_anchor()
        self._refresh()

    def set_chord(self, summary: ChordSummary | None) -> None:
        if summary is None:
            self._grid.set_chord(None, chord_root_pc=None)
            self._current_chord_root = self._selected_root_pc
            self._apply_anchor()
            self._refresh()
            return

        root_pc = summary.root_pc if summary.root_pc is not None else (self._tonic_pc or 0)
        if summary.pcs:
            chord_pcs = [pc % 12 for pc in summary.pcs]
        else:
            chord_pcs = [((root_pc + interval) % 12) for interval in summary.intervals]
        self._selected_root_pc = root_pc % 12
        self._current_chord_root = self._selected_root_pc
        self._grid.set_chord(chord_pcs, chord_root_pc=root_pc)
        if self._scale_degrees is None:
            self._tonic_pc = root_pc % 12
        self._apply_anchor()
        self._refresh()

    def set_label_mode(self, mode: str) -> None:
        self._label_mode = mode
        if mode == "degrees":
            self._grid.set_display(degree_style="degrees")
        elif mode == "names":
            self._grid.set_display(degree_style="names")
        else:
            self._grid.set_display(degree_style="names")
        self._refresh()

    def set_layout_mode(self, mode: str, *, hide_out_of_key: bool | None = None) -> None:
        self._layout_mode = mode
        if hide_out_of_key is not None:
            self._hide_out_of_key = hide_out_of_key
        self._grid.set_display(layout_mode=mode, hide_out_of_key=self._hide_out_of_key)
        self._refresh()

    def set_anchor_mode(self, mode: str) -> None:
        self._anchor_mode = mode
        self._apply_anchor()
        self._refresh()

    def set_hide_out_of_key(self, hide: bool) -> None:
        self._hide_out_of_key = hide
        self._grid.set_display(hide_out_of_key=hide)
        self._refresh()

    def set_spelling(self, mode: str) -> None:
        self._current_spelling = mode
        self._grid.set_display(spelling=mode)
        self._refresh()

    def set_root_pc(self, pc: int | None) -> None:
        if pc is None:
            return
        pc_norm = pc % 12
        self._selected_root_pc = pc_norm
        if self._current_chord_root is None:
            self._current_chord_root = pc_norm
        self._apply_anchor()
        self._refresh()

    # --- Internal helpers -------------------------------------------------

    def _refresh(self) -> None:
        cells = self._grid.cells
        for row_idx in range(_GRID_ROWS):
            for col_idx in range(_GRID_COLS):
                label = self._labels[row_idx][col_idx]
                try:
                    cell = cells[row_idx][col_idx]
                except IndexError:
                    label.setText("--")
                    self._apply_palette(label, base=True)
                    continue
                label.setText(self._label_for_cell(cell))
                self._apply_palette(label, cell=cell)

    def _label_for_cell(self, cell: PushCell) -> str:
        mode = self._label_mode
        tonic_for_labels = self._tonic_pc if self._tonic_pc is not None else self._selected_root_pc
        if mode == "degrees" and self._scale_degrees is not None and tonic_for_labels is not None:
            label = self._degree_label(cell.pc, tonic_for_labels)
        elif mode == "intervals" and self._current_chord_root is not None:
            label = self._interval_label(cell.pc, self._current_chord_root)
        elif mode == "semitones":
            base = self._tonic_pc if self._tonic_pc is not None else self._selected_root_pc
            label = str((cell.pc - base) % 12)
        else:
            label = name_for_pc(cell.pc, prefer=self._current_spelling)

        if mode == "names" and not cell.in_key and not cell.in_chord:
            label = label.lower()

        markers = ""
        if cell.is_tonic:
            markers += "°"
        if cell.in_chord:
            markers += "*"
            if not cell.in_key:
                markers += "!"
        elif mode not in {"intervals", "semitones"} and not cell.in_key:
            label = label.lower()
        return f"{label}{markers}"

    def _apply_palette(self, label: QLabel, *, cell: PushCell | None = None, base: bool = False) -> None:
        palette = label.palette()
        if base or cell is None:
            palette.setColor(QPalette.Window, QColor("#2b2d42"))
            palette.setColor(QPalette.WindowText, QColor("#edf2f4"))
            label.setPalette(palette)
            return

        if cell.is_tonic and cell.in_chord:
            bg, fg = "#f72585", "#ffffff"
        elif cell.is_tonic:
            bg, fg = "#3a86ff", "#ffffff"
        elif cell.in_chord and cell.in_key:
            bg, fg = "#ffbe0b", "#000000"
        elif cell.in_chord:
            bg, fg = "#fb5607", "#000000"
        elif cell.in_key:
            bg, fg = "#8ecae6", "#000000"
        else:
            bg, fg = "#3a3a3a", "#cccccc"
        palette.setColor(QPalette.Window, QColor(bg))
        palette.setColor(QPalette.WindowText, QColor(fg))
        label.setPalette(palette)

    def _resolve_tonic(self, summary: ScaleSummary) -> Optional[int]:
        # Prefer explicit context tokens that look like notes.
        for token in summary.context.tokens:
            try:
                parsed = parse_pitch_token(token)
            except ValueError:
                continue
            if parsed.pc is not None:
                return parsed.pc
        # Fall back to deducing from note names if available.
        if summary.note_names:
            try:
                return pc_from_name(summary.note_names[0])
            except Exception:
                return None
        return None

    def _apply_anchor(self) -> None:
        if self._anchor_mode == "fixed_C":
            self._grid.set_anchor("fixed_C")
            return

        if self._anchor_mode == "chord":
            root = self._current_chord_root
            if root is None:
                root = self._tonic_pc
            if root is None:
                self._grid.set_anchor("fixed_C")
            else:
                self._grid.set_anchor("fixed_root", root_pc=root)
            return

        # tonic mode (fallbacks to chord root then C)
        root = self._tonic_pc
        if root is None:
            root = self._current_chord_root
        if root is None:
            self._grid.set_anchor("fixed_C")
        else:
            self._grid.set_anchor("fixed_root", root_pc=root)

    def _degree_label(self, pc: int, tonic_pc: int) -> str:
        rel = (pc - tonic_pc) % 12
        mapping = {
            0: "1",
            1: "b2",
            2: "2",
            3: "b3",
            4: "3",
            5: "4",
            6: "#4",
            7: "5",
            8: "b6",
            9: "6",
            10: "b7",
            11: "7",
        }
        return mapping.get(rel, f"pc{rel}")

    def _interval_label(self, pc: int, root_pc: int) -> str:
        rel = (pc - root_pc) % 12
        return _INTERVAL_LABELS.get(rel, f"{rel}")


__all__ = ["PushGridWidget"]
