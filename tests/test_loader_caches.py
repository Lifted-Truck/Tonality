"""RE-5b: the function-mappings loader is cached (mtime-keyed like the others).

Correctness is the whole point of a cache change: same inputs → identical
output (and, since callers only iterate, the same shared object), distinct
args → distinct entries, and a source-file change invalidates.
"""

from __future__ import annotations

import mts.io.loaders as loaders
from mts.io.loaders import load_function_mappings


def test_repeated_default_calls_are_cached_same_object():
    a = load_function_mappings("major")
    b = load_function_mappings("major")
    assert a is b  # cache hit returns the shared list


def test_distinct_args_are_distinct_entries():
    major = load_function_mappings("major")
    minor = load_function_mappings("minor")
    borrowed = load_function_mappings("major", include_borrowed=True)
    featured = load_function_mappings("major", features=["secondary_dominants"])
    assert major is not minor
    assert major is not borrowed
    assert major is not featured
    # and the outputs actually differ where the args say they should
    assert [(m.degree_pc, m.chord_quality) for m in major] != [
        (m.degree_pc, m.chord_quality) for m in minor
    ]


def test_custom_templates_bypass_the_cache():
    from mts.theory.functions import TEMPLATES_MAJOR

    a = load_function_mappings("major", templates=TEMPLATES_MAJOR)
    b = load_function_mappings("major", templates=TEMPLATES_MAJOR)
    assert a == b  # equal content...
    assert a is not b  # ...but recomputed each time (not cached)


def test_a_source_mtime_change_invalidates(monkeypatch):
    load_function_mappings("major")  # prime the cache
    assert loaders._FUNCTION_MAPPINGS_CACHE is not None

    real_stat = loaders.Path.stat

    def bumped_stat(self, *args, **kwargs):
        result = real_stat(self, *args, **kwargs)
        if self.name in ("scales.json", "chord_qualities.json"):
            class _S:
                st_mtime_ns = result.st_mtime_ns + 1
            return _S()
        return result

    monkeypatch.setattr(loaders.Path, "stat", bumped_stat)
    fresh = load_function_mappings("major")
    # recomputed under the new mtime — equal content, not the stale object
    assert [(m.degree_pc, m.chord_quality) for m in fresh]
