# Tonality Qt GUI Scaffold

This package contains the first-pass scaffolding for a Qt-based interface.

## Current status

- `app.py` launches a minimal interactive main window that embeds
  `SimpleWorkspacePanel`.
- `workspace_controller.py` wraps the shared `Workspace` object, listens for
  change notifications, and emits Qt signals.
- `presenters.py` provides GUI-agnostic dataclasses for summarising analysis
  output. These can also back a future web front-end.
- `audio.py` defines a pluggable audio backend interface with a null
  implementation and a Qt Multimedia stub.

## Next steps

1. Expand the views under `mts/gui/qt/views/` with richer widgets (Push grid,
   timeline browsers, etc.).
2. Flesh out `QtMultimediaAudioBackend` once playback requirements are clear and
   introduce tests for the audio interface.
3. Wire controller signals into a status bar / logging pane so background
   updates (e.g., CLI session loads) are visible.
4. Extract shared grid-rendering helpers from `mts/cli/push.py` so the Qt panel
   can reuse them without duplicating logic.
