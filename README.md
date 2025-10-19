## mcp-bitbucket
Python MCP server for Bitbucket Cloud (REST v2), built with FastMCP. It exposes tools for repositories, pull requests (incl. comments, drafts), branching models, and pipelines so AI clients (e.g., Cursor) can safely automate workflows.

### Requirements
- Python 3.10+
- uv (`pipx install uv` or follow uv docs)
- Bitbucket Cloud account with either:
  - App Password (recommended) for `BITBUCKET_USERNAME`/`BITBUCKET_PASSWORD`, or
  - OAuth token via `BITBUCKET_TOKEN`

Recommended scopes for App Password (adjust to your needs):
- repository:read, pullrequest:read, pullrequest:write
- pipeline:read, pipeline:write (if you will use pipelines tools)

### Install (editable)
```bash
uv pip install -e .
```

### Docker Usage (HTTP/SSE Transport)

The MCP server runs in a Docker container using HTTP/SSE transport, allowing a single long-running container that handles multiple Cursor connections.

#### Quick Start

1. **Create environment file:**
```bash
cp .env.example .env
# Edit .env with your Bitbucket credentials
```

2. **Build and start the container:**
```bash
docker-compose up -d --build
```

3. **Configure Cursor** (`~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "bitbucket": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

4. **Restart Cursor** - The Bitbucket MCP server should now be available!

#### Manual Docker Commands

**Build the image:**
```bash
docker build -t mcp-bitbucket:latest .
```

**Run with docker-compose:**
```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Run with docker directly:**
```bash
docker run -d \
  --name mcp-bitbucket \
  -p 8000:8000 \
  -e BITBUCKET_USERNAME=your_username \
  -e BITBUCKET_PASSWORD=your_app_password \
  -e BITBUCKET_WORKSPACE=your_workspace \
  -e MCP_TRANSPORT=sse \
  mcp-bitbucket:latest
```

#### Health Check

Verify the server is running:
```bash
curl http://localhost:8000/sse
```

#### Container Management

```bash
# Check if running
docker ps | grep mcp-bitbucket

# View logs
docker logs mcp-bitbucket

# Restart
docker restart mcp-bitbucket

# Stop and remove
docker stop mcp-bitbucket
docker rm mcp-bitbucket
```

#### Benefits of HTTP/SSE Transport

- **Single container**: One long-running container handles all requests
- **Multiple connections**: Cursor can connect/reconnect without spawning new containers
- **Better performance**: No container startup overhead per request
- **Easier debugging**: View logs with `docker logs`
- **Health monitoring**: Built-in health checks

### Configuration
Environment variables:
- BITBUCKET_URL: defaults to `https://api.bitbucket.org/2.0`
- BITBUCKET_TOKEN: OAuth token (optional, alternative to username/password)
- BITBUCKET_USERNAME / BITBUCKET_PASSWORD: Bitbucket username + App Password
- BITBUCKET_WORKSPACE: default workspace slug (optional but convenient)
- FASTMCP_LOG_LEVEL: DEBUG|INFO|... (optional)

### Run (stdio server)
```bash
BITBUCKET_USERNAME='<user>' \
BITBUCKET_PASSWORD='<app_password>' \
BITBUCKET_WORKSPACE='<workspace>' \
uv run mcp-bitbucket
```
The server uses stdio and prints little until a client connects.

### Debug with MCP Inspector
Expose a FastMCP instance via `src/app.py` and launch the Inspector:
```bash
BITBUCKET_USERNAME='<user>' \
BITBUCKET_PASSWORD='<app_password>' \
BITBUCKET_WORKSPACE='<workspace>' \
uv run --with mcp mcp dev src/app.py --with-editable .
```
Open the printed URL and call tools like `health` and `listRepositories`.

### Use with Cursor (Native/Development)

#### Option 1: Docker (Recommended for Production)
See [Docker Usage](#docker-usage) section above.

#### Option 2: Direct UV (for Development)
If Cursor runs inside the same Ubuntu WSL2 environment, prefer an absolute path to `uv` and add editable source to ensure the local tree is used:
```json
{
  "mcpServers": {
    "bitbucket": {
      "command": "/home/nemanja/.local/bin/uv",
      "args": ["run", "--with-editable", "/home/nemanja/projects/mcp/mcp-bitbucket", "mcp-bitbucket"],
      "env": {
        "BITBUCKET_URL": "https://api.bitbucket.org/2.0",
        "BITBUCKET_USERNAME": "your_username",
        "BITBUCKET_PASSWORD": "your_app_password",
        "BITBUCKET_WORKSPACE": "your_workspace",
        "FASTMCP_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

#### Option 3: WSL Bridge (Windows)
If Cursor runs on Windows (outside WSL), bridge to WSL via:
```json
{
  "mcpServers": {
    "bitbucket": {
      "command": "wsl",
      "args": [
        "bash", "-lc",
        "cd /home/<user>/projects/mcp/mcp-bitbucket && BITBUCKET_USERNAME='your_username' BITBUCKET_PASSWORD='your_app_password' BITBUCKET_WORKSPACE='your_workspace' /home/<user>/.local/bin/uv run mcp-bitbucket"
      ]
    }
  }
}
```

### Tools (high-level)
- health
- listRepositories, getRepository
- getPullRequests, createPullRequest, getPullRequest, updatePullRequest, getPullRequestActivity,
  approvePullRequest, unapprovePullRequest, declinePullRequest, mergePullRequest,
  getPullRequestComments, getPullRequestCommits, getPullRequestDiff,
  addPullRequestComment, addPendingPullRequestComment, publishPendingComments,
  createDraftPullRequest, publishDraftPullRequest, convertTodraft,
  getPendingReviewPRs (requires `BITBUCKET_USERNAME` to identify current reviewer)
- Branching model: get/update at repo and project levels; resolve effective repo model
- Pipelines: list runs, get run, run pipeline, stop run, list/get step(s), step logs

All tools return MCP-compatible responses (text content with pretty-printed JSON, or raw text for diffs/logs).

### Troubleshooting
- No tools in client: ensure the command actually starts in your environment (absolute path to `uv` helps). Add `FASTMCP_LOG_LEVEL=DEBUG`.
- 401/403: verify App Password scopes and workspace/repo access.
- Workspace missing: set `BITBUCKET_WORKSPACE` or pass `workspace` argument to tools.
- Inspector won’t connect: ensure proxy health at `http://localhost:6277/health` returns `{ "status": "ok" }`. If bridging from Windows to WSL, enable localhost forwarding in WSL.

### Security
Treat App Passwords and tokens as secrets. Rotate if exposed.
