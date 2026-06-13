"""Tests for the aggregate_logs tool (client stubbed, no HTTP)."""

from datetime import datetime, timezone

import pytest

from quickwit_mcp.tools.search import aggregate_logs


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def search(self, index, **kwargs):
        self.calls.append((index, kwargs))
        return self.response


AGGS = {"by_level": {"terms": {"field": "level"}}}
RESPONSE = {
    "num_hits": 6,
    "hits": [],
    "aggregations": {"by_level": {"buckets": [{"key": "ERROR", "doc_count": 3}]}},
}


async def test_forces_max_hits_zero_and_passes_aggs():
    client = FakeClient(RESPONSE)
    await aggregate_logs(client, "logs", aggs=AGGS)
    index, kwargs = client.calls[0]
    assert index == "logs"
    assert kwargs["max_hits"] == 0
    assert kwargs["aggs"] == AGGS
    assert kwargs["query"] == "*"


async def test_returns_num_hits_and_aggregations():
    out = await aggregate_logs(FakeClient(RESPONSE), "logs", aggs=AGGS)
    assert out["num_hits"] == 6
    assert out["aggregations"]["by_level"]["buckets"][0]["doc_count"] == 3


async def test_time_bounds_converted_to_epoch():
    client = FakeClient(RESPONSE)
    await aggregate_logs(client, "logs", aggs=AGGS, start="2026-06-01T00:00:00Z", end=1718200300)
    _, kwargs = client.calls[0]
    expected_start = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())
    assert kwargs["start_timestamp"] == expected_start
    assert kwargs["end_timestamp"] == 1718200300


@pytest.mark.parametrize("bad", [None, {}, [], "terms"])
async def test_rejects_empty_or_non_object_aggs(bad):
    with pytest.raises(ValueError):
        await aggregate_logs(FakeClient(RESPONSE), "logs", aggs=bad)
