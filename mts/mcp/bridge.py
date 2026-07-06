"""Local HTTP bridge over the pure MCP tool functions (ROADMAP gap 9).

Browsers cannot spawn the stdio MCP server, so this exposes the exact same
surface — the SDK-free functions in ``tools.TOOLS`` — over local HTTP. It is
Decision 5-compliant glue: no intelligence, no new dependencies (stdlib
``http.server`` only), no state. The tool signatures and their ``to_dict()``
shapes remain the contract; the bridge just moves JSON.

Run it with ``python -m mts.mcp.bridge`` (defaults to ``127.0.0.1:8012``).

Endpoints:

- ``GET  /``             service info (name, tool count, endpoint shapes)
- ``GET  /tools``        descriptors for every tool (name, doc, params)
- ``GET  /tools/<name>`` descriptor for one tool
- ``POST /call/<name>``  invoke a tool; body is a JSON object of keyword
  arguments. Success: ``{"ok": true, "result": ...}``. Failure: 400 with
  ``{"ok": false, "error": ..., "error_type": ...}`` for bad input — a
  ``ValueError`` from the engine, or a ``TypeError`` from *binding* the
  kwargs (unknown/missing arguments); 404 for unknown tools; 500 otherwise,
  **including a TypeError raised inside the engine** (an engine bug is not
  the client's fault — RE-4e).

CORS is wide open (``Access-Control-Allow-Origin: *``) because the server
binds loopback by default — the boundary is the host, not the origin.
Local-first: this is not a hosted endpoint and must not become one.
(RE-4e records that loopback + open CORS still lets any web page the user
visits invoke path-taking tools; the tightening mechanism — origin
allowlist vs token — is a design call A6 coordinates, on the integrations
channel. Behavior is unchanged until that call lands.)
"""

from __future__ import annotations

import argparse
import inspect
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .tools import TOOLS

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8012

_TOOL_MAP = {fn.__name__: fn for fn in TOOLS}


def describe_tool(fn) -> dict:
    """A JSON-ready descriptor of one tool: name, docstring, parameters."""
    params = []
    for name, param in inspect.signature(fn).parameters.items():
        required = param.default is inspect.Parameter.empty
        params.append(
            {
                "name": name,
                "annotation": (
                    None
                    if param.annotation is inspect.Parameter.empty
                    else str(param.annotation)
                ),
                "required": required,
                "default": None if required else param.default,
            }
        )
    return {"name": fn.__name__, "doc": inspect.getdoc(fn), "params": params}


def _service_info() -> dict:
    return {
        "service": "tonality-http-bridge",
        "tools": len(TOOLS),
        "endpoints": {
            "GET /tools": "descriptors for every tool",
            "GET /tools/<name>": "descriptor for one tool",
            "POST /call/<name>": "invoke a tool with a JSON object of kwargs",
        },
    }


class BridgeHandler(BaseHTTPRequestHandler):
    server_version = "TonalityBridge/0.1"

    def log_message(self, format, *args):  # noqa: A002 - stdlib signature
        pass  # a library-embedded local server should not spam stderr

    def _send(self, status: int, payload: dict | list) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: int, message: str, error_type: str) -> None:
        self._send(status, {"ok": False, "error": message, "error_type": error_type})

    def do_OPTIONS(self) -> None:  # CORS preflight
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/":
            self._send(200, _service_info())
        elif self.path == "/tools":
            self._send(200, [describe_tool(fn) for fn in TOOLS])
        elif self.path.startswith("/tools/"):
            name = self.path[len("/tools/") :]
            fn = _TOOL_MAP.get(name)
            if fn is None:
                self._send_error(404, f"Unknown tool {name!r}. GET /tools lists all tools.", "NotFound")
            else:
                self._send(200, describe_tool(fn))
        else:
            self._send_error(404, f"Unknown path {self.path!r}.", "NotFound")

    def do_POST(self) -> None:
        if not self.path.startswith("/call/"):
            self._send_error(404, f"Unknown path {self.path!r}. POST /call/<tool_name>.", "NotFound")
            return
        name = self.path[len("/call/") :]
        fn = _TOOL_MAP.get(name)
        if fn is None:
            self._send_error(404, f"Unknown tool {name!r}. GET /tools lists all tools.", "NotFound")
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            kwargs = json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            self._send_error(400, f"Request body is not valid JSON: {exc}", "JSONDecodeError")
            return
        if not isinstance(kwargs, dict):
            self._send_error(400, "Request body must be a JSON object of keyword arguments.", "TypeError")
            return
        # Bind the signature BEFORE calling (RE-4e): a TypeError from binding
        # is the caller's (unknown/missing kwargs → 400), but a TypeError
        # raised *inside* the engine is an engine bug and must report as 500 —
        # the old blanket `except TypeError → 400` blamed the client for both.
        try:
            inspect.signature(fn).bind(**kwargs)
        except TypeError as exc:
            self._send_error(400, f"Bad arguments for {name!r}: {exc}", "TypeError")
            return
        try:
            result = fn(**kwargs)
            self._send(200, {"ok": True, "result": result})
        except ValueError as exc:
            self._send_error(400, str(exc), type(exc).__name__)
        except Exception as exc:  # noqa: BLE001 - bridge must answer, not die
            self._send_error(500, f"{type(exc).__name__}: {exc}", type(exc).__name__)


def make_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    """Build the bridge server (not yet serving; call ``serve_forever``)."""
    server = ThreadingHTTPServer((host, port), BridgeHandler)
    server.daemon_threads = True
    return server


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Tonality local HTTP bridge (gap 9).")
    parser.add_argument("--host", default=DEFAULT_HOST, help="bind address (default: loopback)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port (default: {DEFAULT_PORT})")
    args = parser.parse_args(argv)
    server = make_server(args.host, args.port)
    host, port = server.server_address[:2]
    print(f"Tonality HTTP bridge: http://{host}:{port} ({len(TOOLS)} tools; GET /tools to discover)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
