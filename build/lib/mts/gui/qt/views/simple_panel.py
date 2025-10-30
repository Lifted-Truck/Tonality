"""
Simple Qt widgets for poking at the Tonality workspace.

This module keeps the initial GUI deliberately minimal so we can smoke-test the
controller handshake and listener plumbing.  It can be replaced with richer
widgets once the UX solidifies.
"""

from __future__ import annotations

from typing import Any

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

from ..workspace_controller import WorkspaceController

_ROOT_NAMES = [
    ("C", 0),
    ("C#", 1),
    ("D", 2),
    ("Eb", 3),
    ("E", 4),
    ("F", 5),
    ("F#", 6),
    ("G", 7),
    ("Ab", 8),
    ("A", 9),
    ("Bb", 10),
    ("B", 11),
]


class SimpleWorkspacePanel(QWidget):
    """Minimal interactive front-end for the workspace."""

    def __init__(self, controller: WorkspaceController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
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
        scale_layout.addLayout(scale_select_layout)

        self.scale_summary = QLabel("No scale selected.")
        self.scale_summary.setWordWrap(True)
        scale_layout.addWidget(self.scale_summary)
        layout.addWidget(self.scale_group)

        self.chord_group = QGroupBox("Chord (rooted on selected pitch class)")
        chord_layout = QVBoxLayout(self.chord_group)
        chord_select_layout = QHBoxLayout()
        self.chord_root_combo = QComboBox()
        for label, _ in _ROOT_NAMES:
            self.chord_root_combo.addItem(label)
        self.chord_quality_combo = QComboBox()
        self.chord_quality_combo.addItem("Select quality…", userData=None)
        for name in self._controller.available_chord_qualities():
            self.chord_quality_combo.addItem(name, userData=name)
        chord_select_layout.addWidget(self.chord_root_combo)
        chord_select_layout.addWidget(self.chord_quality_combo)
        chord_layout.addLayout(chord_select_layout)

        self.chord_summary = QLabel("No chord selected.")
        self.chord_summary.setWordWrap(True)
        chord_layout.addWidget(self.chord_summary)
        layout.addWidget(self.chord_group)

        self.context_label = QLabel("Context: scope=abstract")
        self.context_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.context_label.setWordWrap(True)
        layout.addWidget(self.context_label)
        layout.addStretch(1)

    def _connect_signals(self) -> None:
        self.scale_combo.currentIndexChanged.connect(self._on_scale_index_changed)
        self.chord_quality_combo.currentIndexChanged.connect(self._on_chord_index_changed)

        self._controller.scale_changed.connect(self._on_scale_summary_changed)
        self._controller.chord_changed.connect(self._on_chord_summary_changed)
        self._controller.context_changed.connect(self._on_context_changed)

    # --- Event handlers ---------------------------------------------------

    def _on_scale_index_changed(self, index: int) -> None:
        name = self.scale_combo.itemData(index)
        if name:
            self._controller.set_scale_by_name(str(name))

    def _on_chord_index_changed(self, index: int) -> None:
        quality = self.chord_quality_combo.itemData(index)
        if not quality:
            return
        root_idx = self.chord_root_combo.currentIndex()
        _, root_pc = _ROOT_NAMES[root_idx % len(_ROOT_NAMES)]
        self._controller.set_chord(root_pc, str(quality))

    def _on_scale_summary_changed(self, summary: Any) -> None:
        if not summary:
            self.scale_summary.setText("No scale selected.")
            return
        text = (
            f"{summary.name} · degrees {list(summary.degrees)}\n"
            f"Cardinality: {summary.cardinality}   "
            f"Pattern: {list(summary.step_pattern)}"
        )
        if summary.note_names:
            text += f"\nNotes: {', '.join(summary.note_names)}"
        self.scale_summary.setText(text)

    def _on_chord_summary_changed(self, summary: Any) -> None:
        if not summary:
            self.chord_summary.setText("No chord selected.")
            return
        brief = summary.brief or {}
        intervals_text = ", ".join(str(iv) for iv in summary.intervals) or "n/a"
        lines = [f"{summary.name} · intervals [{intervals_text}]"]
        if brief:
            if fingerprint := brief.get("interval_fingerprint"):
                lines.append(f"Fingerprint: {fingerprint}")
            if scales := brief.get("compatible_scales"):
                lines.append(f"Fits: {', '.join(scales)}")
        self.chord_summary.setText("\n".join(lines))

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


__all__ = ["SimpleWorkspacePanel"]
