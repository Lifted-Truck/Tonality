"""Regenerate ``port/pin.json`` — the fingerprint of the ported surface.

The C++ port thread (see ``port/PORT.md``) vendors fixtures generated from this
engine. ``tests/test_port_pin.py`` compares the live engine against the committed
pin, so any PR that changes the ported surface fails the suite until the author
(1) reruns this script, (2) commits the new pin in the same PR, and (3) files a
notice in ``integrations/tonality-core/`` telling the port thread to refresh its
vendored fixtures. That test is the accountability hook between the two threads —
it rides the existing Stop-hook/pytest run, no extra machinery.

    .venv/bin/python3.13 scripts/update_port_pin.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PIN_PATH = REPO_ROOT / "port" / "pin.json"
CONFORMANCE_PATH = REPO_ROOT / "tests" / "golden" / "conformance.json"

# Tools whose conformance cases the port reproduces, slice by slice. Slice 1b
# (chirality/DFT-phase) extends this list when those fields join the export.
PORTED_CONFORMANCE_TOOLS = ("set_class_info",)


# The set-class table carries float fields (DFT magnitudes/phases, the chirality
# family) computed via cmath/golden-section. Those agree across IEEE-754 platforms
# only to the last few ULPs (~1e-15 at these magnitudes) — but the fingerprint is
# an EXACT sha256 of the JSON, so raw floats made the pin machine-specific (green
# on the machine that generated it, red on a fresh clone / CI). The rest of the
# engine compares these values with a 1e-9 tolerance; the fingerprint now matches
# that intent by rounding to 1e-10 (tighter than 1e-9, so real drift still shows)
# before hashing. `+ 0.0` collapses -0.0/0.0 so a zero-crossing can't flip a hash.
_FINGERPRINT_DECIMALS = 10


def _round_floats(obj: object) -> object:
    if isinstance(obj, float):
        return round(obj, _FINGERPRINT_DECIMALS) + 0.0
    if isinstance(obj, list):
        return [_round_floats(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _round_floats(v) for k, v in obj.items()}
    return obj


def _canonical_sha256(obj: object) -> str:
    payload = json.dumps(_round_floats(obj), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ported_surface_fingerprint() -> dict[str, object]:
    """The live engine's fingerprint of everything the port slice vendors."""
    from mts.io.export import (
        EXPORT_SCHEMA_VERSION,
        SET_CLASS_TABLE_FIELDS,
        set_class_table,
    )

    conformance = json.loads(CONFORMANCE_PATH.read_text())
    ported_cases = [
        case
        for case in conformance["cases"]
        if case["tool"] in PORTED_CONFORMANCE_TOOLS
    ]
    return {
        "surface": "port.slice-1b",  # slice 1 + the chirality/DFT-phase family (export.2)
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "set_class_table_fields": list(SET_CLASS_TABLE_FIELDS),
        "set_class_table_sha256": _canonical_sha256(set_class_table()),
        "ported_conformance_tools": list(PORTED_CONFORMANCE_TOOLS),
        "ported_conformance_cases_sha256": _canonical_sha256(ported_cases),
    }


def main() -> None:
    fingerprint = ported_surface_fingerprint()
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        commit = None
    fingerprint["pinned_at_commit"] = commit
    PIN_PATH.parent.mkdir(parents=True, exist_ok=True)
    PIN_PATH.write_text(json.dumps(fingerprint, indent=2, sort_keys=True) + "\n")
    print(f"wrote {PIN_PATH.relative_to(REPO_ROOT)}")
    for key, value in fingerprint.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
