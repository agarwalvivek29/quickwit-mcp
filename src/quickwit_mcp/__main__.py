"""Entry point: ``python -m quickwit_mcp``.

Runs the MCP server over the transport configured by ``MCP_TRANSPORT``
(``stdio`` for local development, ``streamable-http`` for remote deployment).
"""

from __future__ import annotations

from .config import get_settings
from .server import build_server


def main() -> None:
    settings = get_settings()
    server = build_server(settings)
    server.run(transport=settings.mcp_transport.value)


if __name__ == "__main__":
    main()
