"""Static query-syntax help for building Quickwit queries.

A cheap, network-free reference the model can pull before composing a search,
so it writes valid queries instead of guessing. Content tracks the Quickwit 0.8
query language (https://quickwit.io/docs/reference/query-language).
"""

from __future__ import annotations

_QUERY_SYNTAX_HELP = """\
# Quickwit query language — cheat sheet

Pass these as the `query` argument to `search_logs` / `aggregate_logs`.

## Clauses
- Term:            `level:ERROR`
- Phrase:          `message:"connection refused"`  (field needs `record: position`)
- Phrase prefix:   `message:"connection ref"*`
- Term prefix:     `service:payment*`
- Term set:        `level:IN [ERROR WARN]`
- Exists:          `trace_id:*`            (field is set)
- Match all:       `*`
- Nested fields:   `resource.service:checkout`   (dotted path)

## Ranges
- Inclusive:       `status:[400 TO 599]`
- Exclusive:       `latency_ms:{100 TO 200}`
- Half-open:       `status:[500 TO *]`
- Comparison:      `latency_ms:>100`, `>=100`, `<50`, `<=50`

## Booleans
- `AND` (default between clauses), `OR`, `NOT` (or `-`)
- Precedence: `NOT` > `AND` > `OR`; group with parentheses
- Example: `(level:ERROR OR level:WARN) AND service:payment NOT message:timeout`

## Escaping
Escape these with `\\`:  `+ ^ : { } " [ ] ( ) ~ ! \\ *` and space.

## Time filtering — do NOT put it in the query
Use the `start` / `end` arguments instead (accept `now`, `now-1h`, `now-7d`,
ISO-8601 like `2026-06-01T12:00:00Z`, or raw epoch seconds). They prune at the
storage layer and are much cheaper than a range clause.

## Sorting (heads-up: inverted vs. most engines)
In Quickwit a **bare field name sorts DESCENDING**, a `-` prefix sorts ascending:
- `sort_by: "timestamp"`  -> newest first
- `sort_by: "-timestamp"` -> oldest first
`search_logs` already defaults to newest-first on a single index.

## Aggregations (`aggregate_logs`, Elasticsearch-style)
Count by a field (terms):
```json
{"by_level": {"terms": {"field": "level", "size": 10}}}
```
Trend over time (date_histogram):
```json
{"over_time": {"date_histogram": {"field": "timestamp", "fixed_interval": "1h"}}}
```
Metric inside a bucket (avg latency per service):
```json
{"by_service": {"terms": {"field": "service"},
  "aggs": {"avg_latency": {"avg": {"field": "latency_ms"}}}}}
```
Metric aggs available: avg, min, max, sum, count, stats, percentiles.
"""


def get_query_syntax_help() -> str:
    """Return a concise Quickwit query-language + aggregation cheat sheet (markdown)."""
    return _QUERY_SYNTAX_HELP
