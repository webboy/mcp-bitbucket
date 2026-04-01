# mcp-bitbucket

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)

Python MCP (Model Context Protocol) server for **Bitbucket Cloud** (REST API v2.0), built with [FastMCP](https://github.com/jlowin/fastmcp). It exposes **35 tools** covering repositories, pull requests (including comments, drafts, and pending reviews), branching models, and pipelines — enabling AI clients (Cursor, Claude Code, etc.) to safely automate Bitbucket workflows.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [Docker Usage](#docker-usage-httpsse-transport)
- [Multi-Project Setup](#multi-project-setup)
- [Tools Reference](#tools-reference)
- [Use with AI Clients](#use-with-ai-clients)
- [Debugging with MCP Inspector](#debug-with-mcp-inspector)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [License](#license)

---

## Features

- Full Bitbucket Cloud REST API v2.0 coverage for common workflows
- Two transport modes: **stdio** (for local AI clients) and **SSE/HTTP** (for Docker/remote)
- Draft pull requests and pending (unpublished) comments support
- Cross-repository pending review detection
- Branching model management at both repository and project levels
- Pipeline management: trigger, stop, inspect runs, steps, and logs
- Built-in health check with connectivity validation
- Multi-project support with separate credentials per workspace
- Docker-ready with health checks, resource limits, and non-root user

---

## Requirements

- **Python 3.10+**
- **uv** package manager (`pipx install uv` or follow [uv docs](https://docs.astral.sh/uv/))
- **Bitbucket Cloud** account with one of:
  - App Password (recommended) for `BITBUCKET_USERNAME` / `BITBUCKET_PASSWORD`
  - OAuth token via `BITBUCKET_TOKEN`

### Recommended App Password Scopes

| Scope | Required for |
|-------|-------------|
| `repository:read` | Listing repos, branching models |
| `pullrequest:read` | Reading PRs, comments, diffs, commits |
| `pullrequest:write` | Creating/updating/merging PRs, comments |
| `pipeline:read` | Listing and inspecting pipeline runs |
| `pipeline:write` | Triggering and stopping pipelines |

---

## Installation

```bash
# Clone the repository
git clone https://github.com/webboy/mcp-bitbucket.git
cd mcp-bitbucket

# Install in editable mode
uv pip install -e .
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `mcp[cli]>=1.2.0` | MCP SDK with CLI support |
| `httpx>=0.27` | HTTP client for Bitbucket API |
| `pydantic>=2.7` | Data validation and tool parameter schemas |
| `structlog>=24.1.0` | Structured logging |
| `uvicorn>=0.30.0` | ASGI server for SSE transport |
| `starlette>=0.37.0` | ASGI framework |

---

## Configuration

All configuration is done via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BITBUCKET_URL` | `https://api.bitbucket.org/2.0` | Bitbucket Cloud API base URL |
| `BITBUCKET_TOKEN` | — | OAuth Bearer token (alternative to username/password) |
| `BITBUCKET_USERNAME` | — | Bitbucket username (for App Password auth) |
| `BITBUCKET_PASSWORD` | — | Bitbucket App Password |
| `BITBUCKET_WORKSPACE` | — | Default workspace slug (optional but convenient) |
| `MCP_TRANSPORT` | `stdio` | Transport type: `stdio` or `sse` |
| `MCP_HOST` | `0.0.0.0` | Host to bind SSE server |
| `MCP_PORT` | `9000` | Port for SSE server |
| `FASTMCP_LOG_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

> **Note:** Either `BITBUCKET_TOKEN` **or** `BITBUCKET_USERNAME` + `BITBUCKET_PASSWORD` must be set. The `BITBUCKET_USERNAME` is also required for the `getPendingReviewPRs` tool to identify the current reviewer.

---

## Running the Server

### stdio mode (default)

```bash
BITBUCKET_USERNAME='<user>' \
BITBUCKET_PASSWORD='<app_password>' \
BITBUCKET_WORKSPACE='<workspace>' \
uv run mcp-bitbucket
```

The server uses stdio and waits for an MCP client to connect.

### SSE/HTTP mode

```bash
BITBUCKET_USERNAME='<user>' \
BITBUCKET_PASSWORD='<app_password>' \
BITBUCKET_WORKSPACE='<workspace>' \
uv run mcp-bitbucket --transport sse --port 9000
```

The server starts an HTTP endpoint at `http://0.0.0.0:9000/sse`.

### CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--transport` | `stdio` (or `MCP_TRANSPORT` env) | `stdio` or `sse` |
| `--host` | `0.0.0.0` (or `MCP_HOST` env) | Bind host for SSE |
| `--port` | `9000` (or `MCP_PORT` env) | Bind port for SSE |

---

## Docker Usage (HTTP/SSE Transport)

The MCP server runs in a Docker container using HTTP/SSE transport, allowing a single long-running container that handles multiple client connections.

### Quick Start

1. **Create environment file:**
```bash
cp .env.example .env
# Edit .env with your Bitbucket credentials
```

2. **Build and start the container:**
```bash
docker-compose up -d --build
```

3. **Configure your AI client** (e.g., Cursor `~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "bitbucket": {
      "url": "http://localhost:9000/sse"
    }
  }
}
```

4. **Restart your AI client** — The Bitbucket MCP server should now be available!

### Manual Docker Commands

```bash
# Build the image
docker build -t mcp-bitbucket:latest .

# Run with docker-compose
docker-compose up -d          # Start in background
docker-compose logs -f         # View logs
docker-compose down            # Stop

# Run directly
docker run -d \
  --name mcp-bitbucket \
  -p 9000:9000 \
  -e BITBUCKET_USERNAME=your_username \
  -e BITBUCKET_PASSWORD=your_app_password \
  -e BITBUCKET_WORKSPACE=your_workspace \
  -e MCP_TRANSPORT=sse \
  mcp-bitbucket:latest
```

### Health Check

```bash
curl http://localhost:9000/sse
```

### Container Management

```bash
docker ps | grep mcp-bitbucket   # Check if running
docker logs mcp-bitbucket        # View logs
docker restart mcp-bitbucket     # Restart
docker stop mcp-bitbucket && docker rm mcp-bitbucket  # Stop and remove
```

### Benefits of HTTP/SSE Transport

- **Single container** — one long-running container handles all requests
- **Multiple connections** — clients can connect/reconnect without spawning new containers
- **Better performance** — no container startup overhead per request
- **Easier debugging** — view logs with `docker logs`
- **Health monitoring** — built-in health checks (30s interval)
- **Resource limits** — default 512MB memory limit, 128MB reserved

---

## Multi-Project Setup

Run multiple containers with different Bitbucket credentials for separate projects:

1. **Create project-specific env files:**
```bash
cp .env.project1.example .env.project1
cp .env.project2.example .env.project2
# Edit each with the appropriate credentials
```

2. **Start both containers:**
```bash
docker compose -f docker-compose.project1.yml up -d
docker compose -f docker-compose.project2.yml up -d
```

3. **Configure your AI client with both servers:**
```json
{
  "mcpServers": {
    "bitbucket-project1": {
      "url": "http://localhost:9000/sse"
    },
    "bitbucket-project2": {
      "url": "http://localhost:9001/sse"
    }
  }
}
```

4. **Manage individually:**
```bash
docker compose -f docker-compose.project1.yml down      # Stop project1
docker compose -f docker-compose.project2.yml logs -f    # Logs for project2
```

---

## Tools Reference

All tools return MCP-compatible responses (text content with pretty-printed JSON, or raw text for diffs/logs). Errors are returned as structured `ERROR: <ExceptionType>: <message>` text.

### Health (1 tool)

| Tool | Description |
|------|-------------|
| `health` | Validates configuration and Bitbucket connectivity. Checks credentials and workspace access. |

### Repositories (2 tools)

| Tool | Description |
|------|-------------|
| `listRepositories` | List repositories in a workspace. Filter by name (contains match) and limit results (1–100). |
| `getRepository` | Get full repository details by workspace and repo slug. |

### Pull Requests (17 tools)

| Tool | Description |
|------|-------------|
| `getPullRequests` | List PRs for a repository. Filter by state (`OPEN`, `MERGED`, `DECLINED`, `SUPERSEDED`) and limit. |
| `createPullRequest` | Create a PR with title, description, source/target branches, optional reviewers. Supports `draft=True`. |
| `getPullRequest` | Get a single PR by ID. |
| `updatePullRequest` | Update PR title and/or description. |
| `getPullRequestActivity` | List activity feed (comments, approvals, status changes) for a PR. |
| `approvePullRequest` | Approve a PR as the current user. |
| `unapprovePullRequest` | Remove your approval from a PR. |
| `declinePullRequest` | Decline (close) a PR with an optional message. |
| `mergePullRequest` | Merge a PR with optional commit message and merge strategy (`merge-commit`, `squash`, `fast-forward`). |
| `getPullRequestComments` | List all comments on a PR. |
| `getPullRequestCommits` | List commits included in a PR. |
| `getPullRequestDiff` | Get the unified diff for a PR (raw text). |
| `addPullRequestComment` | Add a comment to a PR. Supports inline file/line comments and pending (draft) comments. |
| `addPendingPullRequestComment` | Add a pending (unpublished) comment to a PR. Shorthand for `addPullRequestComment` with `pending=True`. |
| `publishPendingComments` | Publish all pending comments on a PR. |
| `createDraftPullRequest` | Create a draft PR (shorthand for `createPullRequest` with `draft=True`). |
| `publishDraftPullRequest` | Publish a draft PR (convert to ready for review). |
| `convertTodraft` | Convert an open PR back to draft. |
| `getPendingReviewPRs` | List PRs awaiting your review across all (or specified) repositories in a workspace. Requires `BITBUCKET_USERNAME`. |

### Branching Models (7 tools)

| Tool | Description |
|------|-------------|
| `getRepositoryBranchingModel` | Get the repository-level branching model (effective settings). |
| `getRepositoryBranchingModelSettings` | Get raw repository branching model settings (may inherit from project). |
| `updateRepositoryBranchingModelSettings` | Update repository branching model: development/production branches and branch types. |
| `getEffectiveRepositoryBranchingModel` | Resolve the effective branching model taking project-level inheritance into account. |
| `getProjectBranchingModel` | Get project-level branching model (defaults for repositories). |
| `getProjectBranchingModelSettings` | Get raw project branching model settings. |
| `updateProjectBranchingModelSettings` | Update project branching model: development/production branches and branch types. |

### Pipelines (8 tools)

| Tool | Description |
|------|-------------|
| `listPipelineRuns` | List pipeline runs. Filter by status (`COMPLETED`, `FAILED`, `RUNNING`), target branch, trigger type (`PUSH`, `MANUAL`), and limit. |
| `getPipelineRun` | Get details for a specific pipeline run by UUID. |
| `runPipeline` | Trigger a pipeline run for a target branch/commit with optional pipeline variables. |
| `stopPipeline` | Stop a running pipeline by UUID. |
| `getPipelineSteps` | List all steps for a pipeline run. |
| `getPipelineStep` | Get details for a specific pipeline step. |
| `getPipelineStepLogs` | Get raw logs for a pipeline step (plain text). |

---

## Use with AI Clients

### Cursor (Docker — Recommended)

See [Docker Usage](#docker-usage-httpsse-transport) above. Configure `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "bitbucket": {
      "url": "http://localhost:9000/sse"
    }
  }
}
```

### Cursor / Claude Code (Direct UV — Development)

If the client runs inside the same environment (e.g., Ubuntu/WSL2), use an absolute path to `uv`:
```json
{
  "mcpServers": {
    "bitbucket": {
      "command": "/home/<user>/.local/bin/uv",
      "args": ["run", "--with-editable", "/path/to/mcp-bitbucket", "mcp-bitbucket"],
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

### Cursor on Windows (WSL Bridge)

If Cursor runs on Windows (outside WSL), bridge to WSL:
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

---

## Debug with MCP Inspector

Launch the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) to interactively test tools:

```bash
BITBUCKET_USERNAME='<user>' \
BITBUCKET_PASSWORD='<app_password>' \
BITBUCKET_WORKSPACE='<workspace>' \
uv run --with mcp mcp dev src/app.py --with-editable .
```

Open the printed URL and call tools like `health` and `listRepositories`.

---

## Architecture

```
mcp-bitbucket/
├── src/
│   ├── cli.py                # CLI entry point (argparse, transport selection)
│   ├── app.py                # FastMCP instance for MCP Inspector / dev
│   ├── server.py             # BitbucketMcpServer: tool registry + MCP handlers
│   ├── bitbucket_client.py   # BitbucketClient: thin httpx wrapper over REST v2.0
│   └── config.py             # BitbucketConfig dataclass + env loader
├── Dockerfile                # Python 3.10-slim, non-root user, SSE default
├── docker-compose.yml        # Default single-instance compose
├── docker-compose.project1.yml  # Multi-project compose (port 9000)
├── docker-compose.project2.yml  # Multi-project compose (port 9001)
├── .env.example              # Template for environment variables
├── pyproject.toml            # Project metadata and dependencies (hatchling)
└── LICENSE                   # MIT
```

### Key Components

- **`BitbucketConfig`** — Immutable dataclass holding API URL, credentials, and default workspace. Loaded from environment variables.
- **`BitbucketClient`** — Synchronous HTTP client (httpx) that maps 1:1 to Bitbucket REST API v2.0 endpoints. Supports both token and App Password authentication.
- **`BitbucketMcpServer`** — Registers all 35 tools with FastMCP, wraps each call in error handling (`_safe`), and manages both stdio and SSE transports.
- **`cli.py`** — Entry point that parses CLI arguments, initializes config and server, and runs the selected transport.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No tools visible in client | Ensure the command starts in your environment (use absolute path to `uv`). Set `FASTMCP_LOG_LEVEL=DEBUG`. |
| 401/403 errors | Verify App Password scopes and workspace/repo access. |
| Workspace missing errors | Set `BITBUCKET_WORKSPACE` env var or pass `workspace` argument to tools. |
| Inspector won't connect | Ensure proxy health at `http://localhost:6277/health` returns `{"status":"ok"}`. If bridging from Windows to WSL, enable localhost forwarding. |
| Container not starting | Check `docker logs mcp-bitbucket` for startup errors. Verify `.env` file exists and is populated. |
| `getPendingReviewPRs` fails | Requires `BITBUCKET_USERNAME` to be set (identifies the current reviewer). |

---

## Security

- Treat App Passwords and OAuth tokens as secrets. **Never commit `.env` files** — they are in `.gitignore`.
- The Docker image runs as a **non-root user** (`mcp`, UID 1000).
- Rotate credentials immediately if exposed.
- The server does not store or log credentials.

---

## License

[MIT](LICENSE) — Copyright (c) 2025 Nemanja Milenković
