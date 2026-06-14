# Security Policy

## Supported versions

quickwit-mcp is pre-1.0; only the latest released version receives security fixes.

| Version | Supported |
|---------|-----------|
| 0.0.x   | ✅        |

## Reporting a vulnerability

Please report security issues **privately** — do not open a public issue.

- Use [GitHub private vulnerability reporting](https://github.com/agarwalvivek29/quickwit-mcp/security/advisories/new), or
- Email **vivek.agarwal@aspora.com** with details and reproduction steps.

You can expect an acknowledgement within a few days. Once a fix is available we'll coordinate
disclosure and credit you if you wish.

## Scope notes

This server is **read-only** and stateless; it forwards queries to a Quickwit instance you
configure via `QW_BASE_URL`. It does not handle client authentication itself — that is expected
to be provided by the MCP gateway / network in front of it. Reports about how the server handles
or forwards credentials, query injection, or response handling are in scope.
