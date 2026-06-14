"""Search and aggregation tools."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..client import QuickwitClient, QuickwitError
from ..config import Settings, get_settings
from ..timeparse import to_epoch_seconds
from ..trim import clamp_max_hits, shape_search_response


def _is_single_index(index: str) -> bool:
    """Default 'latest' sorting only applies to a single concrete index."""
    return "," not in index and "*" not in index


async def _default_sort(client: QuickwitClient, index: str) -> str | None:
    """Resolve newest-first sort, or None if unavailable.

    Note Quickwit's (counter-intuitive) sort semantics, verified live against
    0.8.2: a bare field name sorts **descending** (newest first for a timestamp),
    while a ``-`` prefix sorts ascending. So newest-first is the bare field name.
    """
    if not _is_single_index(index):
        return None
    try:
        described = await client.describe_index(index)
    except QuickwitError:
        return None
    field = described.get("timestamp_field_name")
    return field if field else None


async def search_logs(
    client: QuickwitClient,
    index: str,
    *,
    query: str = "*",
    start: str | int | None = None,
    end: str | int | None = None,
    max_hits: int | None = None,
    start_offset: int | None = None,
    sort_by: str | None = None,
    search_field: str | None = None,
    snippet_fields: Iterable[str] | None = None,
    fields: Iterable[str] | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Search logs in one or more indexes.

    ``index`` may be a single id, a comma list, or a glob. ``query`` uses the
    Quickwit query language; ``start`` / ``end`` accept human time and are
    converted to epoch seconds. ``max_hits`` is clamped to the configured
    ceiling (default count when omitted). ``start_offset`` paginates; ``fields``
    projects each hit to the chosen keys.

    When ``sort_by`` is omitted and a single concrete index is targeted, results
    default to **newest first** (descending on the index timestamp field).
    Snippets and any aggregations are preserved in the response.
    """
    settings = settings or get_settings()
    if sort_by is None:
        sort_by = await _default_sort(client, index)

    raw = await client.search(
        index,
        query=query,
        start_timestamp=to_epoch_seconds(start) if start is not None else None,
        end_timestamp=to_epoch_seconds(end) if end is not None else None,
        max_hits=clamp_max_hits(max_hits, settings),
        start_offset=start_offset,
        sort_by=sort_by,
        search_field=search_field,
        snippet_fields=list(snippet_fields) if snippet_fields else None,
    )
    return shape_search_response(raw, fields=fields)


async def aggregate_logs(
    client: QuickwitClient,
    index: str,
    *,
    aggs: dict[str, Any],
    query: str = "*",
    start: str | int | None = None,
    end: str | int | None = None,
) -> dict[str, Any]:
    """Run an Elasticsearch-style aggregation and return counts, not documents.

    ``aggs`` is the aggregation request (e.g. ``date_histogram``, ``terms``,
    metric aggs). ``query`` (default match-all) and ``start`` / ``end`` (human
    time, converted to epoch seconds) scope the documents aggregated over.
    ``max_hits`` is forced to 0 so no raw hits come back — only the buckets.

    Returns ``{"num_hits": <total matched>, "aggregations": {...}}``.
    """
    if not isinstance(aggs, dict) or not aggs:
        raise ValueError("aggs must be a non-empty object")

    raw = await client.search(
        index,
        query=query,
        max_hits=0,
        start_timestamp=to_epoch_seconds(start) if start is not None else None,
        end_timestamp=to_epoch_seconds(end) if end is not None else None,
        aggs=aggs,
    )
    return {
        "num_hits": raw.get("num_hits"),
        "aggregations": raw.get("aggregations", {}),
    }
