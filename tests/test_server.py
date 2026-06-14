"""Tests for FastMCP server assembly."""

import httpx
import respx

from quickwit_mcp.config import Settings
from quickwit_mcp.server import build_server

SETTINGS = Settings(qw_base_url="http://qw.test", _env_file=None)


async def _get_health() -> httpx.Response:
    app = build_server(SETTINGS).streamable_http_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://srv") as client:
        return await client.get("/health")


@respx.mock
async def test_health_ok_when_quickwit_reachable():
    respx.get("http://qw.test/api/v1/version").mock(
        return_value=httpx.Response(200, json={"build": {"version": "v0.8.2"}})
    )
    resp = await _get_health()
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["quickwit_version"] == "v0.8.2"


@respx.mock
async def test_health_503_when_quickwit_down():
    respx.get("http://qw.test/api/v1/version").mock(side_effect=httpx.ConnectError("refused"))
    resp = await _get_health()
    assert resp.status_code == 503
    assert resp.json()["status"] == "unavailable"


async def test_host_port_from_settings():
    mcp = build_server(
        Settings(qw_base_url="http://qw.test", mcp_host="0.0.0.0", mcp_port=9001, _env_file=None)
    )
    assert mcp.settings.host == "0.0.0.0"
    assert mcp.settings.port == 9001


async def test_all_tools_registered():
    mcp = build_server(SETTINGS)
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert names == {
        "list_indexes",
        "describe_index",
        "search_logs",
        "aggregate_logs",
        "get_query_syntax_help",
    }


async def test_tools_have_descriptions_and_schemas():
    mcp = build_server(SETTINGS)
    tools = {t.name: t for t in await mcp.list_tools()}
    # search_logs should expose its params in the input schema
    props = tools["search_logs"].inputSchema["properties"]
    assert "index" in props and "query" in props and "fields" in props
    # every tool carries a docstring-derived description
    assert all(t.description for t in tools.values())
