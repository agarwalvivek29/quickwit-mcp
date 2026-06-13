"""Tests for the time-expression parser."""

from datetime import datetime, timezone

import pytest

from quickwit_mcp.timeparse import to_epoch_seconds

# Fixed reference point for deterministic relative-offset tests.
NOW = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
NOW_EPOCH = 1767225600  # 2026-01-01T00:00:00Z


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("now", NOW_EPOCH),
        ("NOW", NOW_EPOCH),
        ("now-45s", NOW_EPOCH - 45),
        ("now-30m", NOW_EPOCH - 1800),
        ("now-1h", NOW_EPOCH - 3600),
        ("now-7d", NOW_EPOCH - 7 * 86400),
        ("now-1H", NOW_EPOCH - 3600),  # case-insensitive unit
    ],
)
def test_relative(value, expected):
    assert to_epoch_seconds(value, now=NOW) == expected


def test_iso_utc_z():
    expected = int(datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp())
    assert to_epoch_seconds("2026-06-01T12:00:00Z") == expected


def test_iso_with_offset():
    assert to_epoch_seconds("2026-06-01T12:00:00+05:30") == to_epoch_seconds("2026-06-01T06:30:00Z")


def test_iso_naive_treated_as_utc():
    expected = int(datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp())
    assert to_epoch_seconds("2026-06-01T12:00:00") == expected


def test_iso_bare_date_is_midnight_utc():
    expected = int(datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp())
    assert to_epoch_seconds("2026-06-01") == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1718200000, 1718200000),
        ("1718200000", 1718200000),
        (1718200000.9, 1718200000),  # truncated
        ("1718200000.9", 1718200000),
        ("  1718200000  ", 1718200000),  # whitespace tolerated
    ],
)
def test_raw_epoch(value, expected):
    assert to_epoch_seconds(value) == expected


@pytest.mark.parametrize("value", ["", "   ", "tomorrow", "now-1y", "now+1h", "not-a-date"])
def test_invalid_strings_raise_value_error(value):
    with pytest.raises(ValueError):
        to_epoch_seconds(value)


@pytest.mark.parametrize("value", [None, True, [], {}])
def test_invalid_types_raise_type_error(value):
    with pytest.raises(TypeError):
        to_epoch_seconds(value)
