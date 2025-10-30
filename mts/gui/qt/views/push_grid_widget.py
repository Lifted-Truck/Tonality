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

from ...layouts.push_grid import PushGrid, PushCell
from ..presenters import ScaleSummary, ChordSummary
from ...core.enharmonics import name_for_pc, pc_from_name
from ...analysis import parse_pitch_token


_GRID_ROWS = 8
_GRID_COLS = 8


class PushGridWidget(QWidget):
    """Minimal grid renderer highlighting the active chord."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._grid = PushGrid(
            preset="fourths",
            anchor="fixed_root",
            origin="upper",
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

        self._tonic_pc = 0
        self._scale_degrees: Optional[Sequence[int]] = None
        self._refresh()

    # --- Public API -------------------------------------------------------

    def set_scale(self, summary: ScaleSummary | None) -> None:
        if summary:
            tonic = self._resolve_tonic(summary)
            if tonic is not None:
                self._tonic_pc = tonic
            self._scale_degrees = tuple(summary.degrees)
        else:
            self._scale_degrees = None
        degrees_list = list(self._scale_degrees) if self._scale_degrees else None
        self._grid.set_key(self._tonic_pc, degrees_list)
        self._refresh()

    def set_chord(self, summary: ChordSummary | None) -> None:
        if summary is None:
            self._grid.set_chord(None, chord_root_pc=None)
            self._grid.set_anchor("fixed_root", root_pc=self._tonic_pc)
            degrees_list = list(self._scale_degrees) if self._scale_degrees else None
            self._grid.set_key(self._tonic_pc, degrees_list)
            self._refresh()
            return

        root_pc = summary.root_pc if summary.root_pc is not None else self._tonic_pc
        chord_pcs = [((root_pc + interval) % 12) for interval in summary.intervals]
        self._grid.set_anchor("fixed_root", root_pc=root_pc)
        self._grid.set_chord(chord_pcs, chord_root_pc=root_pc)
        if self._scale_degrees is None:
            self._tonic_pc = root_pc
        degrees_list = list(self._scale_degrees) if self._scale_degrees else None
        self._grid.set_key(self._tonic_pc, degrees_list)
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
        token = name_for_pc(cell.pc, prefer=self._grid.spelling)
        if cell.is_tonic and cell.in_chord:
            return f"{token}*"
        if cell.is_tonic:
            return f"{token}°"
        if cell.in_chord:
            return f"{token}*"
        if not cell.in_key:
            return token.lower()
        return token

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


__all__ = ["PushGridWidget"]
