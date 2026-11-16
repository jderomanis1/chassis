"""Official MCP SDK stdio adapter. Business logic lives in tool_handlers."""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import anyio
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from chassis.index import FILTER_FIELDS
from chassis.tool_handlers import TOOL_INPUTS, ToolHandlers

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


async def serve(root: Path, agent: str) -> None:
    server = make_server(ToolHandlers(root, agent))
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="chassis-mcp", description=__doc__)
    parser.add_argument("--vault", type=Path, default=Path(os.environ.get("CHASSIS_VAULT", ".")))
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level, stream=sys.stderr, format="%(levelname)s %(name)s: %(message)s")
    logger = logging.getLogger(__name__)
    logger.info("Chassis stdio server starting")
    try:
        asyncio.run(serve(args.vault, os.environ.get("CHASSIS_AGENT_ID", "").strip()))
    except KeyboardInterrupt:
        pass
    except Exception:
        logger.exception("Chassis stdio server failed")
        return 1
    logger.info("Chassis stdio server stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
