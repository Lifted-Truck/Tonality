"""The local HTTP bridge (gap 9): same surface as the MCP tools, over loopback HTTP."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from mts.mcp.bridge import describe_tool, make_server
from mts.mcp.tools import TOOLS, chord_analysis


@pytest.fixture(scope="module")
def base_url():
    server = make_server(port=0)  # OS-assigned free port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    yield f"http://{host}:{port}"
    server.shutdown()


def _request(url: str, payload: dict | list | None = None, method: str | None = None):
    """Returns (status, headers, parsed_body); never raises on HTTP error codes."""
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, response.headers, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as error:
        return error.code, error.headers, json.loads(error.read())


# --- discovery -----------------------------------------------------------------------


def test_index_reports_service_and_tool_count(base_url):
    status, _, body = _request(f"{base_url}/")
    assert status == 200
    assert body["service"] == "tonality-http-bridge"
    assert body["tools"] == len(TOOLS)


def test_tools_lists_every_tool(base_url):
    status, _, body = _request(f"{base_url}/tools")
    assert status == 200
    assert {tool["name"] for tool in body} == {fn.__name__ for fn in TOOLS}
    for tool in body:
        assert tool["doc"]  # every tool documents itself to blind clients


def test_single_tool_descriptor_marks_required_params(base_url):
    status, _, body = _request(f"{base_url}/tools/chord_analysis")
    assert status == 200
    params = {p["name"]: p for p in body["params"]}
    assert params["root"]["required"] is True
    assert params["quality"]["required"] is True
    assert params["include_inversions"]["required"] is False
    assert params["include_inversions"]["default"] is True


def test_describe_tool_matches_signature():
    descriptor = describe_tool(chord_analysis)
    assert descriptor["name"] == "chord_analysis"
    assert [p["name"] for p in descriptor["params"]] == [
        "root", "quality", "tonic", "include_inversions", "include_set_class",
    ]


# --- invocation ----------------------------------------------------------------------


def test_call_returns_tool_result(base_url):
    status, _, body = _request(
        f"{base_url}/call/set_class_info", payload={"pcs": [0, 4, 7]}
    )
    assert status == 200
    assert body["ok"] is True
    assert body["result"]["mask"] == 0b000010010001  # C-E-G


def test_call_with_note_names_and_catalog_quality(base_url):
    status, _, body = _request(
        f"{base_url}/call/chord_analysis", payload={"root": "C", "quality": "maj7"}
    )
    assert status == 200
    assert body["ok"] is True
    assert isinstance(body["result"], dict)


def test_call_with_no_body_uses_defaults(base_url):
    status, _, body = _request(f"{base_url}/call/list_scales", method="POST")
    assert status == 200
    assert body["ok"] is True
    assert any(scale["name"] == "Ionian" for scale in body["result"])


# --- error contract ------------------------------------------------------------------


def test_engine_value_error_maps_to_400_with_message(base_url):
    status, _, body = _request(
        f"{base_url}/call/chord_analysis", payload={"root": "C", "quality": "nonsense"}
    )
    assert status == 400
    assert body["ok"] is False
    assert body["error_type"] == "ValueError"
    assert "list_chord_qualities" in body["error"]  # actionable, per the tools contract


def test_missing_required_argument_maps_to_400(base_url):
    status, _, body = _request(f"{base_url}/call/chord_analysis", payload={"root": "C"})
    assert status == 400
    assert body["error_type"] == "TypeError"


def test_unknown_tool_is_404_with_discovery_hint(base_url):
    status, _, body = _request(f"{base_url}/call/not_a_tool", payload={})
    assert status == 404
    assert "/tools" in body["error"]


def test_unknown_path_is_404(base_url):
    status, _, body = _request(f"{base_url}/nope")
    assert status == 404
    assert body["ok"] is False


def test_invalid_json_body_is_400(base_url):
    request = urllib.request.Request(
        f"{base_url}/call/list_scales", data=b"{not json", method="POST"
    )
    try:
        urllib.request.urlopen(request)
        raise AssertionError("expected HTTP 400")
    except urllib.error.HTTPError as error:
        assert error.code == 400
        assert json.loads(error.read())["error_type"] == "JSONDecodeError"


def test_non_object_json_body_is_400(base_url):
    status, _, body = _request(f"{base_url}/call/list_scales", payload=[1, 2, 3])
    assert status == 400
    assert "JSON object" in body["error"]


# --- browser usability ---------------------------------------------------------------


def test_cors_header_on_responses(base_url):
    _, headers, _ = _request(f"{base_url}/tools")
    assert headers["Access-Control-Allow-Origin"] == "*"


def test_options_preflight(base_url):
    status, headers, _ = _request(f"{base_url}/call/list_scales", method="OPTIONS")
    assert status == 204
    assert "POST" in headers["Access-Control-Allow-Methods"]
    assert headers["Access-Control-Allow-Headers"] == "Content-Type"
