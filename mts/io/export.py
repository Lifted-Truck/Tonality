"""Versioned-data export (Phase 8 / Decision-10 consumer-port corollary).

A native-port consumer (TERRANE — a VST3/AU plugin that ships neither CPython nor
a sidecar) reimplements a small subset of the engine, bounded by two contracts:
it computes the **same answers from the same versioned data, citing the same
version strings**, and **parity is checked against the golden conformance harness**.

This module packages the *data* such a port consumes — it is **not** a parallel
implementation. Three pieces:

- :func:`set_class_table` — the engine's table-driven set-class / DFT combinatorics
  precomputed for all 4096 pc-set masks, so a port can consume them as pure data
  instead of reimplementing the mask-space math. Each entry mirrors the
  ``set_class_info`` MCP tool's (conformance-pinned) shape, keyed by mask.
- :func:`versioned_data_manifest` — a stable-schema **index** of every versioned
  prior / catalog (file → version strings) plus the table's schema, so a consumer
  has a single document naming all the versioned data it must pin. It stays a thin
  *naming* document (no embedded content) so it remains small and cheap to read.
- :func:`versioned_data_bundle` — the **self-contained** sibling: it re-uses the
  manifest's index and additionally **embeds each ``data/*.json`` asset's parsed
  JSON content** plus a per-asset **sha256** of the file bytes, so a native port
  can consume the actual priors/catalogs **without the repo**. It also surfaces the
  non-data, code-resident policies a port must cite — currently the ``doubling.1``
  voice-leading cardinality policy (a documented algorithm, not a JSON asset).

Embedding lives in the *bundle*, not the manifest, on purpose: the manifest answers
"what versions must I pin?" (tiny, always cheap); the bundle answers "give me the
data so I can run without the repo" (large, fetched once). The manifest is a strict
subset of the bundle, so a consumer never has to reconcile two version listings.

The engine remains the source of truth; the golden conformance harness remains the
parity oracle. Regenerate after any change to the underlying combinatorics or priors.
"""

from __future__ import annotations

import dataclasses
import hashlib
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
    "rotational_period",
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
    from ..core.symmetry import rotational_period

    table: list[dict[str, Any]] = []
    for mask in range(4096):
        entry = dataclasses.asdict(set_class_data(mask))
        entry["mask"] = mask
        entry["cardinality"] = bin(mask).count("1")
        entry["interval_vector"] = list(interval_vector_from_mask(mask))
        entry["rotational_period"] = rotational_period(mask)
        table.append({field: entry[field] for field in SET_CLASS_TABLE_FIELDS})
    return table


def _asset_versions(data: Any) -> list[str] | None:
    """Version string(s) declared by a parsed ``data/*.json`` asset, or ``None``.

    A versioned prior is a list whose entries carry a ``"version"`` field; an
    unversioned catalog (or any non-list payload) reports ``None``.
    """

    if isinstance(data, list):
        return [
            e["version"] for e in data if isinstance(e, dict) and "version" in e
        ] or None
    return None


def _data_asset_index() -> dict[str, dict[str, Any]]:
    """Per-file ``{name: {"versions": ...}}`` over ``data/*.json`` (sorted)."""

    from .loaders import DATA_DIR

    assets: dict[str, dict[str, Any]] = {}
    for path in sorted(DATA_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        assets[path.name] = {"versions": _asset_versions(data)}
    return assets


def voice_leading_policies() -> list[dict[str, Any]]:
    """Code-resident policies a native port must cite, exported as data.

    The voice-leading cardinality convention is a **named choice, not a fact**
    (ROADMAP Phase 3.5): it lives as a code constant + documented algorithm in
    ``mts/analysis/voice_leading.py``, never as a ``data/*.json`` asset. A port
    reimplements the algorithm but must cite the same policy id so downstream
    numbers stay reproducible — so the export surfaces the id + a short
    description here. This exposes identity only; it does not change behaviour.
    """

    from ..analysis.voice_leading import POLICY_DOUBLING_V1

    return [
        {
            "id": POLICY_DOUBLING_V1,
            "kind": "voice_leading_cardinality",
            "description": (
                "Unequal-cardinality pairing for minimal voice leading: every "
                "pitch class of both sets must participate, so pcs of the smaller "
                "set may carry several voices (a triad moving to a seventh chord "
                "with one tone splitting). Cited in voice-leading results so "
                "downstream numbers stay reproducible across engine upgrades."
            ),
        },
    ]


def versioned_data_manifest() -> dict[str, Any]:
    """A stable-schema index of the engine's versioned data assets.

    For each ``data/*.json`` prior/catalog, records the version string(s) it
    declares (``None`` for an unversioned catalog). Plus the set-class-table
    schema and the code-resident policies a port must cite. The single document a
    native port reads to know exactly which versioned data — and which version
    strings — it must pin and cite. Names the data; does **not** embed content
    (use :func:`versioned_data_bundle` for the self-contained payload).
    """

    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "description": (
            "Versioned-data export for native-port consumers (Decision-10 "
            "consumer-port corollary). The golden conformance harness is the parity "
            "oracle; this names the versioned data a port must pin + cite."
        ),
        "data_assets": _data_asset_index(),
        "policies": voice_leading_policies(),
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


def versioned_data_bundle() -> dict[str, Any]:
    """Self-contained export: the manifest **plus** embedded asset content + hashes.

    A native port can consume this single document **without the repo**. For each
    ``data/*.json`` prior/catalog it carries, alongside the manifest's version
    listing, the asset's **parsed JSON content** and a **sha256** of the exact
    file bytes (integrity check / change detector). The top-level manifest fields
    (``schema_version``, ``data_assets`` version index, ``policies``,
    ``set_class_table`` schema) are re-used verbatim, so the bundle is a strict
    superset — a consumer never reconciles two version listings.

    The bundle deliberately does *not* inline the 4096-row ``set_class_table``
    (1.4M); the table is emitted as its own artifact. Deterministic.
    """

    from .loaders import DATA_DIR

    bundle = versioned_data_manifest()
    bundle["bundle_note"] = (
        "Self-contained: each data_assets entry embeds parsed 'content' and a "
        "'sha256' over the raw file bytes. set_class_table is emitted separately."
    )
    for path in sorted(DATA_DIR.glob("*.json")):
        raw = path.read_bytes()
        entry = bundle["data_assets"][path.name]
        entry["sha256"] = hashlib.sha256(raw).hexdigest()
        entry["content"] = json.loads(raw)
    return bundle


__all__ = [
    "EXPORT_SCHEMA_VERSION",
    "SET_CLASS_TABLE_FIELDS",
    "set_class_table",
    "versioned_data_manifest",
    "versioned_data_bundle",
    "voice_leading_policies",
]
