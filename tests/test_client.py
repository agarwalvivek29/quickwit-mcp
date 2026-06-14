"""Tests for the Quickwit REST client (httpx mocked with respx)."""

import json

import httpx
import pytest
import respx

from quickwit_mcp.client import QuickwitClient, QuickwitError
from quickwit_mcp.config import Settings

BASE = "http://qw.test"


def make_client() -> QuickwitClient:
    return QuickwitClient(settings=Settings(qw_base_url=BASE, _env_file=None))


@respx.mock
async def test_list_indexes():
    route = respx.get(f"{BASE}/api/v1/indexes").mock(
        return_value=httpx.Response(200, json=[{"index_id": "logs"}])
    )
    async with make_client() as c:
        out = await c.list_indexes()
    assert route.called
    assert out == [{"index_id": "logs"}]


@respx.mock
async def test_ping_returns_version():
    respx.get(f"{BASE}/api/v1/version").mock(
        return_value=httpx.Response(200, json={"build": {"version": "v0.8.2"}})
    )
    async with make_client() as c:
        out = await c.ping()
    assert out["build"]["version"] == "v0.8.2"


@respx.mock
async def test_ping_raises_on_error():
    respx.get(f"{BASE}/api/v1/version").mock(return_value=httpx.Response(503, text="down"))
    async with make_client() as c:
        with pytest.raises(QuickwitError):
            await c.ping()


@respx.mock
async def test_get_index_metadata():
    respx.get(f"{BASE}/api/v1/indexes/logs").mock(
        return_value=httpx.Response(
            200,
            json={"index_config": {"doc_mapping": {"field_mappings": [{"name": "level"}]}}},
        )
    )
    async with make_client() as c:
        out = await c.get_index_metadata("logs")
    assert out["index_config"]["doc_mapping"]["field_mappings"][0]["name"] == "level"


@respx.mock
async def test_describe_index():
    respx.get(f"{BASE}/api/v1/indexes/logs/describe").mock(
        return_value=httpx.Response(200, json={"num_docs": 42})
    )
    async with make_client() as c:
        out = await c.describe_index("logs")
    assert out["num_docs"] == 42


@respx.mock
async def test_search_builds_body_and_returns_payload():
    route = respx.post(f"{BASE}/api/v1/logs/search").mock(
        return_value=httpx.Response(200, json={"num_hits": 1, "hits": [{"x": 1}]})
    )
    async with make_client() as c:
        out = await c.search(
            "logs",
            query="level:ERROR",
            max_hits=10,
            start_timestamp=1000,
            end_timestamp=2000,
            sort_by="timestamp",
        )
    assert out["num_hits"] == 1
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "query": "level:ERROR",
        "max_hits": 10,
        "start_timestamp": 1000,
        "end_timestamp": 2000,
        "sort_by": "timestamp",
    }


@respx.mock
async def test_search_omits_unset_optional_fields():
    route = respx.post(f"{BASE}/api/v1/logs/search").mock(
        return_value=httpx.Response(200, json={"num_hits": 0, "hits": []})
    )
    async with make_client() as c:
        await c.search("logs", query="*", max_hits=5)
    body = json.loads(route.calls.last.request.content)
    assert body == {"query": "*", "max_hits": 5}


@respx.mock
async def test_search_pagination_and_snippets():
    route = respx.post(f"{BASE}/api/v1/logs/search").mock(
        return_value=httpx.Response(200, json={"num_hits": 0, "hits": []})
    )
    async with make_client() as c:
        await c.search(
            "logs",
            query="error",
            max_hits=20,
            start_offset=40,
            snippet_fields=["message", "body"],
        )
    body = json.loads(route.calls.last.request.content)
    assert body["start_offset"] == 40
    # snippet_fields is serialized comma-separated, the form Quickwit accepts.
    assert body["snippet_fields"] == "message,body"


@respx.mock
async def test_search_passes_aggs():
    route = respx.post(f"{BASE}/api/v1/logs/search").mock(
        return_value=httpx.Response(200, json={"aggregations": {}})
    )
    aggs = {"by_level": {"terms": {"field": "level"}}}
    async with make_client() as c:
        await c.search("logs", query="*", max_hits=0, aggs=aggs)
    body = json.loads(route.calls.last.request.content)
    assert body["aggs"] == aggs


@respx.mock
async def test_search_multi_index_glob_passthrough():
    route = respx.post(f"{BASE}/api/v1/app-logs,api-logs/search").mock(
        return_value=httpx.Response(200, json={"num_hits": 0, "hits": []})
    )
    async with make_client() as c:
        await c.search("app-logs,api-logs", query="*", max_hits=5)
    assert route.called


@respx.mock
async def test_error_preserves_json_body():
    respx.get(f"{BASE}/api/v1/indexes").mock(
        return_value=httpx.Response(400, json={"message": "bad query"})
    )
    async with make_client() as c:
        with pytest.raises(QuickwitError) as excinfo:
            await c.list_indexes()
    assert excinfo.value.status_code == 400
    assert excinfo.value.body == {"message": "bad query"}


@respx.mock
async def test_error_falls_back_to_text_body():
    respx.get(f"{BASE}/api/v1/indexes").mock(return_value=httpx.Response(502, text="upstream down"))
    async with make_client() as c:
        with pytest.raises(QuickwitError) as excinfo:
            await c.list_indexes()
    assert excinfo.value.status_code == 502
    assert excinfo.value.body == "upstream down"
