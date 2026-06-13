"""Search and aggregation tools."""

from __future__ import annotations

from typing import Any

from ..client import QuickwitClient
from ..timeparse import to_epoch_seconds


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
