"""
Qt application bootstrap for Tonality.

The module intentionally keeps UI minimal for now; it simply wires up the
`WorkspaceController` and shows a placeholder window so further widgets can be
layered on incrementally.
"""

from __future__ import annotations

import sys
from typing import Sequence

try:  # pragma: no cover - import guard
    from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QWidget, QVBoxLayout  # type: ignore
except ImportError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "Tonality's Qt app requires PySide6. Install the 'tonality[qt]' extra "
        "when the dependency group is defined."
    ) from exc

from .workspace_controller import WorkspaceController


class PlaceholderWindow(QMainWindow):
    """Temporary window that proves the event loop wiring."""

    def __init__(self, controller: WorkspaceController) -> None:
        super().__init__()
        self._controller = controller
        self.setWindowTitle("Tonality Qt (scaffold)")
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("Tonality Qt GUI scaffolding is active."))
        layout.addWidget(QLabel("Implement real widgets in mts/gui/qt/views/ soon."))
        self.setCentralWidget(central)


def main(argv: Sequence[str] | None = None) -> int:
    """Launch the Qt application."""

    app = QApplication(list(argv) if argv is not None else sys.argv)
    controller = WorkspaceController()
    window = PlaceholderWindow(controller)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
