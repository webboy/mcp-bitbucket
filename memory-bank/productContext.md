# Product Context

## Why This Exists
This MCP server bridges Bitbucket Cloud with AI assistants like Cursor, enabling developers to interact with Bitbucket through natural language commands instead of manual UI navigation or API calls.

## Problems It Solves
1. **Manual PR Reviews**: Instead of opening Bitbucket UI, developers can ask "show me PR 2424" or "list my pending reviews"
2. **Workflow Automation**: AI can help create PRs, add comments, approve/merge, and manage branching
3. **Context Switching**: Reduces need to leave the IDE to interact with Bitbucket
4. **Deployment Flexibility**: Runs either natively (stdio) or in Docker (HTTP/SSE)

## How It Works
- **Native Mode**: Runs as CLI tool with stdio transport for direct integration
- **Docker Mode**: Runs as HTTP/SSE server in container for isolated, reproducible deployment
- Exposes 36+ tools covering repos, PRs, comments, pipelines, and branching models
- Uses Bitbucket REST API v2 with username/password or OAuth token authentication

## User Experience Goals
- **Zero friction**: Single URL configuration in Cursor for Docker mode
- **Self-service**: Start container with `docker compose up -d`, connect immediately
- **Transparent**: Works through MCP protocol - users interact via natural language
- **Reliable**: One container handles all connections, auto-restarts on failure

Provide an MCP server to enable AI assistants (e.g., Cursor) to interact with Bitbucket Cloud. The server exposes safe read/write operations for PRs, comments, branching configs, and pipelines, using Bitbucket REST v2.


