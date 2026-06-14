"""Tests for the static query-syntax help tool."""

from quickwit_mcp.tools.help import get_query_syntax_help


def test_returns_nonempty_markdown():
    text = get_query_syntax_help()
    assert isinstance(text, str)
    assert len(text) > 200


def test_covers_key_topics():
    text = get_query_syntax_help()
    for token in (
        "level:ERROR",  # term query
        "IN [",  # term set
        "TO",  # range
        "AND",  # boolean
        "date_histogram",  # aggregation
        "start",  # time filtering guidance
    ):
        assert token in text


def test_documents_inverted_sort():
    text = get_query_syntax_help()
    # The counter-intuitive sort behavior must be called out.
    assert "newest first" in text
    assert 'sort_by: "timestamp"' in text


def test_is_pure_no_args():
    # Stable, deterministic, no network.
    assert get_query_syntax_help() == get_query_syntax_help()
