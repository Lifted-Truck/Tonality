"""Render the software bill of materials from the hash-pinned locks.

    ~/Documents/Tonality/.venv/bin/python3.13 scripts/sbom.py   # rewrite it
    ~/Documents/Tonality/.venv/bin/python3.13 scripts/sbom.py --check

The SBOM (CycloneDX 1.5 JSON, `docs/security/sbom.cdx.json`) is DERIVED from
`requirements/*.lock`, never edited by hand, and `tests/test_supply_chain.py`
fails when it drifts from them -- so a dependency bump that skips this script
cannot merge. Deterministic on purpose: no timestamp, no random serialNumber,
components sorted. A wall-clock field would make every regeneration a diff and
the drift gate meaningless.

Stdlib only (the gate runs in the dev suite on Python 3.10 and 3.13): the lock
format parsed here is the narrow one `uv pip compile --generate-hashes` writes,
one `name==version [; marker]` line followed by `--hash=sha256:` lines.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCKS = {
    # lock file -> what it locks, and the CycloneDX scope that follows from it
    "ci.lock": "the dev/CI environment (`.[dev]`)",
    "server.lock": "the MCP server (`.[mcp]`)",
}
SBOM_PATH = ROOT / "docs" / "security" / "sbom.cdx.json"
RUNTIME = {"mido", "packaging"}   # what a plain `pip install mts` pulls in

_PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;\\]+)\s*(?:;\s*([^\\]+?))?\s*\\?$")
_HASH = re.compile(r"--hash=sha256:([0-9a-f]{64})")


def parse_lock(path: Path) -> list[dict]:
    """Every pinned requirement in a lock: name, version, marker, sha256s."""
    return parse_lock_text(path.read_text(encoding="utf-8"))


def parse_lock_text(text: str) -> list[dict]:
    entries: list[dict] = []
    for line in text.splitlines():
        pin = _PIN.match(line)
        if pin:
            name, version, marker = pin.groups()
            entries.append({"name": name.lower(), "version": version,
                            "marker": (marker or "").strip(), "hashes": []})
            continue
        found = _HASH.search(line)
        if found and entries:
            entries[-1]["hashes"].append(found.group(1))
    return entries


def _project_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'^version\s*=\s*"([^"]+)"', text, re.M).group(1)


def render() -> str:
    components: dict[tuple[str, str], dict] = {}
    for lock, purpose in LOCKS.items():
        for entry in parse_lock(ROOT / "requirements" / lock):
            key = (entry["name"], entry["version"])
            comp = components.setdefault(key, {
                "type": "library",
                "bom-ref": f"pkg:pypi/{entry['name']}@{entry['version']}",
                "name": entry["name"],
                "version": entry["version"],
                "purl": f"pkg:pypi/{entry['name']}@{entry['version']}",
                "scope": "required" if entry["name"] in RUNTIME else "optional",
                "hashes": [{"alg": "SHA-256", "content": h} for h in sorted(entry["hashes"])],
                "properties": [],
            })
            comp["properties"].append({"name": "tonality:lock", "value": lock})
            if entry["marker"]:
                comp["properties"].append(
                    {"name": "tonality:marker", "value": f"{lock}: {entry['marker']}"})
    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "library",
                "bom-ref": "pkg:pypi/mts",
                "name": "mts",
                "version": _project_version(),
                "description": "Tonality music-theory engine",
            },
            "properties": [
                {"name": "tonality:source", "value": f"requirements/{lock} — {purpose}"}
                for lock, purpose in LOCKS.items()
            ] + [{"name": "tonality:generator", "value": "scripts/sbom.py"}],
        },
        "components": [components[k] for k in sorted(components)],
    }
    return json.dumps(bom, indent=2, ensure_ascii=False) + "\n"


def _shown(path: Path) -> str:
    # Repo-relative when inside the repo (never print a machine-absolute path).
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def main(argv: list[str]) -> int:
    rendered = render()
    if "--check" in argv:
        current = SBOM_PATH.read_text(encoding="utf-8") if SBOM_PATH.exists() else ""
        if current != rendered:
            print(f"{_shown(SBOM_PATH)} is stale; run scripts/sbom.py")
            return 1
        print("sbom: current")
        return 0
    SBOM_PATH.write_text(rendered, encoding="utf-8")
    print(f"wrote {_shown(SBOM_PATH)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
