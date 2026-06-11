"""FastMCP server wiring for the Tonality tools (stdio transport).

The SDK import is guarded: the engine never requires ``mcp``; only running
the endpoint does (``pip install mts[mcp]``, then ``python -m mts.mcp``).
"""

from __future__ import annotations

from .tools import TOOLS

_INSTRUCTIONS = """\
Tonality: exact pitch-class combinatorics for 12-TET music — the arithmetic
LLMs get wrong (interval vectors, set classes, exhaustive naming, symmetry,
key induction, voice-leading distance). Inputs accept note names ("C", "F#",
"Bb") or pitch-class ints (0-11); chords/scales use catalog names — call
list_chord_qualities / list_scales to discover them. Results are plural and
evidenced by design: ranked alternatives with scores are part of the answer,
and is_ambiguous=true means the material genuinely admits several readings —
report that honestly rather than picking one silently.\
"""


def build_server():
    """Construct the FastMCP server with every tool registered."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RuntimeError(
            "The Tonality MCP endpoint needs the optional 'mcp' dependency. "
            "Install it with: pip install 'mts[mcp]'"
        ) from exc

    server = FastMCP("tonality", instructions=_INSTRUCTIONS)
    for tool in TOOLS:
        server.add_tool(tool)
    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
