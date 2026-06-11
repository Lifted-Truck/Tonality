"""MCP endpoint: a thin adapter exposing the engine to AI agents (Phase 4).

Decision 5 governs this package: **the intelligence stays in the engine** —
every tool here parses agent-friendly inputs, calls one existing typed
analysis entry point, and returns its ``to_dict()``. Nothing is computed in
this layer.

- ``tools.py`` — the tool functions, pure and dependency-free (fully tested
  without the MCP SDK installed).
- ``server.py`` — wires the tools into a FastMCP stdio server. Requires the
  optional ``mcp`` dependency (``pip install mts[mcp]``); run with
  ``python -m mts.mcp``.

Stateless by default; a session-backed variant is deferred until a multi-turn
consumer exists (see ROADMAP Phase 4).
"""

from . import tools

__all__ = ["tools"]
