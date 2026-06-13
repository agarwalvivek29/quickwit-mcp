"""Tests for the list_indexes tool (client stubbed, no HTTP)."""

from quickwit_mcp.client import QuickwitError
from quickwit_mcp.tools.indexes import list_indexes


class FakeClient:
    def __init__(self, indexes, describe=None, fail_for=()):
        self._indexes = indexes
        self._describe = describe or {}
        self._fail_for = set(fail_for)

    async def list_indexes(self):
        return self._indexes

    async def describe_index(self, index_id):
        if index_id in self._fail_for:
            raise QuickwitError(500, "boom")
        return self._describe[index_id]


def _meta(index_id, uri=None):
    return {"index_config": {"index_id": index_id, "index_uri": uri or f"file:///{index_id}"}}


async def test_list_basic_sorted():
    client = FakeClient([_meta("b-logs"), _meta("a-logs")])
    out = await list_indexes(client)
    assert [i["index_id"] for i in out] == ["a-logs", "b-logs"]
    assert out[0]["index_uri"] == "file:///a-logs"
    assert "num_docs" not in out[0]


async def test_list_with_stats():
    client = FakeClient(
        [_meta("logs")],
        describe={"logs": {"num_published_docs": 6, "min_timestamp": 1, "max_timestamp": 9}},
    )
    out = await list_indexes(client, with_stats=True)
    assert out[0]["num_docs"] == 6
    assert out[0]["min_timestamp"] == 1
    assert out[0]["max_timestamp"] == 9


async def test_list_with_stats_tolerates_describe_failure():
    client = FakeClient([_meta("logs")], fail_for={"logs"})
    out = await list_indexes(client, with_stats=True)
    # listing still succeeds, just without stats for the failed index
    assert out[0]["index_id"] == "logs"
    assert "num_docs" not in out[0]


async def test_empty():
    assert await list_indexes(FakeClient([])) == []
