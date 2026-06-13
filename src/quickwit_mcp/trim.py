"""Shape Quickwit search responses for LLM consumption.

The goal is modest and non-destructive: bound how many hits come back by
default, and let a caller *opt in* to projecting each hit down to the fields it
cares about. We never strip the response envelope and never drop ``snippets``
or ``aggregations`` — slimming is something the caller asks for, not something
that happens silently.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .config import Settings

# Top-level keys worth carrying through from a Quickwit search response.
_PRESERVED_KEYS = ("num_hits", "elapsed_time_micros", "errors", "snippets", "aggregations")


def clamp_max_hits(requested: int | None, settings: Settings) -> int:
    """Resolve and bound the hit count for a search.

    ``None`` -> the configured default. Anything above the ceiling is capped;
    values below 1 are floored to 1.
    """
    value = settings.qw_default_max_hits if requested is None else requested
    value = min(value, settings.qw_max_hits_ceiling)
    return max(value, 1)


def project_hits(hits: Iterable[dict[str, Any]], fields: Iterable[str] | None) -> list[dict]:
    """Reduce each hit to ``fields`` (keys that are present), or return as-is.

    When ``fields`` is falsy, hits pass through unchanged.
    """
    if not fields:
        return list(hits)
    keep = list(fields)
    return [{k: hit[k] for k in keep if k in hit} for hit in hits]


def shape_search_response(raw: dict[str, Any], *, fields: Iterable[str] | None = None) -> dict:
    """Return a compact response: preserved envelope + (optionally projected) hits.

    ``num_hits``, ``elapsed_time_micros``, ``errors``, ``snippets`` and
    ``aggregations`` are carried through untouched when present. Only the per-hit
    documents are reshaped, and only if ``fields`` is given.
    """
    out: dict[str, Any] = {key: raw[key] for key in _PRESERVED_KEYS if key in raw}
    out["hits"] = project_hits(raw.get("hits", []), fields)
    return out
