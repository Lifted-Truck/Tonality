"""Example audit checks — invariant style, fenced out of the dev suite.

Run explicitly (not part of `pytest tests/`):
    pytest audit/checks

This file is a template for the audit thread (see ../AUDIT.md): assert behavioral
*invariants*, allowlist documented 12-TET limitations, and keep everything under
``audit/``. Bug findings go to GitHub issues; standing invariants that earn their
keep get promoted into ``tests/`` via a reviewed PR.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make `mts` importable from any worktree (repo root is two levels up).
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.io.loaders import load_chord_qualities, load_scales  # noqa: E402

# Accepted 12-TET footprint coincidences (NOT bugs) — see AUDIT.md §7 / ROADMAP Phase 6.
KNOWN_SCALE_EQUIVALENCES = {
    frozenset([0, 2, 4, 7, 9]): {"Major Pentatonic", "Pelog Selisir"},
}


def test_all_intervals_in_range():
    for q in load_chord_qualities().values():
        assert all(0 <= iv < 12 for iv in q.intervals), q.name
    for s in load_scales().values():
        assert all(0 <= d < 12 for d in s.degrees), s.name


def test_aliases_resolve_to_canonical_object():
    for catalog in (load_chord_qualities(), load_scales()):
        for key, obj in catalog.items():
            if key != obj.name:  # an alias key
                assert key in obj.aliases


def test_scale_footprint_collisions_are_allowlisted():
    by_footprint: dict[frozenset, set[str]] = {}
    for s in load_scales().values():
        by_footprint.setdefault(frozenset(s.degrees), set()).add(s.name)
    for footprint, names in by_footprint.items():
        if len(names) > 1:
            assert names == KNOWN_SCALE_EQUIVALENCES.get(footprint), (
                f"Unexpected scale footprint collision {sorted(footprint)}: {names}"
            )
