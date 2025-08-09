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

### Use with Cursor
If Cursor runs inside the same Ubuntu WSL2 environment, prefer an absolute path to `uv` and add editable source to ensure the local tree is used:
```json
{
  "mcpServers": {
    "bitbucket": {
      "command": "/home/nemanja/.local/bin/uv",
      "args": ["run", "--with-editable", "/home/nemanja/projects/mcp/mcp-bitbucket", "mcp-bitbucket"],
      "env": {
        "BITBUCKET_URL": "https://api.bitbucket.org/2.0",
        "BITBUCKET_USERNAME": "<user>",
        "BITBUCKET_PASSWORD": "<app_password>",
        "BITBUCKET_WORKSPACE": "<workspace>",
        "FASTMCP_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```
If Cursor runs on Windows (outside WSL), bridge to WSL via:
```json
{
  "mcpServers": {
    "bitbucket": {
      "command": "wsl",
      "args": [
        "bash", "-lc",
        "cd /home/<user>/projects/mcp/mcp-bitbucket && BITBUCKET_USERNAME='<user>' BITBUCKET_PASSWORD='<app_password>' BITBUCKET_WORKSPACE='<workspace>' /home/<user>/.local/bin/uv run mcp-bitbucket"
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
