"""Tests for FastMCP server assembly."""

from quickwit_mcp.config import Settings
from quickwit_mcp.server import build_server

SETTINGS = Settings(qw_base_url="http://qw.test", _env_file=None)


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
