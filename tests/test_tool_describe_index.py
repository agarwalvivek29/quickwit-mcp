"""Tests for the describe_index tool (client stubbed, no HTTP)."""

from quickwit_mcp.tools.indexes import describe_index


class FakeClient:
    def __init__(self, described, meta):
        self._described = described
        self._meta = meta

    async def describe_index(self, index_id):
        return self._described

    async def get_index_metadata(self, index_id):
        return self._meta


DESCRIBED = {
    "num_published_docs": 6,
    "size_published_docs_uncompressed": 679,
    "timestamp_field_name": "timestamp",
    "min_timestamp": 1718200000,
    "max_timestamp": 1718200300,
}

META = {
    "index_config": {
        "doc_mapping": {
            "timestamp_field": "timestamp",
            "field_mappings": [
                {"name": "timestamp", "type": "datetime"},
                {"name": "level", "type": "text"},
                {
                    "name": "resource",
                    "type": "object",
                    "field_mappings": [
                        {"name": "service", "type": "text"},
                        {"name": "host", "type": "text"},
                    ],
                },
            ],
        }
    }
}


async def test_merges_stats_and_schema():
    out = await describe_index(FakeClient(DESCRIBED, META), "logs-demo")
    assert out["index_id"] == "logs-demo"
    assert out["num_docs"] == 6
    assert out["size_bytes"] == 679
    assert out["timestamp_field"] == "timestamp"
    assert out["min_timestamp"] == 1718200000
    assert out["max_timestamp"] == 1718200300


async def test_field_mapping_flattens_nested_objects():
    out = await describe_index(FakeClient(DESCRIBED, META), "logs-demo")
    assert out["fields"] == {
        "timestamp": "datetime",
        "level": "text",
        "resource.service": "text",
        "resource.host": "text",
    }


async def test_tolerates_empty_mapping():
    out = await describe_index(
        FakeClient({"num_published_docs": 0}, {"index_config": {"doc_mapping": {}}}),
        "empty",
    )
    assert out["fields"] == {}
    assert out["num_docs"] == 0
    assert out["timestamp_field"] is None
