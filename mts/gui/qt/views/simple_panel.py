"""
Simple Qt widgets for poking at the Tonality workspace.

This module keeps the initial GUI deliberately minimal so we can smoke-test the
controller handshake and listener plumbing.  It can be replaced with richer
widgets once the UX solidifies.
"""

from __future__ import annotations

from typing import Any, Optional

try:  # pragma: no cover - import guard
    from PySide6.QtCore import Qt  # type: ignore
    from PySide6.QtWidgets import (  # type: ignore
        QWidget,
        QVBoxLayout,
        QGroupBox,
        QComboBox,
        QLabel,
        QHBoxLayout,
    )
except ImportError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "SimpleWorkspacePanel requires PySide6. Install the 'tonality[qt]' extra."
    ) from exc

from ....core.enharmonics import name_for_pc
from ..workspace_controller import WorkspaceController
from .push_grid_widget import PushGridWidget

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

_KEY_SIGNATURE_BY_TONIC = {
    0: 0,
    7: 1,
    2: 2,
    9: 3,
    4: 4,
    11: 5,
    6: 6,
    5: -1,
    10: -2,
    3: -3,
    8: -4,
    1: -5,
}


class SimpleWorkspacePanel(QWidget):
    """Minimal interactive front-end for the workspace."""

    def __init__(self, controller: WorkspaceController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._display_context = controller.display_context()
        self._updating_ui = False
        self._last_scale_tonic: Optional[int] = None
        self._current_label_mode: str = "names"
        self._setup_ui()
        self._connect_signals()

    # --- Qt plumbing ------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self.scale_group = QGroupBox("Scale")
        scale_layout = QVBoxLayout(self.scale_group)
        scale_select_layout = QHBoxLayout()
        self.scale_combo = QComboBox()
        self.scale_combo.addItem("Select scale…", userData=None)
        for name in self._controller.available_scales():
            self.scale_combo.addItem(name, userData=name)
        scale_select_layout.addWidget(self.scale_combo)
        self.scale_tonic_combo = QComboBox()
        scale_select_layout.addWidget(self.scale_tonic_combo)
        scale_layout.addLayout(scale_select_layout)

        self.scale_summary = QLabel("No scale selected.")
        self.scale_summary.setWordWrap(True)
        scale_layout.addWidget(self.scale_summary)
        layout.addWidget(self.scale_group)

        self.chord_group = QGroupBox("Chord (rooted on selected pitch class)")
        chord_layout = QVBoxLayout(self.chord_group)
        chord_select_layout = QHBoxLayout()
        self.chord_root_combo = QComboBox()
        self.chord_quality_combo = QComboBox()
        self.chord_quality_combo.addItem("None", userData=None)
        for name in self._controller.available_chord_qualities():
            self.chord_quality_combo.addItem(name, userData=name)
        chord_select_layout.addWidget(self.chord_root_combo)
        chord_select_layout.addWidget(self.chord_quality_combo)
        chord_layout.addLayout(chord_select_layout)

        self.chord_summary = QLabel("No chord selected.")
        self.chord_summary.setWordWrap(True)
        chord_layout.addWidget(self.chord_summary)
        layout.addWidget(self.chord_group)

        self.push_group = QGroupBox("Push Grid Preview")
        push_layout = QVBoxLayout(self.push_group)
        controls_layout = QHBoxLayout()
        self.grid_label_combo = QComboBox()
        self.grid_label_combo.addItem("Note names", userData="names")
        self.grid_label_combo.addItem("Scale degrees", userData="degrees")
        self.grid_label_combo.addItem("Chord intervals", userData="intervals")
        self.grid_label_combo.addItem("Semitone numbers", userData="semitones")
        controls_layout.addWidget(QLabel("Labels:"))
        controls_layout.addWidget(self.grid_label_combo)

        self.grid_layout_combo = QComboBox()
        self.grid_layout_combo.addItem("Chromatic", userData=("chromatic", False))
        self.grid_layout_combo.addItem("In-scale", userData=("in_scale", True))
        controls_layout.addWidget(QLabel("Layout:"))
        controls_layout.addWidget(self.grid_layout_combo)

        self.grid_anchor_combo = QComboBox()
        self.grid_anchor_combo.addItem("Fixed C origin", userData="fixed_C")
        self.grid_anchor_combo.addItem("Tonic origin", userData="tonic")
        self.grid_anchor_combo.addItem("Chord root", userData="chord")
        controls_layout.addWidget(QLabel("Anchor:"))
        controls_layout.addWidget(self.grid_anchor_combo)
        self.grid_spelling_combo = QComboBox()
        self.grid_spelling_combo.addItem("Auto", userData="auto")
        self.grid_spelling_combo.addItem("Sharps", userData="sharps")
        self.grid_spelling_combo.addItem("Flats", userData="flats")
        controls_layout.addWidget(QLabel("Spelling:"))
        controls_layout.addWidget(self.grid_spelling_combo)
        controls_layout.addStretch(1)
        push_layout.addLayout(controls_layout)

        self.push_grid_widget = PushGridWidget()
        self.push_grid_widget.set_display_context(self._display_context)
        push_layout.addWidget(self.push_grid_widget)
        layout.addWidget(self.push_group)

        self.context_label = QLabel("Context: scope=abstract")
        self.context_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.context_label.setWordWrap(True)
        layout.addWidget(self.context_label)
        layout.addStretch(1)

    def _connect_signals(self) -> None:
        self.scale_combo.currentIndexChanged.connect(self._on_scale_index_changed)
        self.scale_tonic_combo.currentIndexChanged.connect(self._on_scale_tonic_changed)
        self.chord_root_combo.currentIndexChanged.connect(self._on_chord_root_changed)
        self.chord_quality_combo.currentIndexChanged.connect(self._on_chord_index_changed)

        self._controller.scale_changed.connect(self._on_scale_summary_changed)
        self._controller.chord_changed.connect(self._on_chord_summary_changed)
        self._controller.context_changed.connect(self._on_context_changed)
        self._controller.display_context_changed.connect(self._on_display_context_changed)

        self.grid_label_combo.currentIndexChanged.connect(self._on_grid_label_changed)
        self.grid_layout_combo.currentIndexChanged.connect(self._on_grid_layout_changed)
        self.grid_anchor_combo.currentIndexChanged.connect(self._on_grid_anchor_changed)
        self.grid_spelling_combo.currentIndexChanged.connect(self._on_grid_spelling_changed)

        # Initialize defaults
        self._refresh_scale_tonic_options()
        self.push_grid_widget.set_label_mode(self.grid_label_combo.currentData())
        layout_mode, hide = self.grid_layout_combo.currentData()
        self.push_grid_widget.set_layout_mode(layout_mode, hide_out_of_key=hide)
        self.push_grid_widget.set_anchor_mode(self.grid_anchor_combo.currentData())
        self.push_grid_widget.set_spelling(self.grid_spelling_combo.currentData())
        self._current_label_mode = self.grid_label_combo.currentData()
        self._update_chord_root_options()

    # --- Event handlers ---------------------------------------------------

    def _on_scale_index_changed(self, index: int) -> None:
        if self._updating_ui:
            return
        name = self.scale_combo.itemData(index)
        if name:
            tonic_pc = self._current_scale_tonic_pc()
            self._controller.set_scale_by_name(str(name), tonic_pc if tonic_pc is not None else -1)

    def _on_scale_tonic_changed(self, index: int) -> None:
        if self._updating_ui:
            return
        name = self.scale_combo.currentData()
        if name:
            tonic_pc = self._current_scale_tonic_pc()
            self._controller.set_scale_by_name(str(name), tonic_pc if tonic_pc is not None else -1)
        if self._current_scale_tonic_pc() is None and self.grid_label_combo.currentData() == "names":
            idx = self.grid_label_combo.findData("semitones")
            if idx != -1:
                self.grid_label_combo.setCurrentIndex(idx)
        self._update_chord_root_options()

    def _on_chord_root_changed(self, index: int) -> None:
        data = self.chord_root_combo.itemData(index)
        if data is None:
            self.push_grid_widget.set_root_pc(None)
            root_pc = self._current_scale_tonic_pc() or 0
            if self.chord_quality_combo.currentIndex() != 0:
                self.chord_quality_combo.setCurrentIndex(0)
            self._controller.set_display_setting("chord_root_pc", None)
            return
        else:
            root_pc = int(data)
            self.push_grid_widget.set_root_pc(root_pc)
            self._controller.set_display_setting("chord_root_pc", root_pc)
        quality = self.chord_quality_combo.currentData()
        if quality:
            self._controller.set_chord(root_pc, str(quality))

    def _on_chord_index_changed(self, index: int) -> None:
        quality = self.chord_quality_combo.itemData(index)
        if not quality:
            self.push_grid_widget.set_chord(None)
            return
        root_idx = self.chord_root_combo.currentIndex()
        root_pc = self.chord_root_combo.itemData(root_idx)
        if root_pc is None:
            root_pc = 0
        else:
            self.push_grid_widget.set_root_pc(int(root_pc))
        self._controller.set_chord(root_pc, str(quality))

    def _on_scale_summary_changed(self, summary: Any) -> None:
        if not summary:
            self.scale_summary.setText("No scale selected.")
            self.push_grid_widget.set_scale(None)
            self._last_scale_tonic = None
            self._update_chord_root_options()
            return
        self._sync_scale_controls(summary)
        text = (
            f"{summary.name} · degrees {list(summary.degrees)}\n"
            f"Cardinality: {summary.cardinality}   "
            f"Pattern: {list(summary.step_pattern)}"
        )
        if summary.note_names:
            text += f"\nNotes: {', '.join(summary.note_names)}"
        self.scale_summary.setText(text)
        self.push_grid_widget.set_scale(summary)

    def _on_chord_summary_changed(self, summary: Any) -> None:
        if not summary:
            self.chord_summary.setText("No chord selected.")
            self.push_grid_widget.set_chord(None)
            return
        brief = summary.brief
        intervals_text = ", ".join(str(iv) for iv in summary.intervals) or "n/a"
        lines = [f"{summary.name} · intervals [{intervals_text}]"]
        if summary.root_pc is not None:
            tonic = self._current_scale_tonic_pc()
            if tonic is None:
                tonic = self._last_scale_tonic
            base = tonic if tonic is not None else 0
            root_name = name_for_pc(summary.root_pc)
            display_label = self._root_label_for_pc(summary.root_pc, base, tonic)
            if display_label != root_name:
                root_text = f"{root_name} ({display_label})"
            else:
                root_text = root_name
            if tonic is not None and (summary.root_pc % 12) != (tonic % 12):
                tonic_name = name_for_pc(tonic)
                root_text += f" ≠ tonic {tonic_name}"
            lines.append(f"Root: {root_text}")
        if brief:
            fingerprint = getattr(brief, "interval_fingerprint", None)
            if fingerprint:
                lines.append(f"Fingerprint: {fingerprint}")
            compatible = getattr(brief, "compatible_scales", None)
            if compatible:
                lines.append(f"Fits: {', '.join(compatible)}")
        self.chord_summary.setText("\n".join(lines))
        self.push_grid_widget.set_chord(summary)

    def _on_context_changed(self, payload: Any) -> None:
        if not payload:
            self.context_label.setText("Context: scope=abstract")
            return
        tokens = payload.get("tokens") or []
        absolute = payload.get("absolute_midi") or []
        pieces = [f"scope={payload.get('scope', 'abstract')}"]
        if tokens:
            pieces.append(f"tokens={tokens}")
        if absolute:
            pieces.append(f"absolute_midi={absolute}")
        self.context_label.setText("Context: " + ", ".join(pieces))

    def _on_grid_label_changed(self, index: int) -> None:
        mode = self.grid_label_combo.itemData(index)
        if mode:
            if mode == "names" and self._current_scale_tonic_pc() is None and self._last_scale_tonic is None:
                idx = self.grid_label_combo.findData("semitones")
                if idx != -1 and idx != index:
                    self.grid_label_combo.setCurrentIndex(idx)
                    return
            self.push_grid_widget.set_label_mode(mode)
            self._current_label_mode = mode
            self._controller.set_display_setting("label_mode", mode)
            self._update_chord_root_options()

    def _on_grid_layout_changed(self, index: int) -> None:
        data = self.grid_layout_combo.itemData(index)
        if not data:
            return
        mode, hide = data
        self.push_grid_widget.set_layout_mode(mode, hide_out_of_key=hide)

    def _on_grid_anchor_changed(self, index: int) -> None:
        mode = self.grid_anchor_combo.itemData(index)
        if mode:
            self.push_grid_widget.set_anchor_mode(mode)

    def _on_grid_spelling_changed(self, index: int) -> None:
        mode = self.grid_spelling_combo.itemData(index)
        if mode:
            self.push_grid_widget.set_spelling(mode)
            if self._current_label_mode == "names":
                self._update_chord_root_options()
            self._refresh_scale_tonic_options()
            self._controller.set_display_setting("spelling", mode)

    def _on_display_context_changed(self, payload: object) -> None:
        self.push_grid_widget.refresh_from_context()

    # --- Helpers ----------------------------------------------------------

    def _current_spelling_mode(self) -> str:
        return self.grid_spelling_combo.currentData() or "auto"

    def _current_scale_tonic_pc(self) -> int | None:
        data = self.scale_tonic_combo.currentData()
        if data is None or data == -1:
            return None
        return int(data)

    def _refresh_scale_tonic_options(self) -> None:
        current_value = self._current_scale_tonic_pc()
        prefer = self._current_spelling_mode()
        self.scale_tonic_combo.blockSignals(True)
        self.scale_tonic_combo.clear()
        self.scale_tonic_combo.addItem("Auto tonic / intervals", userData=-1)
        for pc in range(12):
            label = self._spell_pc(pc, prefer)
            self.scale_tonic_combo.addItem(label, userData=pc)
        if current_value is None:
            idx = self.scale_tonic_combo.findData(-1)
        else:
            idx = self.scale_tonic_combo.findData(current_value % 12)
            if idx == -1:
                idx = self.scale_tonic_combo.findData(-1)
        self.scale_tonic_combo.setCurrentIndex(idx if idx != -1 else 0)
        self.scale_tonic_combo.blockSignals(False)

    def _sync_scale_controls(self, summary: Any) -> None:
        name_idx = self.scale_combo.findData(summary.name)
        tonic_pc = summary.tonic_pc if summary.tonic_pc is not None else -1
        tonic_idx = self.scale_tonic_combo.findData(tonic_pc)
        if tonic_idx == -1:
            tonic_idx = 0
        self._updating_ui = True
        if name_idx != -1 and self.scale_combo.currentIndex() != name_idx:
            self.scale_combo.setCurrentIndex(name_idx)
        if self.scale_tonic_combo.currentIndex() != tonic_idx:
            self.scale_tonic_combo.setCurrentIndex(tonic_idx)
        self._updating_ui = False
        if summary.tonic_pc is not None:
            self._last_scale_tonic = summary.tonic_pc
        if summary.tonic_pc is None and self.grid_label_combo.currentData() == "names":
            idx = self.grid_label_combo.findData("semitones")
            if idx != -1:
                self.grid_label_combo.setCurrentIndex(idx)
        self._update_chord_root_options()

    def _update_chord_root_options(self) -> None:
        current_pc = self.chord_root_combo.currentData()
        tonic = self._current_scale_tonic_pc()
        base = tonic if tonic is not None else (self._last_scale_tonic if self._last_scale_tonic is not None else 0)
        prefer = self._current_spelling_mode()
        if prefer == "auto" and tonic is not None:
            prefer = "auto"
        elif prefer == "auto":
            prefer = "sharps"
        self.chord_root_combo.blockSignals(True)
        self.chord_root_combo.clear()

        self.chord_root_combo.addItem("None", userData=None)
        for pc in range(12):
            label = self._root_label_for_pc(pc, base, tonic, prefer)
            self.chord_root_combo.addItem(label, pc)

        if current_pc is None:
            idx = 0
        else:
            idx = self.chord_root_combo.findData(current_pc % 12)
            if idx == -1:
                idx = 0
        if idx == -1:
            idx = 0
        self.chord_root_combo.setCurrentIndex(idx)
        self.chord_root_combo.blockSignals(False)
        data = self.chord_root_combo.itemData(self.chord_root_combo.currentIndex())
        self.push_grid_widget.set_root_pc(int(data) if data is not None else None)

    @staticmethod
    def _degree_label(pc: int, tonic_pc: int) -> str:
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
        rel = (pc - tonic_pc) % 12
        return mapping.get(rel, f"pc{rel}")

    def _root_label_for_pc(self, pc: int, base: int, tonic: Optional[int], prefer: str | None = None) -> str:
        mode = self._current_label_mode
        if mode == "degrees":
            anchor = tonic if tonic is not None else base
            return self._degree_label(pc, anchor)
        if mode == "intervals":
            rel = (pc - base) % 12
            return _INTERVAL_LABELS.get(rel, str(rel))
        if mode == "semitones":
            rel = (pc - base) % 12
            return str(rel)
        spelling = prefer or self._current_spelling_mode()
        key_sig = None
        if spelling == "auto":
            reference = tonic if tonic is not None else pc
            key_sig = _KEY_SIGNATURE_BY_TONIC.get(reference % 12, 0)
        return name_for_pc(pc, prefer=spelling, key_signature=key_sig)

    def _spell_pc(self, pc: int, prefer: str) -> str:
        if prefer == "auto":
            key_sig = _KEY_SIGNATURE_BY_TONIC.get(pc % 12, 0)
            return name_for_pc(pc, prefer="auto", key_signature=key_sig)
        return name_for_pc(pc, prefer=prefer)


__all__ = ["SimpleWorkspacePanel"]
