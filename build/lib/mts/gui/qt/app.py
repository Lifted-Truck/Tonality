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
    from PySide6.QtWidgets import QApplication, QMainWindow  # type: ignore
except ImportError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "Tonality's Qt app requires PySide6. Install the 'tonality[qt]' extra "
        "when the dependency group is defined."
    ) from exc

from .workspace_controller import WorkspaceController
from .views.simple_panel import SimpleWorkspacePanel


class MainWindow(QMainWindow):
    """Minimal interactive window for exploring the workspace."""

    def __init__(self, controller: WorkspaceController) -> None:
        super().__init__()
        self._controller = controller
        self.setWindowTitle("Tonality Qt (preview)")
        self._panel = SimpleWorkspacePanel(controller, self)
        self.setCentralWidget(self._panel)
        self.resize(520, 480)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._controller.dispose()
        super().closeEvent(event)


def main(argv: Sequence[str] | None = None) -> int:
    """Launch the Qt application."""

    app = QApplication(list(argv) if argv is not None else sys.argv)
    controller = WorkspaceController()
    window = MainWindow(controller)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
