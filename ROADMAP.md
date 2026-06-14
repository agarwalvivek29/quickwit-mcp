# Roadmap

Direction for quickwit-mcp. Dates are intentionally omitted; items move when they're ready.

## v0.0.1 — MVP (read-only) ✅

The minimal, safe, read-only server.

- Async Quickwit REST client (Quickwit 0.8)
- Tools: `list_indexes`, `describe_index`, `search_logs`, `aggregate_logs`, `get_query_syntax_help`
- Config via env; `stdio` + `streamable-http` transports
- Time parsing, response shaping (projection + hit clamp)
- Dockerfile, CI (matrix + coverage + docker build), dev harness (`scripts/dev-quickwit.sh`)
- Docs

## v0.1.0 — richer reading & operability

- **Auth passthrough** — optional bearer/header forwarding to Quickwit for setups not fronted by a gateway
- **`search/stream`** — bulk export endpoint for large result sets (CSV / row-binary)
- **MCP resources** — expose live index schemas as resources, not just a tool call
- **Aggregation helpers** — typed convenience tools for common shapes (error-rate-over-time, top-N services)
- **Per-index timestamp-field caching** — avoid the extra `describe` lookup on every defaulted search

## Later

- Caching of index metadata / describe results
- Multi-cluster support (route by index → cluster)
- Elasticsearch-compatible API (`/api/v1/_elastic/...`) as an alternate query surface
- Optional, clearly-guarded write/admin tools (ingest, index management) — off by default

## Governance

- **Branch protection** on `main` (require PR + CI + CODEOWNERS review) — to be enabled once a
  second maintainer joins, which resolves the solo self-approval limitation.

Have an idea? Open a [feature request](https://github.com/agarwalvivek29/quickwit-mcp/issues/new/choose).
