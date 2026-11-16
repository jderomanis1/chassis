import asyncio

import pytest

pytest.importorskip("mcp", reason="Install the mcp extra for SDK interoperability")

from mcp import Client
from mcp.client.stdio import StdioServerParameters

from mcp_client import StdioClient

TOOLS = ["create_from_template", "create_record", "list_records", "read_record", "search", "update_record"]


def test_real_stdio_initialize_list_tools_and_clean_shutdown(git_repo):
    with StdioClient(git_repo) as client:
        initialized = client.initialize()
        assert initialized["serverInfo"]["name"] == "Chassis"
        listed = client.request("tools/list")
        assert sorted(tool["name"] for tool in listed["tools"]) == TOOLS
        for tool in listed["tools"]:
            assert tool["inputSchema"]["additionalProperties"] is False
            assert "agent" not in tool["inputSchema"]["properties"]
    assert "Chassis stdio server starting" in "".join(client.stderr_lines)
    assert not (git_repo / ".chassis").exists()


def test_official_sdk_client_connects_to_real_stdio_process(git_repo):
    import os
    import sys

    async def exercise():
        params = StdioServerParameters(command=sys.executable,
            args=["-m", "chassis.mcp_server", "--vault", str(git_repo)],
            env={key: value for key, value in os.environ.items() if key.startswith("CHASSIS_")})
        async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
            listed = await client.list_tools()
            assert sorted(tool.name for tool in listed.tools) == TOOLS
            result = await client.call_tool("read_record", {"id": "venture-acme"})
            assert result.is_error is False
            assert result.structured_content["record"]["id"] == "venture-acme"

    asyncio.run(exercise())
