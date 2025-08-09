from __future__ import annotations

from config import load_config_from_env
from server import BitbucketMcpServer


# Expose a FastMCP instance for the MCP CLI / Inspector
_bitbucket_server = BitbucketMcpServer(config=load_config_from_env())

# The MCP CLI searches for one of these variable names
app = _bitbucket_server._server  # FastMCP instance
server = app
mcp = app


