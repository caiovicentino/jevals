import asyncio

import pytest

pytest.importorskip("mcp")

from jevals.integrations.mcp_server import build_server  # noqa: E402


def test_mcp_server_builds_and_lists_evals():
    # mcp 2.x renamed FastMCP to MCPServer, and list_evals used to build every eval with no
    # arguments, which CustomRubric doesn't allow.
    server = build_server()
    names = {t.name for t in asyncio.run(server.list_tools())}
    assert {"list_evals", "describe_eval", "evaluate", "gate", "docs"} <= names
    assert "custom_rubric" in str(asyncio.run(server.call_tool("list_evals", {})))
