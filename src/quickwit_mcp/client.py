"""Async HTTP client for the Quickwit REST API.

A thin wrapper with no MCP concerns: it speaks Quickwit's ``/api/v1`` endpoints
and returns parsed JSON, raising :class:`QuickwitError` (with the original
response body) on any non-2xx status.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from .config import Settings, get_settings


class QuickwitError(Exception):
    """Raised when Quickwit returns a non-2xx response.

    The original response body (parsed JSON when possible, otherwise text) is
    preserved on :attr:`body` so callers can surface Quickwit's own error to the
    model for self-correction.
    """

    def __init__(self, status_code: int, body: Any, *, url: str | None = None) -> None:
        self.status_code = status_code
        self.body = body
        self.url = url
        super().__init__(f"Quickwit returned HTTP {status_code} for {url}: {body!r}")


class QuickwitClient:
    """Reusable async client over a single Quickwit instance.

    Holds a pooled :class:`httpx.AsyncClient`. Use as an async context manager,
    or call :meth:`aclose` when done. An external client may be injected (e.g.
    for testing); in that case the caller owns its lifecycle.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self._settings.qw_base_url,
            timeout=self._settings.qw_timeout,
            headers={"Accept": "application/json"},
        )

    async def __aenter__(self) -> QuickwitClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client if this instance owns it."""
        if self._owns_client:
            await self._client.aclose()

    # -- internals ---------------------------------------------------------

    @staticmethod
    def _handle(resp: httpx.Response) -> Any:
        if resp.is_success:
            return resp.json()
        try:
            body: Any = resp.json()
        except (json.JSONDecodeError, ValueError):
            body = resp.text
        raise QuickwitError(resp.status_code, body, url=str(resp.request.url))

    # -- endpoints ---------------------------------------------------------

    async def ping(self, *, timeout: float = 3.0) -> Any:
        """``GET /api/v1/version`` with a short timeout — a cheap reachability check.

        Used by the health endpoint; raises on any failure (non-2xx via
        :class:`QuickwitError`, connection/timeout via the underlying httpx error).
        """
        return self._handle(await self._client.get("/api/v1/version", timeout=timeout))

    async def list_indexes(self) -> Any:
        """``GET /api/v1/indexes`` — metadata for every index."""
        return self._handle(await self._client.get("/api/v1/indexes"))

    async def get_index_metadata(self, index_id: str) -> Any:
        """``GET /api/v1/indexes/{id}`` — full index metadata.

        This is where the doc mapping lives (``index_config.doc_mapping``),
        including ``field_mappings`` — the field-name/type schema needed to
        build valid queries. ``describe_index`` does *not* return the mapping.
        """
        return self._handle(await self._client.get(f"/api/v1/indexes/{index_id}"))

    async def describe_index(self, index_id: str) -> Any:
        """``GET /api/v1/indexes/{id}/describe`` — stats and timestamp range.

        Returns ``num_published_docs``, ``min_timestamp`` / ``max_timestamp``,
        ``timestamp_field_name`` and split sizes. For the field mapping, use
        :meth:`get_index_metadata`.
        """
        return self._handle(await self._client.get(f"/api/v1/indexes/{index_id}/describe"))

    async def search(
        self,
        index: str,
        *,
        query: str,
        start_timestamp: int | None = None,
        end_timestamp: int | None = None,
        max_hits: int,
        start_offset: int | None = None,
        sort_by: str | None = None,
        search_field: str | None = None,
        snippet_fields: list[str] | None = None,
        aggs: dict[str, Any] | None = None,
    ) -> Any:
        """``POST /api/v1/{index}/search``.

        ``index`` is passed through untouched, so single ids, comma-separated
        lists (``idx1,idx2``) and globs (``idx*``) all work. ``start_timestamp``
        / ``end_timestamp`` are unix epoch seconds. ``start_offset`` paginates
        past ``max_hits``. ``snippet_fields`` requests highlighted match
        snippets for the named fields; like ``search_field`` it is sent as a
        comma-separated string, the form Quickwit accepts in both GET and POST.
        """
        body: dict[str, Any] = {"query": query, "max_hits": max_hits}
        if start_timestamp is not None:
            body["start_timestamp"] = start_timestamp
        if end_timestamp is not None:
            body["end_timestamp"] = end_timestamp
        if start_offset is not None:
            body["start_offset"] = start_offset
        if sort_by is not None:
            body["sort_by"] = sort_by
        if search_field is not None:
            body["search_field"] = search_field
        if snippet_fields:
            body["snippet_fields"] = ",".join(snippet_fields)
        if aggs is not None:
            body["aggs"] = aggs
        return self._handle(await self._client.post(f"/api/v1/{index}/search", json=body))
