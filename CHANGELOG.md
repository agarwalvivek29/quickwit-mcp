# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `MCP_STATELESS` setting (and Helm `stateless` value, default true) — runs streamable-http without per-session state so any replica can serve any request. Required for horizontal scaling behind a round-robin Service; stateful mode (default for the binary) needs a single instance or sticky sessions.
- Helm chart (`charts/quickwit-mcp`): Deployment (both probes → `/health`, non-root + read-only-rootfs securityContext, resources), Service, ServiceAccount, optional Ingress and HPA (autoscaling/v2), and a PodDisruptionBudget. Published to GHCR as an OCI artifact (`oci://ghcr.io/agarwalvivek29/charts/quickwit-mcp`) on release; linted/rendered in CI.

## [0.0.3] — 2026-06-14

### Added
- `GET /status` — diagnostic (always 200) reporting Quickwit reachability for monitoring.

### Changed
- `GET /health` is now liveness **and** readiness (200 if the process is up; **no Quickwit call**). Point both k8s probes here. This replaces the 0.0.2 behavior where `/health` checked Quickwit — coupling a probe to a shared dependency would pull every replica from the Service at once when Quickwit blips (cascading failure). The Docker `HEALTHCHECK` uses `/health`.

## [0.0.2] — 2026-06-14

### Added
- `GET /health` readiness endpoint — returns 200 when Quickwit is reachable, 503 otherwise. The Docker `HEALTHCHECK` now uses it instead of a TCP-only check.

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

[Unreleased]: https://github.com/agarwalvivek29/quickwit-mcp/compare/v0.0.3...HEAD
[0.0.3]: https://github.com/agarwalvivek29/quickwit-mcp/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/agarwalvivek29/quickwit-mcp/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/agarwalvivek29/quickwit-mcp/releases/tag/v0.0.1
