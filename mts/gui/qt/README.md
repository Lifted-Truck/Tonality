# Tonality Qt GUI Scaffold

> **Demoted layer.** The project is library-first; the Qt GUI and audio backend
> are deferred and must not shape core architecture (see
> [ROADMAP.md](../../../ROADMAP.md) "Demoted / deferred" — the single source of
> truth for direction). Keep this package compiling as an example consumer of
> the typed analysis API; don't extend it without a roadmap change.

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

Any future GUI/audio work is tracked in [ROADMAP.md](../../../ROADMAP.md), not
here.
