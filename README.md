# quickwit-mcp

A **[Model Context Protocol](https://modelcontextprotocol.io) (MCP) server** that exposes
[Quickwit](https://quickwit.io) log search and aggregations to LLM clients (Claude and others).

It's a thin, stateless, **read-only** layer: MCP tool calls → Quickwit REST API → trimmed JSON.
Run it locally over `stdio`, or remotely over `streamable-http` behind an MCP gateway.

Targets the Quickwit **0.8** REST API.

## Why

Investigating logs through an LLM should be as simple as asking. This server gives an agent the
minimal, safe surface it needs — discover indexes, learn their schema, search, and aggregate —
without any destructive capability.

## Architecture

```
┌────────────┐   MCP    ┌──────────────┐   MCP    ┌───────────────┐  HTTP   ┌───────────┐
│ Claude /   │ ───────▶ │ MCP Gateway  │ ───────▶ │ quickwit-mcp  │ ──────▶ │ Quickwit  │
│ MCP client │  (http)  │ (auth, etc.) │  (http)  │ (this server) │  REST   │  0.8 API  │
└────────────┘          └──────────────┘          └───────────────┘         └───────────┘
```

Auth is handled by the gateway; the server only needs network reach to Quickwit (`QW_BASE_URL`).

## Tools

| Tool | Description |
|------|-------------|
| `list_indexes` | List queryable indexes (ids + uris). `with_stats=true` adds doc count + timestamp range. |
| `describe_index` | Stats, timestamp range, and the field schema (`name → type`) for an index. |
| `search_logs` | Search one/many indexes (`idx`, `idx1,idx2`, `idx*`). Time filtering, pagination, field projection, snippets. Defaults to newest-first. |
| `aggregate_logs` | Elasticsearch-style aggregations (`terms`, `date_histogram`, metrics). Returns counts, not documents. |
| `get_query_syntax_help` | Static Quickwit query-language + aggregation cheat sheet (no network call). |

Time arguments (`start` / `end`) accept `now`, relative offsets (`now-1h`, `now-7d`), ISO-8601
(`2026-06-01T12:00:00Z`), or raw epoch seconds.

## Quickstart

### Local (stdio)

```bash
pip install -e .
QW_BASE_URL=http://localhost:7280 MCP_TRANSPORT=stdio python -m quickwit_mcp
```

Need a Quickwit to point at? Use the dev harness (Docker, seeds a `logs-demo` index):

```bash
scripts/dev-quickwit.sh up      # http://localhost:7280
scripts/dev-quickwit.sh down
```

### Remote (streamable-http, Docker)

```bash
docker build -t quickwit-mcp .
docker run -p 8000:8000 -e QW_BASE_URL=http://<quickwit-host>:7280 quickwit-mcp
# MCP endpoint: http://localhost:8000/mcp
```

## Configuration

All via environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `QW_BASE_URL` | _(required)_ | Quickwit base URL, e.g. `http://localhost:7280` |
| `QW_TIMEOUT` | `30` | HTTP request timeout (seconds) |
| `QW_DEFAULT_MAX_HITS` | `100` | Hits returned when a search omits `max_hits` |
| `QW_MAX_HITS_CEILING` | `500` | Hard cap per search; page beyond with `start_offset` |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `MCP_HOST` | `127.0.0.1` | Bind address for streamable-http (use `0.0.0.0` in containers) |
| `MCP_PORT` | `8000` | Port for streamable-http |

## Development

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check .
pytest -q
```

Every change is verified against a live Quickwit via `scripts/dev-quickwit.sh`, not just unit
tests. See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Contributing

Contributions go through Issue → PR → Review → Merge. See [CONTRIBUTING.md](./CONTRIBUTING.md)
and the [ROADMAP](./ROADMAP.md). Good first issues are labelled
[`good first issue`](https://github.com/agarwalvivek29/quickwit-mcp/labels/good%20first%20issue).

## License

[Apache-2.0](./LICENSE)
