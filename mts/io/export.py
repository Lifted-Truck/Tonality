"""Versioned-data export (Phase 8 / Decision-10 consumer-port corollary).

A native-port consumer (TERRANE — a VST3/AU plugin that ships neither CPython nor
a sidecar) reimplements a small subset of the engine, bounded by two contracts:
it computes the **same answers from the same versioned data, citing the same
version strings**, and **parity is checked against the golden conformance harness**.

This module packages the *data* such a port consumes — it is **not** a parallel
implementation. Two pieces:

- :func:`set_class_table` — the engine's table-driven set-class / DFT combinatorics
  precomputed for all 4096 pc-set masks, so a port can consume them as pure data
  instead of reimplementing the mask-space math. Each entry mirrors the
  ``set_class_info`` MCP tool's (conformance-pinned) shape, keyed by mask.
- :func:`versioned_data_manifest` — a stable-schema index of every versioned prior
  / catalog (file → version strings) plus the table's schema, so a consumer has a
  single document naming all the versioned data it must pin.

The engine remains the source of truth; the golden conformance harness remains the
parity oracle. Regenerate after any change to the underlying combinatorics or priors.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any

EXPORT_SCHEMA_VERSION = "export.1"

#: The per-mask fields of :func:`set_class_table` (documented in the manifest).
SET_CLASS_TABLE_FIELDS = (
    "mask",
    "cardinality",
    "normal_order",
    "prime_form",
    "prime_form_mask",
    "interval_vector",
    "dft_magnitudes",
    "z_partner_prime_form",
    "complement_prime_form",
    "rotational_symmetry_order",
)


def set_class_table() -> list[dict[str, Any]]:
    """Precomputed set-class / DFT data for every pc-set mask 0..4095.

    Returns a 4096-element list where **position == mask** (a direct array
    lookup for a consumer). Each entry mirrors the ``set_class_info`` tool's
    output for that mask plus the cardinality. Deterministic; the engine is the
    source of truth, so a port is faithful iff it reproduces these rows (the
    conformance harness pins one row already).
    """

    from ..analysis.pcset_math import set_class_data
    from ..core.bitmask import interval_vector_from_mask
    from ..core.symmetry import mask_symmetry_order

    table: list[dict[str, Any]] = []
    for mask in range(4096):
        entry = dataclasses.asdict(set_class_data(mask))
        entry["mask"] = mask
        entry["cardinality"] = bin(mask).count("1")
        entry["interval_vector"] = list(interval_vector_from_mask(mask))
        entry["rotational_symmetry_order"] = mask_symmetry_order(mask)
        table.append({field: entry[field] for field in SET_CLASS_TABLE_FIELDS})
    return table


def versioned_data_manifest() -> dict[str, Any]:
    """A stable-schema index of the engine's versioned data assets.

    For each ``data/*.json`` prior/catalog, records the version string(s) it
    declares (``None`` for an unversioned catalog). Plus the set-class-table
    schema. The single document a native port reads to know exactly which
    versioned data — and which version strings — it must pin and cite.
    """

    from .loaders import DATA_DIR

    assets: dict[str, Any] = {}
    for path in sorted(DATA_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        versions: list[str] | None = None
        if isinstance(data, list):
            versions = [
                e["version"] for e in data if isinstance(e, dict) and "version" in e
            ] or None
        assets[path.name] = {"versions": versions}

    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "description": (
            "Versioned-data export for native-port consumers (Decision-10 "
            "consumer-port corollary). The golden conformance harness is the parity "
            "oracle; this names the versioned data a port must pin + cite."
        ),
        "data_assets": assets,
        "set_class_table": {
            "entries": 4096,
            "index": "list position == pc-set mask (0..4095)",
            "fields": list(SET_CLASS_TABLE_FIELDS),
            "note": (
                "per-mask combinatorics precomputed; each row mirrors the "
                "set_class_info MCP tool output for that mask."
            ),
        },
    }


__all__ = [
    "EXPORT_SCHEMA_VERSION",
    "SET_CLASS_TABLE_FIELDS",
    "set_class_table",
    "versioned_data_manifest",
]
