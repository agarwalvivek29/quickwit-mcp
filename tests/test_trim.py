"""Tests for response shaping (projection + hit-count clamp)."""

from quickwit_mcp.config import Settings
from quickwit_mcp.trim import clamp_max_hits, project_hits, shape_search_response


def _settings(**over):
    return Settings(qw_base_url="http://qw.test", _env_file=None, **over)


def test_clamp_defaults_when_none():
    s = _settings()
    assert clamp_max_hits(None, s) == s.qw_default_max_hits


def test_clamp_caps_at_ceiling():
    s = _settings()
    assert clamp_max_hits(10_000, s) == s.qw_max_hits_ceiling


def test_clamp_floors_at_one():
    s = _settings()
    assert clamp_max_hits(0, s) == 1
    assert clamp_max_hits(-5, s) == 1


def test_clamp_passes_through_in_range():
    s = _settings()
    assert clamp_max_hits(50, s) == 50


def test_project_passthrough_when_no_fields():
    hits = [{"a": 1, "b": 2}]
    assert project_hits(hits, None) == hits
    assert project_hits(hits, []) == hits


def test_project_selects_fields_and_ignores_missing():
    hits = [{"level": "ERROR", "message": "boom", "service": "auth"}]
    assert project_hits(hits, ["level", "message", "nope"]) == [
        {"level": "ERROR", "message": "boom"}
    ]


def test_shape_preserves_envelope_and_rich_keys():
    raw = {
        "num_hits": 2,
        "elapsed_time_micros": 1234,
        "errors": [],
        "snippets": [{"message": ["<b>boom</b>"]}],
        "aggregations": {"by_level": {"buckets": []}},
        "hits": [{"level": "ERROR", "message": "boom", "service": "auth"}],
    }
    out = shape_search_response(raw, fields=["level"])
    # rich data survives
    assert out["num_hits"] == 2
    assert out["elapsed_time_micros"] == 1234
    assert out["snippets"] == raw["snippets"]
    assert out["aggregations"] == raw["aggregations"]
    # only hits are projected
    assert out["hits"] == [{"level": "ERROR"}]


def test_shape_without_fields_keeps_full_hits():
    raw = {"num_hits": 1, "hits": [{"level": "INFO", "message": "ok"}]}
    out = shape_search_response(raw)
    assert out["hits"] == [{"level": "INFO", "message": "ok"}]


def test_shape_handles_missing_hits():
    out = shape_search_response({"num_hits": 0})
    assert out == {"num_hits": 0, "hits": []}
