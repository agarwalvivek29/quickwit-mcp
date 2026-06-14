# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.1] — 2026-06-14

Initial read-only release.

### Added
- Async Quickwit REST client (Quickwit 0.8): list indexes, index metadata, describe, search.
- MCP tools: `list_indexes`, `describe_index`, `search_logs`, `aggregate_logs`, `get_query_syntax_help`.
- Environment-based configuration; `stdio` and `streamable-http` transports.
- Time-expression parsing (`now`, `now-1h`, ISO-8601, epoch) and response shaping (field projection + hit clamp).
- Dockerfile for streamable-http deployment; CI (Python 3.10–3.12 matrix, coverage, docker build).
- Local dev harness `scripts/dev-quickwit.sh`.
- Documentation: README, CONTRIBUTING, ROADMAP, security & conduct policies.

[Unreleased]: https://github.com/agarwalvivek29/quickwit-mcp/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/agarwalvivek29/quickwit-mcp/releases/tag/v0.0.1
