"""RE-1 packaging: an *installed* copy of the library must work.

The foundational failure this guards against: catalogs/priors lived at the repo
root, so any installed copy (wheel, pip -e from elsewhere, vendored tree) raised
FileNotFoundError on every catalog load — which every MCP tool depends on. Data
now ships inside the package (mts/data/) and pyproject declares it as package
data; these tests pin both halves.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# tomllib is stdlib only on 3.11+; this file parses pyproject to check package
# data. On the 3.10 floor it isn't present (and tomli isn't a dependency), so
# skip just this module there — the rest of the suite still validates 3.10, and
# 3.11+ CI covers the packaging assertions.
if sys.version_info < (3, 11):
    pytest.skip("test_packaging needs tomllib (Python 3.11+)", allow_module_level=True)
import tomllib

import mts
from mts.io.loaders import DATA_DIR

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_data_dir_is_inside_the_package():
    package_dir = Path(mts.__file__).resolve().parent
    assert DATA_DIR == package_dir / "data"
    assert sorted(DATA_DIR.glob("*.json")), "no catalogs found inside the package"


def test_pyproject_declares_package_data_and_entry_points():
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    assert config["tool"]["setuptools"]["package-data"]["mts"] == [
        "data/*.json", "data/rulesets/*.json", "data/patterns/*.json"
    ]
    scripts = config["project"]["scripts"]
    assert scripts["tonality-mcp"] == "mts.mcp.server:main"
    assert scripts["tonality-bridge"] == "mts.mcp.bridge:main"
    # the previously-false license claim stays absent until a LICENSE file lands
    assert not any("License ::" in c for c in config["project"].get("classifiers", []))
    assert "example.com" not in config["project"]["urls"]["Homepage"]


def test_installed_copy_loads_catalogs_without_the_repo(tmp_path):
    """Copy the package tree alone (no repo root) and exercise a catalog-backed
    tool from there — the exact scenario that used to FileNotFoundError."""
    site = tmp_path / "site-packages"
    site.mkdir()
    shutil.copytree(
        Path(mts.__file__).resolve().parent,
        site / "mts",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    probe = (
        "import json, sys\n"
        "from mts.io.loaders import load_scales, load_chord_qualities\n"
        "from mts.mcp.tools import set_class_info\n"
        "assert 'Major' in load_scales()\n"
        "assert 'maj7' in load_chord_qualities()\n"
        "print(json.dumps(set_class_info(pcs=[0, 4, 7])['prime_form']))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        cwd=tmp_path,  # not the repo
        env={"PYTHONPATH": str(site), "PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0, f"installed-copy probe failed:\n{result.stderr}"
    assert json.loads(result.stdout) == [0, 3, 7]  # 037 — prime form of the triad
