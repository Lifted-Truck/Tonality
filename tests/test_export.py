"""Versioned-data export (Phase 8): the set-class/DFT table + manifest a native
port consumes. Faithfulness to the engine is the contract — every row must match
the live combinatorics, and the manifest must cite the live prior versions.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json

from mts.analysis.pcset_math import set_class_data
from mts.analysis.voice_leading import POLICY_DOUBLING_V1
from mts.core.bitmask import interval_vector_from_mask
from mts.core.symmetry import rotational_period
from mts.io.export import (
    EXPORT_SCHEMA_VERSION,
    SET_CLASS_TABLE_FIELDS,
    set_class_table,
    versioned_data_bundle,
    versioned_data_manifest,
)
from mts.io.loaders import DATA_DIR, load_key_profiles


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
        assert row["rotational_period"] == rotational_period(mask)
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


def test_manifest_exports_voice_leading_doubling_policy():
    manifest = versioned_data_manifest()
    policies = {p["id"]: p for p in manifest["policies"]}
    # the doubling.1 cardinality policy is surfaced as data with an id + description
    assert POLICY_DOUBLING_V1 == "doubling.1"
    assert POLICY_DOUBLING_V1 in policies
    policy = policies[POLICY_DOUBLING_V1]
    assert policy["kind"] == "voice_leading_cardinality"
    assert policy["description"].strip()


def test_bundle_embeds_parsed_content_and_matching_sha256():
    bundle = versioned_data_bundle()
    assets = bundle["data_assets"]
    # bundle is a strict superset of the manifest's index (same version listings)
    manifest = versioned_data_manifest()
    for name, entry in manifest["data_assets"].items():
        assert assets[name]["versions"] == entry["versions"]
    # every data/*.json is embedded with parsed content + a sha256 of file bytes
    for path in sorted(DATA_DIR.glob("*.json")):
        entry = assets[path.name]
        raw = path.read_bytes()
        # content is the parsed JSON (not a string) and matches the file
        assert entry["content"] == json.loads(raw)
        # sha256 is present and matches a freshly-hashed file
        assert entry["sha256"] == hashlib.sha256(raw).hexdigest()
    # the policy listing rides along too
    assert any(p["id"] == POLICY_DOUBLING_V1 for p in bundle["policies"])


def test_bundle_is_deterministic_and_json_serialisable():
    a = versioned_data_bundle()
    b = versioned_data_bundle()
    assert a == b
    json.dumps(a)  # the whole bundle (embedded content included) round-trips
