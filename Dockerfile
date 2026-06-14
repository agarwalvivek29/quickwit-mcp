# quickwit-mcp — streamable-http MCP server image.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the package (build needs pyproject, source, and the README it references).
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

# Serve streamable-http on all interfaces so the published port is reachable.
ENV MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000
EXPOSE 8000

# Liveness: the server is up if it's accepting TCP connections on the port.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import socket,sys; s=socket.socket(); s.settimeout(2); sys.exit(s.connect_ex(('127.0.0.1',8000)))"]

CMD ["python", "-m", "quickwit_mcp"]
