"""The port-thread accountability hook (see port/PORT.md).

The C++ port (tonality-core) vendors fixtures generated from this engine.
``port/pin.json`` is the committed fingerprint of that ported surface — the
set-class table (contents + field list + schema version) and the conformance
cases the port reproduces. This test fails whenever the live engine no longer
matches the pin, which makes changing the ported surface *loud* instead of
silently stranding the port on stale fixtures.

If this test fails and the change is intended:

1. rerun ``.venv/bin/python3.13 scripts/update_port_pin.py``
2. commit the regenerated ``port/pin.json`` in the same PR
3. add a notice in ``integrations/tonality-core/`` so the port thread
   refreshes its vendored fixtures and re-runs its parity harness

If the change is NOT intended, you have altered frozen identity-layer
combinatorics — treat it as a regression.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.update_port_pin import PIN_PATH, ported_surface_fingerprint

PROTOCOL = (
    "The ported surface changed (the slice the C++ port vendors — see "
    "port/PORT.md). If intended: rerun scripts/update_port_pin.py, commit the "
    "new port/pin.json in this PR, and file a notice in "
    "integrations/tonality-core/. If not intended, this is a regression in "
    "frozen identity-layer combinatorics."
)


def test_pin_file_exists():
    assert PIN_PATH.exists(), "port/pin.json missing — run scripts/update_port_pin.py"


def test_ported_surface_matches_pin():
    pin = json.loads(Path(PIN_PATH).read_text())
    live = ported_surface_fingerprint()
    for key, live_value in live.items():
        assert pin.get(key) == live_value, f"{key} drifted from port/pin.json. {PROTOCOL}"
