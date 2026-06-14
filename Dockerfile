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

# Liveness: /health returns 200 if the process is up (no Quickwit dependency).
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=4).status==200 else 1)"]

CMD ["python", "-m", "quickwit_mcp"]
