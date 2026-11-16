"""Optional MCP stdio entry point; core imports require no MCP dependency."""
import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="chassis-mcp", description=__doc__)
    parser.add_argument("--vault", type=Path, default=Path(os.environ.get("CHASSIS_VAULT", ".")))
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    parser.add_argument("--max-request-bytes", type=int,
                        default=os.environ.get("CHASSIS_MCP_MAX_REQUEST_BYTES", str(1024 * 1024)))
    args = parser.parse_args(argv)
    if args.max_request_bytes < 1:
        parser.error("--max-request-bytes must be positive")
    try:
        from chassis.mcp_transport import serve
    except ModuleNotFoundError as exc:
        if exc.name not in {"mcp", "anyio", "mcp_types"}:
            raise
        print('MCP support is not installed. Run: uv sync --extra mcp (or pip install "chassis[mcp]").',
              file=sys.stderr)
        return 1
    logging.basicConfig(level=args.log_level, stream=sys.stderr, format="%(levelname)s %(name)s: %(message)s")
    logger = logging.getLogger(__name__)
    logger.info("Chassis stdio server starting")
    try:
        asyncio.run(serve(args.vault, os.environ.get("CHASSIS_AGENT_ID", "").strip(), args.max_request_bytes))
    except KeyboardInterrupt:
        pass
    except Exception:
        logger.exception("Chassis stdio server failed")
        return 1
    logger.info("Chassis stdio server stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
