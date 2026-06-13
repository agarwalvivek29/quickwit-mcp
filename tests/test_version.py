"""Smoke test: the package imports and exposes a version.

Keeps `pytest` collecting cleanly until real tests land in later issues.
"""

import quickwit_mcp


def test_version() -> None:
    assert quickwit_mcp.__version__ == "0.0.1"
