"""Emit the versioned-data export bundle (Phase 8).

Writes the precomputed set-class / DFT table and the versioned-data manifest for
native-port consumers (the Decision-10 consumer-port corollary; TERRANE). The
engine is the source of truth and the golden conformance harness is the parity
oracle — this packages the *data* a port consumes, not a parallel implementation.

    .venv/bin/python3.13 scripts/export_versioned_data.py --out export_artifacts/
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# TODO: remove when package is installed in editable mode.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.io.export import EXPORT_SCHEMA_VERSION, set_class_table, versioned_data_manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out", type=Path, default=Path("export_artifacts"),
        help="output directory (created if absent)",
    )
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    manifest = versioned_data_manifest()
    table = set_class_table()

    (args.out / "manifest.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.out / "set_class_table.json").write_text(
        json.dumps(table, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(f"export schema {EXPORT_SCHEMA_VERSION}: wrote manifest.json + "
          f"set_class_table.json ({len(table)} masks) to {args.out}/")


if __name__ == "__main__":
    main()
