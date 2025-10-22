"""Pytest configuration for Tonality project tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SESSION_FILE = Path(__file__).resolve().parent / "_session_test.json"
os.environ["TONALITY_SESSION_FILE"] = str(SESSION_FILE)


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
