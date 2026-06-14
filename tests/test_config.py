"""Tests for the environment-based settings module."""

import pytest
from pydantic import ValidationError

from quickwit_mcp.config import Settings, Transport

_ENV_VARS = (
    "QW_BASE_URL",
    "QW_TIMEOUT",
    "QW_DEFAULT_MAX_HITS",
    "QW_MAX_HITS_CEILING",
    "MCP_TRANSPORT",
)


def _settings(monkeypatch, **env):
    """Build Settings from a clean env, ignoring any local .env file."""
    for key in _ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return Settings(_env_file=None)


def test_defaults(monkeypatch):
    s = _settings(monkeypatch, QW_BASE_URL="http://localhost:7280")
    assert s.qw_base_url == "http://localhost:7280"
    assert s.qw_timeout == 30.0
    assert s.qw_default_max_hits == 100
    assert s.qw_max_hits_ceiling == 500
    assert s.mcp_transport is Transport.STDIO
    assert s.mcp_host == "127.0.0.1"
    assert s.mcp_port == 8000


def test_missing_base_url_raises(monkeypatch):
    with pytest.raises(ValidationError):
        _settings(monkeypatch)


def test_base_url_must_be_http(monkeypatch):
    with pytest.raises(ValidationError):
        _settings(monkeypatch, QW_BASE_URL="localhost:7280")


def test_base_url_trailing_slash_stripped(monkeypatch):
    s = _settings(monkeypatch, QW_BASE_URL="http://localhost:7280/")
    assert s.qw_base_url == "http://localhost:7280"


def test_transport_parsed_from_env(monkeypatch):
    s = _settings(
        monkeypatch,
        QW_BASE_URL="http://example:7280",
        MCP_TRANSPORT="streamable-http",
    )
    assert s.mcp_transport is Transport.STREAMABLE_HTTP


def test_default_hits_cannot_exceed_ceiling(monkeypatch):
    with pytest.raises(ValidationError):
        _settings(
            monkeypatch,
            QW_BASE_URL="http://example:7280",
            QW_DEFAULT_MAX_HITS="600",
            QW_MAX_HITS_CEILING="500",
        )


def test_timeout_must_be_positive(monkeypatch):
    with pytest.raises(ValidationError):
        _settings(monkeypatch, QW_BASE_URL="http://example:7280", QW_TIMEOUT="0")
