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


def _canonical_sha256(obj: object) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# The fingerprint hashes ONLY the exactly-reproducible fields of the set-class
# table — those whose entire derivation is integer / bit arithmetic, and are
# therefore bit-identical on every conforming platform. The table's FLOAT fields
# (DFT magnitudes/phases, the chirality family, and reflection_residual — a
# golden-section minimizer) are transcendental / iterative and agree across
# platforms only to ~ULP..1e-9, so an EXACT hash of them is inherently
# machine-specific: rounding is not robustly safe (a value can always straddle a
# boundary — CI proved a 1e-10 round still drifted macOS↔Linux). Those are the
# wrong thing to exact-hash; they are tolerance-compared by the conformance
# harness (1e-9) and by the port's own parity harness (PORT.md). The pin's job is
# the FROZEN COMBINATORICS, which is exactly this integer surface.
_FINGERPRINT_TABLE_FIELDS = (
    "mask",
    "cardinality",
    "normal_order",
    "prime_form",
    "prime_form_mask",
    "interval_vector",
    "z_partner_prime_form",
    "complement_prime_form",
    "rotational_period",
)


def _fingerprint_table() -> list[dict[str, object]]:
    """The exactly-reproducible (integer-only) projection of the set-class table."""
    from mts.io.export import set_class_table

    return [
        {field: row[field] for field in _FINGERPRINT_TABLE_FIELDS}
        for row in set_class_table()
    ]


def ported_surface_fingerprint() -> dict[str, object]:
    """The live engine's fingerprint of everything the port slice vendors."""
    from mts.io.export import EXPORT_SCHEMA_VERSION, SET_CLASS_TABLE_FIELDS

    conformance = json.loads(CONFORMANCE_PATH.read_text())
    ported_cases = [
        case
        for case in conformance["cases"]
        if case["tool"] in PORTED_CONFORMANCE_TOOLS
    ]
    return {
        "surface": "port.slice-1b",  # slice 1 + the chirality/DFT-phase family (export.2)
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        # The full export the port vendors (documentation of the surface)...
        "set_class_table_fields": list(SET_CLASS_TABLE_FIELDS),
        # ...but the exact hash covers only the platform-deterministic integer
        # fields; the float fields ride the tolerance harness (see above).
        "set_class_table_sha256_fields": list(_FINGERPRINT_TABLE_FIELDS),
        "set_class_table_sha256": _canonical_sha256(_fingerprint_table()),
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
