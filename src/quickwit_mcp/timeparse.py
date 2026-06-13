"""Parse human-friendly time expressions into unix epoch seconds.

Quickwit's ``start_timestamp`` / ``end_timestamp`` are unix epoch **seconds**,
which prune splits at the storage layer (far cheaper than a range in the query
string). This module accepts the forms a human or an LLM is likely to produce
and normalizes them.

Supported inputs:
  * ``"now"`` and relative offsets ``"now-<N><unit>"`` where unit is
    ``s`` / ``m`` / ``h`` / ``d`` (e.g. ``"now-1h"``, ``"now-7d"``), case-insensitive
  * ISO-8601 datetimes, e.g. ``"2026-06-01T12:00:00Z"`` (a naive value is treated
    as UTC; a bare date like ``"2026-06-01"`` is midnight UTC)
  * raw epoch seconds as ``int`` / ``float`` / numeric string
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

_RELATIVE_RE = re.compile(r"^now(?:-(\d+)([smhd]))?$", re.IGNORECASE)
_NUMERIC_RE = re.compile(r"-?\d+(?:\.\d+)?")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def to_epoch_seconds(value: str | int | float, *, now: datetime | None = None) -> int:
    """Convert a time expression to unix epoch seconds.

    ``now`` may be injected (a :class:`datetime`) so relative offsets are
    deterministic in tests; it defaults to the current UTC time.

    Raises :class:`ValueError` for unparseable strings and :class:`TypeError`
    for unsupported value types.
    """
    # bool is an int subclass — reject it explicitly to avoid True -> 1.
    if isinstance(value, bool):
        raise TypeError("boolean is not a valid time value")
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str):
        raise TypeError(f"unsupported time value type: {type(value).__name__}")

    text = value.strip()
    if not text:
        raise ValueError("empty time value")

    # Raw epoch seconds (int or float form).
    if _NUMERIC_RE.fullmatch(text):
        return int(float(text))

    # "now" / "now-<N><unit>".
    match = _RELATIVE_RE.fullmatch(text)
    if match:
        base = now or datetime.now(timezone.utc)
        base_epoch = int(base.timestamp())
        amount, unit = match.groups()
        if amount is None:
            return base_epoch
        return base_epoch - int(amount) * _UNIT_SECONDS[unit.lower()]

    # ISO-8601. datetime.fromisoformat in Python 3.10 does not accept a "Z"
    # suffix, so normalize it to an explicit UTC offset first.
    iso = f"{text[:-1]}+00:00" if text.endswith(("Z", "z")) else text
    try:
        parsed = datetime.fromisoformat(iso)
    except ValueError as exc:
        raise ValueError(f"could not parse time value: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())
