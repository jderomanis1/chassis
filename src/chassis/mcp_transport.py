"""Optional official SDK adapter with bounded, cancellable stdio input."""
import asyncio
import json
import signal
from pathlib import Path

import anyio
from mcp import types
from mcp.server import Server

from chassis.index import FILTER_FIELDS
from chassis.tool_handlers import TOOL_INPUTS, ToolHandlers
from chassis.stdio import bounded_stdio
from chassis.policy import authorize_reader
from chassis.errors import AuthorizationError

DESCRIPTIONS = {
    "list_records": "List working-tree records in ID order; AND exact filters: " + ", ".join(FILTER_FIELDS),
    "read_record": "Read one complete working-tree record by ID, including derived last_activity_at.",
    "search": "Literal, case-insensitive search within title, next_step, and Markdown body.",
    "create_record": "Create a validated record and one attributed Git commit. Omit version and updated_at.",
    "create_from_template": "Create a populated initiative or read-only agent document from a vault template.",
    "update_record": "Update with expected_version; refuse conflicts and human edits; make one attributed commit.",
}


def make_server(handlers: ToolHandlers) -> Server:
    async def list_tools(_context, _params):
        return types.ListToolsResult(tools=[types.Tool(
            name=name, description=DESCRIPTIONS[name], input_schema=model.model_json_schema(),
            output_schema={"type": "object"}, annotations=types.ToolAnnotations(
                read_only_hint=name in {"list_records", "read_record", "search"}, open_world_hint=False))
            for name, model in TOOL_INPUTS.items()])

    async def call_tool(_context, params):
        # Git/SQLite/flock are synchronous. Keep the protocol loop responsive,
        # and let an in-progress transaction finish if the request is cancelled.
        result = await anyio.to_thread.run_sync(handlers.call, params.name, params.arguments)
        return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(result))],
                                    structured_content=result, is_error="error" in result)

    return Server("Chassis", version="0.0.1", on_list_tools=list_tools, on_call_tool=call_tool)


async def serve(root: Path, agent: str, max_bytes: int) -> None:
    if authorize_reader(root, agent) is None:
        raise AuthorizationError("Authentication failed: a valid agent and CHASSIS_AGENT_TOKEN are required")
    server = make_server(ToolHandlers(root, agent))
    loop = asyncio.get_running_loop()
    with anyio.CancelScope() as scope:
        loop.add_signal_handler(signal.SIGTERM, scope.cancel)
        try:
            async with bounded_stdio(max_bytes) as (reader, writer):
                await server.run(reader, writer, server.create_initialization_options())
        finally:
            loop.remove_signal_handler(signal.SIGTERM)
