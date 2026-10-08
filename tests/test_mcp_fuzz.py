"""Malformed-input fuzz over every MCP tool (security slice, 2026-10-08; P0.2).

THE CONTRACT. Every tool argument is chosen by a caller this engine cannot
trust: a prompt-injected model on the stdio server, or any local process on the
HTTP bridge. For malformed-but-callable input a tool must either return a result
or raise ``ValueError`` — which every door reports as the CALLER's error (HTTP
400). Anything else is an engine defect (the bridge reports it as a 500, per
RE-4e): a stray ``TypeError``/``KeyError``/``AttributeError``, an
``OverflowError``, a hang, or unbounded memory. ``SpecificationError`` is the one
other allowed exit — the cardinal rule's deliberate refusal.

THE BASELINE. When this landed, the same 1,905 calls produced 523 defects across
65 of 79 tools, plus 11 inputs that allocated over 1.2 GB/s until killed. Root
causes and fixes: ``docs/security/BOUNDARIES.md``.

HOW. Each tool's one valid call from the conformance golden is the baseline;
each argument is replaced, one at a time, by every entry of a FIXED mutation
table — no RNG, so a failure always reproduces. Every mutation is reachable
through JSON (``json.loads`` accepts ``NaN``/``Infinity``, and ``1e999`` — a valid
JSON number — parses to infinity). Each call runs under a time bound.
"""

from __future__ import annotations

import copy
import signal

import pytest

from mts.analysis.errors import SpecificationError
from mts.mcp import tools

from test_conformance import CASES

NAN, INF = float("nan"), float("inf")
CALL_SECONDS = 5

ANY = [("None", None), ("str", "x"), ("int", 7), ("dict", {"k": 1}), ("list", [1])]
LIST = [("empty", []), ("[None]", [None]), ("[[str]]", [["x"]]), ("[[None]*3]", [[None, None, None]]),
        ("[[neg]]", [[-1, -1, -1]]), ("[[nan]]", [[NAN, 1, 60]]), ("[[inf]]", [[0, INF, 60]]),
        ("[[1e9]]", [[0, 1e9, 60]]), ("[[midi999]]", [[0, 1, 999]]), ("[[dur-1]]", [[0, -1, 60]]),
        ("[[short]]", [[0]]), ("deep", [[[[[]]]]]), ("[dict]", [{"a": 1}])]
DICT = [("empty", {}), ("unknown", {"zz": 1}), ("nested-null", {"rules": None, "name": None})]
NUM = [("neg", -1), ("huge", 10**18), ("float", 3.5), ("nan", NAN), ("inf", INF), ("-inf", -INF)]
STR = [("empty", ""), ("nul", "\x00"), ("long", "a" * 5000)]


def mutations(value):
    out = list(ANY)
    if isinstance(value, list):
        out += LIST
    elif isinstance(value, dict):
        out += DICT
    elif isinstance(value, bool):
        out += [("int2", 2)]
    elif isinstance(value, (int, float)):
        out += NUM
    elif isinstance(value, str):
        out += STR
    return out


class _Hang(Exception):
    pass


def _alarm(*_):
    raise _Hang()


def classify(fn, kwargs) -> str | None:
    """None if the call honoured the contract; else a one-line defect report."""

    previous = signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(CALL_SECONDS)
    try:
        fn(**kwargs)
        return None
    except (ValueError, SpecificationError):
        return None
    except _Hang:
        return f"no answer within {CALL_SECONDS}s"
    except Exception as exc:  # noqa: BLE001 — every other exit IS the finding
        return f"{type(exc).__name__}: {str(exc)[:80]}"
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def _cases():
    seen = set()
    for tool, kwargs in CASES:
        if tool in seen:
            continue
        seen.add(tool)
        for param, value in kwargs.items():
            for label, bad in mutations(value):
                yield tool, kwargs, param, label, bad


def test_every_tool_honours_the_malformed_input_contract():
    defects = []
    calls = 0
    for tool, kwargs, param, label, bad in _cases():
        trial = copy.deepcopy(kwargs)
        trial[param] = bad
        calls += 1
        problem = classify(getattr(tools, tool), trial)
        if problem:
            defects.append(f"{tool}.{param} <- {label}: {problem}")
    assert calls > 1500, f"the mutation sweep shrank to {calls} calls — check CASES"
    assert not defects, f"{len(defects)} contract violation(s):\n" + "\n".join(defects)


def test_the_harness_sees_a_planted_defect():
    """The must-fail control (Decision 85). A fuzz test that cannot see a
    defect passes forever while protecting nothing — so prove it sees each
    class it claims to catch."""

    def leaks_type_error(**_):
        return None + 1

    def leaks_key_error(**_):
        return {}["missing"]

    def hangs(**_):
        while True:
            pass

    assert classify(leaks_type_error, {}).startswith("TypeError")
    assert classify(leaks_key_error, {}).startswith("KeyError")
    assert "no answer" in classify(hangs, {})
    # ...and the two allowed exits are NOT reported
    assert classify(lambda **_: (_ for _ in ()).throw(ValueError("bad")), {}) is None
    assert classify(lambda **_: {"ok": True}, {}) is None
