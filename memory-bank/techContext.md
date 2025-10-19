# Tech Context

- Python >= 3.10
- UV for dependency and project management (PEP 621 `pyproject.toml`)
- Build backend: Hatchling
- Dependencies: `mcp` (Python MCP SDK), `httpx`, `pydantic`, `structlog`

Notes:
- Using FastMCP (from `mcp.server.fastmcp`) as the primary server API
- CLI tool `mcp` is installed via `mcp[cli]` and used through `uv run --with mcp mcp ...`

## Docker Support

- Docker image based on `python:3.10-slim` for minimal footprint
- UV installed in container for dependency management
- Non-root user (`mcp`, UID 1000) for security
- **HTTP/SSE transport** for network-based communication (default in Docker)
- Single long-running container serves multiple Cursor connections
- Port 8000 exposed for HTTP/SSE endpoint
- Configuration via `.env` file for docker-compose
- Image size optimized via `.dockerignore` (excludes memory-bank, js/, tests, etc.)
- Built-in health checks for monitoring

Additional dependencies for HTTP/SSE:
- `uvicorn>=0.30.0` - ASGI server
- `starlette>=0.37.0` - Web framework (used for SSE transport)

Transport modes:
- **stdio**: Default for direct CLI usage (`mcp-bitbucket`)
- **sse**: Default for Docker (`--transport sse` or `MCP_TRANSPORT=sse`)

Configuration approach:
- Docker: `.env` file with Bitbucket credentials and MCP settings
- Cursor: Simple URL configuration (`http://localhost:8000/sse`)

Deployment:
1. Start container: `docker compose up -d`
2. Configure Cursor: `{"url": "http://localhost:8000/sse"}`
3. Cursor connects to running container via HTTP/SSE

Technical implementation:
- Raw ASGI app for SSE transport (not Starlette routing)
- `SseServerTransport` from `mcp.server.sse` handles protocol
- Routes: `/sse` (GET - SSE connection), `/messages` (POST - client messages)
- Health check endpoint on `/sse` for container monitoring


