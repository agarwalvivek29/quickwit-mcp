"""FastMCP server assembly.

Builds the MCP server, registers the read-only tools over a single shared
:class:`~quickwit_mcp.client.QuickwitClient`, and closes that client on shutdown
via the server lifespan.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import QuickwitClient
from .config import Settings, get_settings
from .tools import help as syntax_help
from .tools import indexes, search

_INSTRUCTIONS = (
    "Read-only access to Quickwit logs. Use `list_indexes` to discover indexes, "
    "`describe_index` to learn an index's fields before querying, `search_logs` to "
    "fetch log lines, and `aggregate_logs` for counts/trends. Call "
    "`get_query_syntax_help` if unsure about query syntax."
)


def build_server(settings: Settings | None = None) -> FastMCP:
    """Construct the FastMCP server with all tools registered.

    A single :class:`QuickwitClient` is shared across tools and closed when the
    server shuts down.
    """
    settings = settings or get_settings()
    client = QuickwitClient(settings)

    @asynccontextmanager
    async def lifespan(_server: FastMCP) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await client.aclose()

    mcp = FastMCP(
        "quickwit-mcp",
        instructions=_INSTRUCTIONS,
        lifespan=lifespan,
        host=settings.mcp_host,
        port=settings.mcp_port,
    )

    @mcp.tool()
    async def list_indexes(with_stats: bool = False) -> list[dict[str, Any]]:
        """List queryable indexes (ids + uris). with_stats adds doc count and timestamp range."""
        return await indexes.list_indexes(client, with_stats=with_stats)

    @mcp.tool()
    async def describe_index(index_id: str) -> dict[str, Any]:
        """Index stats, timestamp range, and the field schema (name -> type) for query building."""
        return await indexes.describe_index(client, index_id)

    @mcp.tool()
    async def search_logs(
        index: str,
        query: str = "*",
        start: str | int | None = None,
        end: str | int | None = None,
        max_hits: int | None = None,
        start_offset: int | None = None,
        sort_by: str | None = None,
        search_field: str | None = None,
        snippet_fields: list[str] | None = None,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Search logs. index may be a single id, comma list, or glob. start/end accept
        'now-1h', ISO-8601, or epoch seconds. Defaults to newest-first; use fields to project."""
        return await search.search_logs(
            client,
            index,
            query=query,
            start=start,
            end=end,
            max_hits=max_hits,
            start_offset=start_offset,
            sort_by=sort_by,
            search_field=search_field,
            snippet_fields=snippet_fields,
            fields=fields,
            settings=settings,
        )

    @mcp.tool()
    async def aggregate_logs(
        index: str,
        aggs: dict[str, Any],
        query: str = "*",
        start: str | int | None = None,
        end: str | int | None = None,
    ) -> dict[str, Any]:
        """Run an Elasticsearch-style aggregation (terms, date_histogram, metrics) and
        return {num_hits, aggregations} instead of raw documents."""
        return await search.aggregate_logs(
            client, index, aggs=aggs, query=query, start=start, end=end
        )

    @mcp.tool()
    def get_query_syntax_help() -> str:
        """Quickwit query-language + aggregation cheat sheet (no network call)."""
        return syntax_help.get_query_syntax_help()

    return mcp
