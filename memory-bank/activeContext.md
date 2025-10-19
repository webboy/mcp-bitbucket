# Active Context

Current state:
- Server migrated to FastMCP (`FastMCP.tool()`; dual transport support)
- CLI entry `mcp-bitbucket` supports both stdio and SSE transports via `--transport` flag
- Inspector workflow working (`src/app.py` exposes FastMCP instance)
- Verified live against Bitbucket Cloud: repositories and PRs listed successfully
- Docker support with HTTP/SSE transport:
  - `Dockerfile` with Python 3.10-slim, uv, uvicorn, starlette
  - HTTP/SSE transport on port 8000 (default for Docker)
  - `docker-compose.yml` with port mapping and health checks
  - `.env` file for configuration (credentials and MCP settings)
  - `.dockerignore` optimized for build context
  - Single long-running container serves all Cursor connections
  - Raw ASGI implementation for proper SSE transport handling
  - Comprehensive Docker documentation in README.md
  - **Verified working**: No errors, clean logs, all tools available in Cursor

Architecture:
- Stdio transport: For direct CLI usage and development
- SSE transport: For Docker deployment with network-based communication
- Environment-based configuration: `MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT`

Next steps:
- Add examples/tests for key tools (health, PR flows, pipelines)
- Consider adding GitHub Actions workflow for automated Docker builds
- Optional: Add curl-based healthcheck to Dockerfile


