"""Bound input before the official SDK parses it; keep child output off the wire."""
import asyncio
import json
import os
from contextlib import asynccontextmanager

import anyio
from mcp import types
from mcp.server.stdio import stdio_server


class WireOutput:
    def __init__(self, stream):
        self.stream, self.lock = stream, anyio.Lock()

    async def write(self, text):
        async with self.lock:
            await self.stream.write(text)
            await self.stream.flush()

    async def flush(self):
        pass  # Each complete frame was already flushed under the same lock.


class RequestLines:
    def __init__(self, reader, writer, limit):
        self.reader, self.writer, self.limit = reader, writer, limit

    async def error(self, rpc_code, message, **data):
        error = {"code": rpc_code, "message": message}
        if data:
            error["data"] = data
        await self.writer.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": error}) + "\n")
        await self.writer.flush()

    async def validate(self, raw):
        try:
            text = raw.decode("utf-8")
            json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
        except (UnicodeError, ValueError):
            await self.error(-32700, "Parse error")
            return None
        try:
            types.jsonrpc_message_adapter.validate_json(text, by_name=False)
        except ValueError:
            await self.error(-32600, "Invalid Request")
            return None
        return text

    async def __aiter__(self):
        buffer, discarded = bytearray(), False
        while chunk := await self.reader.read(65536):
            parts = chunk.split(b"\n")
            for i, part in enumerate(parts):
                if not discarded:
                    if len(buffer) + len(part) > self.limit:
                        buffer.clear()
                        discarded = True
                        await self.error(-32000, "Request exceeds payload limit",
                                         code="payload_too_large", max_bytes=self.limit)
                    else:
                        buffer.extend(part)
                if i < len(parts) - 1:
                    if not discarded and (text := await self.validate(buffer)) is not None:
                        yield text
                    buffer.clear()
                    discarded = False
        if buffer and (text := await self.validate(buffer)) is not None:
            yield text


@asynccontextmanager
async def bounded_stdio(limit):
    # Duplicates preserve the wire while children inherit null stdin and stderr.
    saved_in, saved_out = os.dup(0), os.dup(1)
    pipe, output, transport = None, None, None
    try:
        pipe = os.fdopen(os.dup(saved_in), "rb", buffering=0)
        output = anyio.wrap_file(os.fdopen(os.dup(saved_out), "w", encoding="utf-8"))
        reader = asyncio.StreamReader(limit=65536)
        transport, _ = await asyncio.get_running_loop().connect_read_pipe(
            lambda: asyncio.StreamReaderProtocol(reader), pipe)
        with open(os.devnull, "rb") as empty:
            os.dup2(empty.fileno(), 0)
        os.dup2(2, 1)
        wire = WireOutput(output)
        async with stdio_server(stdin=RequestLines(reader, wire, limit), stdout=wire) as streams:
            yield streams
    finally:
        os.dup2(saved_in, 0)
        os.dup2(saved_out, 1)
        os.close(saved_in)
        os.close(saved_out)
        if transport is not None:
            transport.close()
        elif pipe is not None:
            pipe.close()
        if output is not None:
            await output.aclose()
