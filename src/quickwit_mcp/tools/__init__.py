"""MCP tool implementations.

Each tool is a plain async function taking a :class:`~quickwit_mcp.client.QuickwitClient`.
The FastMCP server (#11) registers them, closing over a shared client. Keeping
them client-injected makes them trivial to unit-test without HTTP.
"""
