"""Index discovery tools."""

from __future__ import annotations

import asyncio
from typing import Any

from ..client import QuickwitClient, QuickwitError


def _config(meta: dict[str, Any]) -> dict[str, Any]:
    return meta.get("index_config", {}) if isinstance(meta, dict) else {}


async def list_indexes(client: QuickwitClient, *, with_stats: bool = False) -> list[dict[str, Any]]:
    """List the indexes available to query.

    Returns one entry per index with its ``index_id`` and ``index_uri``, sorted
    by id. With ``with_stats=True``, also fetches each index's
    ``num_docs`` and timestamp range (``min_timestamp`` / ``max_timestamp``) via
    ``describe`` — issued concurrently. An index whose describe call fails is
    returned without stats rather than failing the whole listing.
    """
    raw = await client.list_indexes()
    items: list[dict[str, Any]] = [
        {"index_id": _config(m).get("index_id"), "index_uri": _config(m).get("index_uri")}
        for m in raw
    ]
    items.sort(key=lambda d: d["index_id"] or "")
    if not with_stats:
        return items

    async def _augment(item: dict[str, Any]) -> dict[str, Any]:
        try:
            described = await client.describe_index(item["index_id"])
        except QuickwitError:
            return item
        item["num_docs"] = described.get("num_published_docs")
        item["min_timestamp"] = described.get("min_timestamp")
        item["max_timestamp"] = described.get("max_timestamp")
        return item

    return list(await asyncio.gather(*(_augment(i) for i in items)))
