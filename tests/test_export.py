"""Versioned-data export (Phase 8): the set-class/DFT table + manifest a native
port consumes. Faithfulness to the engine is the contract — every row must match
the live combinatorics, and the manifest must cite the live prior versions.
"""

from __future__ import annotations

import dataclasses
import json

from mts.analysis.pcset_math import set_class_data
from mts.core.bitmask import interval_vector_from_mask
from mts.core.symmetry import mask_symmetry_order
from mts.io.export import (
    EXPORT_SCHEMA_VERSION,
    SET_CLASS_TABLE_FIELDS,
    set_class_table,
    versioned_data_manifest,
)
from mts.io.loaders import load_key_profiles


def test_table_covers_all_masks_indexed_by_mask():
    table = set_class_table()
    assert len(table) == 4096
    # position == mask (a direct array lookup for a consumer)
    for mask in (0, 1, 2741, 4095):
        assert table[mask]["mask"] == mask
    assert set(table[2741]) == set(SET_CLASS_TABLE_FIELDS)


def test_rows_are_faithful_to_the_engine():
    table = set_class_table()
    # Sample across cardinalities, incl. edges (empty, single pc, full chromatic).
    for mask in (0, 1, 145, 2741, 1365, 4095):
        engine = dataclasses.asdict(set_class_data(mask))
        row = table[mask]
        assert row["prime_form"] == engine["prime_form"]
        assert row["prime_form_mask"] == engine["prime_form_mask"]
        assert row["dft_magnitudes"] == engine["dft_magnitudes"]
        assert row["z_partner_prime_form"] == engine["z_partner_prime_form"]
        assert row["complement_prime_form"] == engine["complement_prime_form"]
        assert row["interval_vector"] == list(interval_vector_from_mask(mask))
        assert row["rotational_symmetry_order"] == mask_symmetry_order(mask)
        assert row["cardinality"] == bin(mask).count("1")


def test_table_is_deterministic_and_json_serialisable():
    a = set_class_table()
    b = set_class_table()
    assert a == b
    json.dumps(a)  # the whole table round-trips to JSON


def test_manifest_cites_live_versions():
    manifest = versioned_data_manifest()
    assert manifest["schema_version"] == EXPORT_SCHEMA_VERSION == "export.1"
    assets = manifest["data_assets"]
    # the versioned priors are present with their live version strings
    assert load_key_profiles().version in assets["key_profiles.json"]["versions"]
    assert "kk-1982.1" in assets["key_profiles.json"]["versions"]
    assert "key-inertia.1" in assets["key_inertia.json"]["versions"]
    # an unversioned catalog records None, not a crash
    assert "scales.json" in assets
    # the table schema is documented
    assert manifest["set_class_table"]["entries"] == 4096
    assert manifest["set_class_table"]["fields"] == list(SET_CLASS_TABLE_FIELDS)
    json.dumps(manifest)
