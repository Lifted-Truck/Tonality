# Tonality Qt GUI Scaffold

This package contains the first-pass scaffolding for a Qt-based interface.

## Current status

- `app.py` boots a placeholder window so the event loop wiring can be tested.
- `workspace_controller.py` wraps the shared `Workspace` object and emits Qt
  signals whenever scale, chord, timeline, or context data changes.
- `presenters.py` provides GUI-agnostic dataclasses for summarising analysis
  output. These can also back a future web front-end.
- `audio.py` defines a pluggable audio backend interface with a null
  implementation and a Qt Multimedia stub.

## Next steps (before editing existing modules)

1. Finalise the optional dependency group in `pyproject.toml` (e.g.,
   `tonality[qt]`) and document installation instructions.
2. Add change-notification hooks to `Workspace` so the controller can listen for
   updates triggered outside the GUI. Check in with the coordinating thread
   before modifying `mts/workspace.py`.
3. Break out view widgets under `mts/gui/qt/views/` (scale panel, chord panel,
   Push grid) that subscribe to the controller signals.
4. Flesh out `QtMultimediaAudioBackend` once playback requirements are clear.
