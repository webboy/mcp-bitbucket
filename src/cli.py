from __future__ import annotations

import asyncio
import logging
import sys

from config import BitbucketConfig, load_config_from_env
from server import BitbucketMcpServer


def main() -> None:
    """Console entry point for the MCP Bitbucket server (stdio)."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    config = load_config_from_env()
    server = BitbucketMcpServer(config=config)

    try:
        asyncio.run(server.run_stdio())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)


if __name__ == "__main__":
    main()


