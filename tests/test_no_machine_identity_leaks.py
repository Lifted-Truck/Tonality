"""Leak gate — no machine identity in tracked files (global doctrine).

No machine-absolute home path (``/Users/<name>/…`` on macOS, ``/home/<name>/…``
on Linux) may appear in a tracked file. On a PUBLIC repo it bakes the
maintainer's username + home layout into the world's copy, and it is not
portable to a clone or a second machine. The doctrine's fix: a ``~/``-relative
path, a repo-relative path, or an env var (with an ``expanduser``'d default).

This gate lives in ``tests/`` on purpose, so it rides every enforcement point at
once — the session Stop hook, ``scripts/ci-local.sh``, and CI — which is exactly
the per-repo ``leak_gate`` the doctrine mandates (the fleet ``governor/
leak_scan.py`` is the backstop for what a per-repo gate can't see, e.g. a private
repo name inside a public one).

Pattern only — the current username is deliberately NOT matched as a bare token:
CI runs as user ``runner``, and "runner" appears legitimately in prose, so a
bare-username check would false-positive. The absolute-path form is the real,
safe signal.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SELF = Path(__file__).name

# an absolute macOS/Linux home path carrying a named user segment
_LEAK = re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+")


def _tracked_text() -> list[tuple[str, str]]:
    listed = subprocess.run(
        ["git", "-C", str(REPO), "ls-files"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    files: list[tuple[str, str]] = []
    for rel in listed:
        if not rel or Path(rel).name == SELF:  # this file names the pattern in prose
            continue
        try:
            files.append((rel, (REPO / rel).read_text(encoding="utf-8")))
        except (UnicodeDecodeError, OSError):
            continue  # binary / unreadable — carries no text leak
    return files


def test_no_machine_absolute_home_paths_in_tracked_files():
    leaks: list[str] = []
    for rel, text in _tracked_text():
        for lineno, line in enumerate(text.splitlines(), 1):
            if _LEAK.search(line):
                leaks.append(f"{rel}:{lineno}: {line.strip()[:100]}")
    assert not leaks, (
        "Machine-identity leak in tracked file(s) — a /Users/<name>/ or "
        "/home/<name>/ absolute path bakes the maintainer's identity into this "
        "PUBLIC repo and is not portable. Use a ~/-relative path, a repo-relative "
        "path, or an env var:\n  " + "\n  ".join(leaks)
    )
