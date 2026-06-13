# quickwit-mcp

> 🚧 **Under construction** — bootstrapping toward `v0.0.1`. Track progress in the [issues](https://github.com/agarwalvivek29/quickwit-mcp/issues) and the [ROADMAP](./ROADMAP.md).

A **[Model Context Protocol](https://modelcontextprotocol.io) (MCP) server** that exposes
[Quickwit](https://quickwit.io) log search and aggregations to LLM clients (Claude and others).

It is a thin, stateless, **read-only** translation layer: MCP tool calls → Quickwit REST API
→ trimmed JSON responses. Designed to run remotely over `streamable-http` behind an MCP
gateway, or locally over `stdio` for development.

## Why

Investigating logs through an LLM should be as simple as asking a question. This server gives
an agent the minimal, safe surface it needs — search, aggregate, and discover indexes — without
handing it any destructive capability.

## Status

This project is in bootstrap. The `v0.0.1` MVP scope and the full contribution workflow are
defined in [ROADMAP.md](./ROADMAP.md) and [CONTRIBUTING.md](./CONTRIBUTING.md) (landing via PRs).

## License

[Apache-2.0](./LICENSE)
