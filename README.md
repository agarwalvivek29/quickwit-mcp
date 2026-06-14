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

Pull the published image from GHCR (or `docker build -t quickwit-mcp .` to build locally):

```bash
docker run -p 8000:8000 -e QW_BASE_URL=http://<quickwit-host>:7280 \
  ghcr.io/agarwalvivek29/quickwit-mcp:latest
# MCP endpoint: http://localhost:8000/mcp
```

Images are published to `ghcr.io/agarwalvivek29/quickwit-mcp` (multi-arch: amd64/arm64),
tagged `latest` and by version (`0.0.1`, `0.0`).

### Kubernetes (Helm)

The chart is published to GHCR as an OCI artifact:

```bash
helm install quickwit-mcp oci://ghcr.io/agarwalvivek29/charts/quickwit-mcp \
  --set quickwit.baseUrl=http://quickwit:7280
```

`quickwit.baseUrl` is required. The chart includes a Deployment (both probes →
`/health`), Service, ServiceAccount, optional Ingress and HPA, and a
PodDisruptionBudget. See [`charts/quickwit-mcp/values.yaml`](./charts/quickwit-mcp/values.yaml)
for all options.

## Health endpoints

- `GET /health` — **liveness + readiness** probe: 200 if the process is up. Point both the k8s `livenessProbe` and `readinessProbe` here. Never calls Quickwit.
- `GET /status` — **diagnostic** (always 200, *not* a probe): reports Quickwit reachability for monitoring/alerts.

The probe deliberately does not check Quickwit. Every replica shares the same Quickwit, so a dependency-coupled probe would pull **all** pods from the Service at once when Quickwit blips — a cascading failure that turns a downstream hiccup into a total outage. When Quickwit is down the pods stay in the Service and return their own errors; alert on `/status` instead.

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
| `MCP_STATELESS` | `false` | `true` = no per-session state, so any replica serves any request (horizontal scaling). `false` keeps sessions in-process (single instance / sticky sessions). |

### Scaling: stateless vs stateful

Stateful streamable-http keeps each session (`Mcp-Session-Id`) in the serving process. Behind a
round-robin load balancer with multiple replicas, follow-up requests can land on a replica that
doesn't have the session — so **stateful needs one instance or sticky sessions**. Set
`MCP_STATELESS=true` to make every request independent; then any replica can serve any request.
Our tools are pure request/response, so stateless mode loses nothing. The Helm chart defaults to
stateless (`stateless: true`) since it ships multiple replicas + HPA.

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
