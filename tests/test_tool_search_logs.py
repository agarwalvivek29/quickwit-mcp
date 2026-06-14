"""Tests for the search_logs tool (client stubbed, no HTTP)."""

from datetime import datetime, timezone

from quickwit_mcp.config import Settings
from quickwit_mcp.tools.search import search_logs


class FakeClient:
    def __init__(self, response=None, timestamp_field="timestamp"):
        self.response = response or {"num_hits": 0, "hits": []}
        self._timestamp_field = timestamp_field
        self.calls = []

    async def describe_index(self, index_id):
        return {"timestamp_field_name": self._timestamp_field}

    async def search(self, index, **kwargs):
        self.calls.append((index, kwargs))
        return self.response


SETTINGS = Settings(qw_base_url="http://qw.test", _env_file=None)
HITS = {
    "num_hits": 1,
    "hits": [{"level": "ERROR", "message": "boom", "service": "auth"}],
    "snippets": [{"message": ["<b>boom</b>"]}],
}


async def test_default_sort_is_newest_first():
    client = FakeClient()
    await search_logs(client, "logs", settings=SETTINGS)
    _, kwargs = client.calls[0]
    # Quickwit: bare field name sorts descending (newest first); '-' would be ascending.
    assert kwargs["sort_by"] == "timestamp"


async def test_explicit_sort_is_respected():
    client = FakeClient()
    await search_logs(client, "logs", sort_by="level", settings=SETTINGS)
    _, kwargs = client.calls[0]
    assert kwargs["sort_by"] == "level"


async def test_glob_index_skips_default_sort():
    client = FakeClient()
    await search_logs(client, "app-*,api-*", settings=SETTINGS)
    _, kwargs = client.calls[0]
    assert kwargs["sort_by"] is None


async def test_default_max_hits_and_ceiling_clamp():
    client = FakeClient()
    await search_logs(client, "logs", settings=SETTINGS)
    assert client.calls[0][1]["max_hits"] == SETTINGS.qw_default_max_hits

    client2 = FakeClient()
    await search_logs(client2, "logs", max_hits=10_000, settings=SETTINGS)
    assert client2.calls[0][1]["max_hits"] == SETTINGS.qw_max_hits_ceiling


async def test_time_converted_and_pagination_passed():
    client = FakeClient()
    await search_logs(
        client,
        "logs",
        start="2026-06-01T00:00:00Z",
        end=1718200300,
        start_offset=40,
        settings=SETTINGS,
    )
    _, kwargs = client.calls[0]
    assert kwargs["start_timestamp"] == int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())
    assert kwargs["end_timestamp"] == 1718200300
    assert kwargs["start_offset"] == 40


async def test_field_projection_applied_and_snippets_preserved():
    client = FakeClient(response=HITS)
    out = await search_logs(client, "logs", fields=["level"], settings=SETTINGS)
    assert out["hits"] == [{"level": "ERROR"}]
    assert out["snippets"] == HITS["snippets"]
    assert out["num_hits"] == 1


async def test_search_field_and_snippet_fields_passed():
    client = FakeClient()
    await search_logs(
        client, "logs", search_field="message", snippet_fields=["message"], settings=SETTINGS
    )
    _, kwargs = client.calls[0]
    assert kwargs["search_field"] == "message"
    assert kwargs["snippet_fields"] == ["message"]
