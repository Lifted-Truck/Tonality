"""Security gate: a library NAME is a stem, never a path (MCP path traversal).

Threat model is the MCP one: tool arguments are chosen by a **prompt-injected
model**, so the tool boundary is a trust boundary even on a local stdio/loopback
server. Before the guard, ``load_named_ruleset("../../../port/pin")`` reached
and parsed a file *outside* the library directory, and the validator's
total-error report echoed that file's top-level keys back to the caller — path
traversal plus content disclosure (the ~10% path-traversal class in MCP's CVE
record; see the MCP security-hardening brief, P0 item 3).

These tests pin the guard on every name→path tool and the library functions
under them. A new named-asset loader MUST route through
``io.loaders.resolve_named_asset`` and gain a case here.
"""

from __future__ import annotations

import pytest

from mts.mcp import tools
from mts.io.loaders import DATA_DIR, resolve_named_asset

# Each loader, with a traversal string crafted for its own directory depth.
_LOADERS = [
    (tools.load_named_ruleset, "ruleset"),
    (tools.load_named_pattern, "pattern"),
    (tools.load_named_cross_part_pattern, "cross-part pattern"),
]

_MALICIOUS = [
    "../../../port/pin",                 # relative escape to a real repo file
    "../../../../../../etc/passwd",      # classic
    "..",                                # bare parent
    "sub/dir",                           # separator at all
    "..\\..\\windows",                   # backslash separator
    ".hidden",                           # leading dot
    "",                                  # empty
]


@pytest.mark.parametrize("loader,_kind", _LOADERS)
@pytest.mark.parametrize("name", _MALICIOUS)
def test_named_loaders_refuse_path_like_names(loader, _kind, name):
    with pytest.raises(ValueError):
        loader(name)


@pytest.mark.parametrize("loader,_kind", _LOADERS)
def test_refusal_happens_before_any_file_is_read(loader, _kind):
    """The refusal must be a NAME rejection, not a downstream schema error —
    otherwise the file was opened and its contents leaked into the message."""
    with pytest.raises(ValueError) as exc:
        loader("../../../port/pin")
    message = str(exc.value)
    assert "names are plain library names" in message
    # the traversal target's keys must NOT appear (that was the disclosure)
    assert "export_schema_version" not in message
    assert "set_class_table_sha256" not in message


def test_legitimate_names_still_load():
    assert tools.load_named_ruleset("first-species-counterpoint")["rules"]
    assert tools.load_named_pattern("arch-contour")["elements"]
    assert tools.load_named_cross_part_pattern("prinner-two-voice")["lines"]


def test_resolve_named_asset_contains_to_directory(tmp_path):
    root = DATA_DIR / "rulesets"
    # a legitimate stem resolves inside the directory
    assert resolve_named_asset(root, "first-species-counterpoint", "ruleset").parent == root.resolve()
    # anything escaping is refused
    for bad in ("../x", "a/b", ".."):
        with pytest.raises(ValueError):
            resolve_named_asset(root, bad, "ruleset")


def test_every_named_loader_routes_through_the_guard():
    """Ratchet: a future name->path loader that skips the guard fails here."""
    import inspect
    import mts.rules.library as rules_lib
    import mts.patterns.library as patterns_lib

    for module in (rules_lib, patterns_lib):
        source = inspect.getsource(module)
        # no raw "<DIR> / f"{name}.json"" construction may remain
        assert 'f"{name}.json"' not in source, (
            f"{module.__name__} builds a path from a name without the guard — "
            "route it through io.loaders.resolve_named_asset"
        )
