from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from config import BitbucketConfig, load_config_from_env
from server import BitbucketMcpServer


def main() -> None:
    """Console entry point for the MCP Bitbucket server."""
    parser = argparse.ArgumentParser(description="MCP Bitbucket Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        help="Transport type: stdio for command-line, sse for HTTP/SSE (default: stdio, or MCP_TRANSPORT env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "9000")),
        help="Port for SSE transport (default: 9000, or MCP_PORT env var)",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("MCP_HOST", "0.0.0.0"),
        help="Host for SSE transport (default: 0.0.0.0, or MCP_HOST env var)",
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config = load_config_from_env()
    server = BitbucketMcpServer(config=config)

    try:
        if args.transport == "sse":
            print(f"Starting MCP server on http://{args.host}:{args.port}", file=sys.stderr)
            asyncio.run(server.run_sse(host=args.host, port=args.port))
        else:
            asyncio.run(server.run_stdio())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)


if __name__ == "__main__":
    main()


