"""Emit the versioned-data export bundle (Phase 8).

Writes three artifacts for native-port consumers (the Decision-10 consumer-port
corollary; TERRANE):

- ``set_class_table.json`` — the precomputed set-class / DFT combinatorics table.
- ``manifest.json`` — the thin **index**: every versioned prior/catalog named with
  its version string(s), the code-resident policies to cite, the table schema.
- ``bundle.json`` — the **self-contained** sibling: the manifest plus each
  ``data/*.json`` asset's embedded parsed content and a sha256 integrity hash, so
  a port can consume the actual priors/catalogs without the repo.

The engine is the source of truth and the golden conformance harness is the parity
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

from mts.io.export import (
    EXPORT_SCHEMA_VERSION,
    set_class_table,
    versioned_data_bundle,
    versioned_data_manifest,
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out", type=Path, default=Path("export_artifacts"),
        help="output directory (created if absent)",
    )
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    manifest = versioned_data_manifest()
    bundle = versioned_data_bundle()
    table = set_class_table()

    (args.out / "manifest.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.out / "bundle.json").write_text(
        json.dumps(bundle, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.out / "set_class_table.json").write_text(
        json.dumps(table, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(f"export schema {EXPORT_SCHEMA_VERSION}: wrote manifest.json + "
          f"bundle.json (embedded content + sha256) + "
          f"set_class_table.json ({len(table)} masks) to {args.out}/")


if __name__ == "__main__":
    main()
