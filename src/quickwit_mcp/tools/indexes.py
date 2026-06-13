"""Index discovery tools."""

from __future__ import annotations

import asyncio
from typing import Any

from ..client import QuickwitClient, QuickwitError


def _config(meta: dict[str, Any]) -> dict[str, Any]:
    return meta.get("index_config", {}) if isinstance(meta, dict) else {}


def _flatten_field_mappings(
    field_mappings: list[dict[str, Any]], prefix: str = ""
) -> dict[str, str]:
    """Flatten Quickwit ``field_mappings`` into ``{dotted_name: type}``.

    ``object`` fields are recursed into so nested fields surface as
    ``parent.child`` — the form used in queries.
    """
    out: dict[str, str] = {}
    for field in field_mappings:
        name = field.get("name")
        if not name:
            continue
        full = f"{prefix}{name}"
        ftype = field.get("type")
        if ftype == "object" and isinstance(field.get("field_mappings"), list):
            out.update(_flatten_field_mappings(field["field_mappings"], prefix=f"{full}."))
        else:
            out[full] = ftype
    return out


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


async def describe_index(client: QuickwitClient, index_id: str) -> dict[str, Any]:
    """Describe an index: stats, timestamp range, and field schema.

    Merges two endpoints because ``/describe`` returns counts and the timestamp
    range but **not** the field mapping — that lives on the index metadata. The
    ``fields`` map (``name -> type``, nested fields dotted) is what lets a model
    build valid queries instead of guessing field names.
    """
    described, meta = await asyncio.gather(
        client.describe_index(index_id),
        client.get_index_metadata(index_id),
    )
    doc_mapping = _config(meta).get("doc_mapping", {})
    return {
        "index_id": index_id,
        "num_docs": described.get("num_published_docs"),
        "size_bytes": described.get("size_published_docs_uncompressed"),
        "timestamp_field": (
            described.get("timestamp_field_name") or doc_mapping.get("timestamp_field")
        ),
        "min_timestamp": described.get("min_timestamp"),
        "max_timestamp": described.get("max_timestamp"),
        "fields": _flatten_field_mappings(doc_mapping.get("field_mappings", [])),
    }
