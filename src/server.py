from __future__ import annotations

import json
from typing import Any, Dict, Optional, Callable, Annotated
from pydantic import Field

import structlog
from mcp.server.fastmcp import FastMCP

from bitbucket_client import BitbucketClient
from config import BitbucketConfig


logger = structlog.get_logger(__name__)


class BitbucketMcpServer:
    """MCP server and tool registry for Bitbucket."""

    def __init__(self, config: BitbucketConfig) -> None:
        self._config = config
        if not (config.token or (config.username and config.password)):
            raise RuntimeError(
                "Either BITBUCKET_TOKEN or BITBUCKET_USERNAME/PASSWORD must be provided"
            )
        self._client = BitbucketClient(config)
        self._server = FastMCP(name="mcp-bitbucket")
        self._register_tools()

    def _register_tools(self) -> None:
        s = self._server

        @s.tool()
        def listRepositories(
            workspace: Annotated[Optional[str], Field(description="Bitbucket workspace slug. Uses BITBUCKET_WORKSPACE when omitted.")] = None,
            limit: Annotated[int, Field(description="Maximum number of repositories to return.", ge=1, le=100)] = 10,
            name: Annotated[Optional[str], Field(description="Filter repositories whose name contains this string.")] = None,
        ) -> Dict[str, Any]:
            """List repositories in a workspace. Optionally filter by `name` (contains) and limit results."""
            return self._safe(lambda: self.tool_list_repositories(workspace=workspace, limit=limit, name=name))

        @s.tool()
        def getRepository(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug (short name)")],
        ) -> Dict[str, Any]:
            """Get repository details by `workspace` and `repo_slug`."""
            return self._safe(lambda: self.tool_get_repository(workspace=workspace, repo_slug=repo_slug))

        @s.tool()
        def getPullRequests(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            state: Annotated[Optional[str], Field(description="Filter by PR state: OPEN, MERGED, DECLINED, SUPERSEDED")] = None,
            limit: Annotated[int, Field(description="Maximum number of pull requests to return.", ge=1, le=100)] = 10,
        ) -> Dict[str, Any]:
            """List pull requests for a repository. Optionally filter by `state` and limit results."""
            return self._safe(lambda: self.tool_get_pull_requests(workspace=workspace, repo_slug=repo_slug, state=state, limit=limit))

        @s.tool()
        def createPullRequest(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            title: Annotated[str, Field(description="Pull request title")],
            description: Annotated[str, Field(description="Pull request description/body")],
            sourceBranch: Annotated[str, Field(description="Source branch name (feature branch)")],
            targetBranch: Annotated[str, Field(description="Target branch name (e.g., main)")],
            reviewers: Annotated[Optional[list[str]], Field(description="Optional list of reviewers (usernames or account IDs), if supported")] = None,
            draft: Annotated[Optional[bool], Field(description="Create as draft PR when True")] = None,
        ) -> Dict[str, Any]:
            """Create a pull request. Set `draft=True` to create a draft PR when supported."""
            return self._safe(lambda: self.tool_create_pull_request(workspace=workspace, repo_slug=repo_slug, title=title, description=description, sourceBranch=sourceBranch, targetBranch=targetBranch, reviewers=reviewers, draft=draft))

        @s.tool()
        def getPullRequest(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
        ) -> Dict[str, Any]:
            """Get a pull request by ID."""
            return self._safe(lambda: self.tool_get_pull_request(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id))

        @s.tool()
        def updatePullRequest(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
            title: Annotated[Optional[str], Field(description="New title")] = None,
            description: Annotated[Optional[str], Field(description="New description/body")] = None,
        ) -> Dict[str, Any]:
            """Update a pull request's title and/or description."""
            return self._safe(lambda: self.tool_update_pull_request(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id, title=title, description=description))

        @s.tool()
        def getPullRequestActivity(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
        ) -> Dict[str, Any]:
            """List activity (comments, approvals, updates) for a pull request."""
            return self._safe(lambda: self.tool_get_pull_request_activity(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id))

        @s.tool()
        def approvePullRequest(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
        ) -> Dict[str, Any]:
            """Approve a pull request as the current user."""
            return self._safe(lambda: self.tool_approve_pull_request(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id))

        @s.tool()
        def unapprovePullRequest(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
        ) -> Dict[str, Any]:
            """Remove your approval from a pull request."""
            return self._safe(lambda: self.tool_unapprove_pull_request(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id))

        @s.tool()
        def declinePullRequest(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
            message: Annotated[Optional[str], Field(description="Optional decline message")] = None,
        ) -> Dict[str, Any]:
            """Decline (close) a pull request. Optionally provide a message."""
            return self._safe(lambda: self.tool_decline_pull_request(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id, message=message))

        @s.tool()
        def mergePullRequest(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
            message: Annotated[Optional[str], Field(description="Optional merge commit message")] = None,
            strategy: Annotated[Optional[str], Field(description="Merge strategy (merge-commit, squash, fast-forward)")] = None,
        ) -> Dict[str, Any]:
            """Merge a pull request. Optionally set a commit `message` and merge `strategy`."""
            return self._safe(lambda: self.tool_merge_pull_request(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id, message=message, strategy=strategy))

        @s.tool()
        def getPullRequestComments(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
        ) -> Dict[str, Any]:
            """List comments for a pull request."""
            return self._safe(lambda: self.tool_get_pull_request_comments(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id))

        @s.tool()
        def getPullRequestCommits(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
        ) -> Dict[str, Any]:
            """List commits included in a pull request."""
            return self._safe(lambda: self.tool_get_pull_request_commits(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id))

        @s.tool()
        def getPullRequestDiff(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
        ) -> Dict[str, Any]:
            """Get unified diff for a pull request."""
            return self._safe(lambda: self.tool_get_pull_request_diff(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id))

        @s.tool()
        def addPullRequestComment(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
            content: Annotated[str, Field(description="Comment text content")],
            inline: Annotated[Optional[dict], Field(description="Inline context for file/line comments (file path, line numbers)")] = None,
            pending: Annotated[Optional[bool], Field(description="When True, keep the comment as pending/draft if supported")] = None,
        ) -> Dict[str, Any]:
            """Add a comment to a pull request. Set `inline` for file/line comments; set `pending=True` to keep as draft."""
            return self._safe(lambda: self.tool_add_pull_request_comment(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id, content=content, inline=inline, pending=pending))

        @s.tool()
        def addPendingPullRequestComment(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
            content: Annotated[str, Field(description="Comment text content")],
            inline: Annotated[Optional[dict], Field(description="Inline context for file/line comments (file path, line numbers)")] = None,
        ) -> Dict[str, Any]:
            """Add a pending (unpublished) comment to a pull request. Equivalent to `pending=True`."""
            return self._safe(lambda: self.tool_add_pending_pull_request_comment(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id, content=content, inline=inline))

        @s.tool()
        def publishPendingComments(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
        ) -> Dict[str, Any]:
            """Publish all pending comments on a pull request."""
            return self._safe(lambda: self.tool_publish_pending_comments(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id))

        @s.tool()
        def createDraftPullRequest(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            title: Annotated[str, Field(description="Pull request title")],
            description: Annotated[str, Field(description="Pull request description/body")],
            sourceBranch: Annotated[str, Field(description="Source branch name (feature branch)")],
            targetBranch: Annotated[str, Field(description="Target branch name (e.g., main)")],
            reviewers: Annotated[Optional[list[str]], Field(description="Optional list of reviewers (usernames or account IDs), if supported")] = None,
        ) -> Dict[str, Any]:
            """Create a draft pull request."""
            return self._safe(lambda: self.tool_create_draft_pull_request(workspace=workspace, repo_slug=repo_slug, title=title, description=description, sourceBranch=sourceBranch, targetBranch=targetBranch, reviewers=reviewers))

        @s.tool()
        def publishDraftPullRequest(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
        ) -> Dict[str, Any]:
            """Publish a draft pull request (convert to ready for review)."""
            return self._safe(lambda: self.tool_publish_draft_pull_request(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id))

        @s.tool()
        def convertTodraft(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pull_request_id: Annotated[str, Field(description="Pull request ID")],
        ) -> Dict[str, Any]:
            """Convert an open pull request to draft."""
            return self._safe(lambda: self.tool_convert_to_draft(workspace=workspace, repo_slug=repo_slug, pull_request_id=pull_request_id))

        @s.tool()
        def getPendingReviewPRs(
            workspace: Annotated[Optional[str], Field(description="Bitbucket workspace slug. Uses BITBUCKET_WORKSPACE when omitted.")] = None,
            limit: Annotated[int, Field(description="Maximum number of pull requests to return.", ge=1, le=100)] = 50,
            repositoryList: Annotated[Optional[list[str]], Field(description="Optional list of repository slugs to limit the search to")] = None,
        ) -> Dict[str, Any]:
            """List PRs awaiting your review across repositories in a workspace."""
            return self._safe(lambda: self.tool_get_pending_review_prs(workspace=workspace, limit=limit, repositoryList=repositoryList))

        # Branching models
        @s.tool()
        def getRepositoryBranchingModel(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
        ) -> Dict[str, Any]:
            """Get repository-level branching model (effective settings)."""
            return self._safe(lambda: self.tool_get_repository_branching_model(workspace=workspace, repo_slug=repo_slug))

        @s.tool()
        def getRepositoryBranchingModelSettings(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
        ) -> Dict[str, Any]:
            """Get repository branching model settings (raw, may inherit from project)."""
            return self._safe(lambda: self.tool_get_repository_branching_model_settings(workspace=workspace, repo_slug=repo_slug))

        @s.tool()
        def updateRepositoryBranchingModelSettings(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            development: Annotated[Optional[dict], Field(description="Development branch settings payload")] = None,
            production: Annotated[Optional[dict], Field(description="Production branch settings payload")] = None,
            branch_types: Annotated[Optional[list], Field(description="Branch types configuration list")] = None,
        ) -> Dict[str, Any]:
            """Update repository branching model settings."""
            return self._safe(lambda: self.tool_update_repository_branching_model_settings(workspace=workspace, repo_slug=repo_slug, development=development, production=production, branch_types=branch_types))

        @s.tool()
        def getEffectiveRepositoryBranchingModel(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
        ) -> Dict[str, Any]:
            """Resolve the effective repository branching model (taking inheritance into account)."""
            return self._safe(lambda: self.tool_get_effective_repository_branching_model(workspace=workspace, repo_slug=repo_slug))

        @s.tool()
        def getProjectBranchingModel(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            project_key: Annotated[str, Field(description="Project key (e.g., ABC)")],
        ) -> Dict[str, Any]:
            """Get project-level branching model (defaults for repositories)."""
            return self._safe(lambda: self.tool_get_project_branching_model(workspace=workspace, project_key=project_key))

        @s.tool()
        def getProjectBranchingModelSettings(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            project_key: Annotated[str, Field(description="Project key")],
        ) -> Dict[str, Any]:
            """Get project branching model settings (raw)."""
            return self._safe(lambda: self.tool_get_project_branching_model_settings(workspace=workspace, project_key=project_key))

        @s.tool()
        def updateProjectBranchingModelSettings(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            project_key: Annotated[str, Field(description="Project key")],
            development: Annotated[Optional[dict], Field(description="Development branch settings payload")] = None,
            production: Annotated[Optional[dict], Field(description="Production branch settings payload")] = None,
            branch_types: Annotated[Optional[list], Field(description="Branch types configuration list")] = None,
        ) -> Dict[str, Any]:
            """Update project branching model settings."""
            return self._safe(lambda: self.tool_update_project_branching_model_settings(workspace=workspace, project_key=project_key, development=development, production=production, branch_types=branch_types))

        # Pipelines
        @s.tool()
        def listPipelineRuns(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            limit: Annotated[Optional[int], Field(description="Maximum number of pipeline runs to return.", ge=1, le=100)] = None,
            status: Annotated[Optional[str], Field(description="Filter by pipeline status (e.g., COMPLETED, FAILED, RUNNING)")] = None,
            target_branch: Annotated[Optional[str], Field(description="Filter by target branch name")] = None,
            trigger_type: Annotated[Optional[str], Field(description="Filter by trigger type (e.g., PUSH, MANUAL)")] = None,
        ) -> Dict[str, Any]:
            """List pipeline runs for a repository. Filter by status, branch, trigger type, and limit."""
            return self._safe(lambda: self.tool_list_pipeline_runs(workspace=workspace, repo_slug=repo_slug, limit=limit, status=status, target_branch=target_branch, trigger_type=trigger_type))

        @s.tool()
        def getPipelineRun(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pipeline_uuid: Annotated[str, Field(description="Pipeline UUID")],
        ) -> Dict[str, Any]:
            """Get details for a specific pipeline run."""
            return self._safe(lambda: self.tool_get_pipeline_run(workspace=workspace, repo_slug=repo_slug, pipeline_uuid=pipeline_uuid))

        @s.tool()
        def runPipeline(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            target: Annotated[dict, Field(description="Target object specifying branch/commit to run against")],
            variables: Annotated[Optional[list[dict]], Field(description="Optional list of pipeline variables {key, value}")] = None,
        ) -> Dict[str, Any]:
            """Trigger a pipeline run for a target (branch/commit) with optional variables."""
            return self._safe(lambda: self.tool_run_pipeline(workspace=workspace, repo_slug=repo_slug, target=target, variables=variables))

        @s.tool()
        def stopPipeline(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pipeline_uuid: Annotated[str, Field(description="Pipeline UUID")],
        ) -> Dict[str, Any]:
            """Stop a running pipeline."""
            return self._safe(lambda: self.tool_stop_pipeline(workspace=workspace, repo_slug=repo_slug, pipeline_uuid=pipeline_uuid))

        @s.tool()
        def getPipelineSteps(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pipeline_uuid: Annotated[str, Field(description="Pipeline UUID")],
        ) -> Dict[str, Any]:
            """List steps for a pipeline run."""
            return self._safe(lambda: self.tool_get_pipeline_steps(workspace=workspace, repo_slug=repo_slug, pipeline_uuid=pipeline_uuid))

        @s.tool()
        def getPipelineStep(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pipeline_uuid: Annotated[str, Field(description="Pipeline UUID")],
            step_uuid: Annotated[str, Field(description="Step UUID")],
        ) -> Dict[str, Any]:
            """Get details for a pipeline step."""
            return self._safe(lambda: self.tool_get_pipeline_step(workspace=workspace, repo_slug=repo_slug, pipeline_uuid=pipeline_uuid, step_uuid=step_uuid))

        @s.tool()
        def getPipelineStepLogs(
            workspace: Annotated[str, Field(description="Bitbucket workspace slug")],
            repo_slug: Annotated[str, Field(description="Repository slug")],
            pipeline_uuid: Annotated[str, Field(description="Pipeline UUID")],
            step_uuid: Annotated[str, Field(description="Step UUID")],
        ) -> Dict[str, Any]:
            """Get raw logs for a pipeline step."""
            return self._safe(lambda: self.tool_get_pipeline_step_logs(workspace=workspace, repo_slug=repo_slug, pipeline_uuid=pipeline_uuid, step_uuid=step_uuid))

        @s.tool()
        def health(
            workspace: Annotated[Optional[str], Field(description="Bitbucket workspace slug. Uses BITBUCKET_WORKSPACE when omitted.")] = None,
        ) -> Dict[str, Any]:
            """Health check: validates configuration and Bitbucket connectivity (optionally for a given workspace)."""
            return self.tool_health(workspace=workspace)

    async def run_stdio(self) -> None:
        """Run server with stdio transport."""
        await self._server.run_stdio_async()

    async def run_sse(self, host: str = "0.0.0.0", port: int = 9000) -> None:
        """Run server with SSE (HTTP) transport."""
        from mcp.server.sse import SseServerTransport
        import uvicorn

        sse = SseServerTransport("/messages")

        async def app(scope, receive, send):
            """ASGI application that routes SSE requests."""
            if scope["type"] == "http":
                path = scope["path"]
                method = scope["method"]
                
                if path == "/sse" and method == "GET":
                    # Handle SSE connection
                    async with sse.connect_sse(scope, receive, send) as streams:
                        await self._server._mcp_server.run(
                            streams[0], streams[1], self._server._mcp_server.create_initialization_options()
                        )
                elif path == "/messages" and method == "POST":
                    # Handle POST messages
                    await sse.handle_post_message(scope, receive, send)
                else:
                    # 404 for other paths
                    await send({
                        "type": "http.response.start",
                        "status": 404,
                        "headers": [[b"content-type", b"text/plain"]],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": b"Not Found",
                    })

        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    def _safe(self, func: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a tool function and convert any exception into a consistent MCP text response.

        Returns a dict of the MCP ToolResponse shape: {"content": [{"type": "text", "text": str}]}.
        """
        try:
            return func()
        except Exception as exc:  # noqa: BLE001 - propagate as user-friendly text
            logger.exception("Tool execution failed")
            return {"content": [{"type": "text", "text": f"ERROR: {type(exc).__name__}: {exc}"}]}

    def tool_health(self, *, workspace: Optional[str]) -> Dict[str, Any]:
        """Health check implementation used by the `health` tool.

        - Verifies minimal configuration is present
        - Resolves workspace (param or default)
        - Performs a light API call (list repositories, limit=1)
        """
        ws = workspace or self._config.default_workspace
        details: Dict[str, Any] = {
            "hasToken": bool(self._config.token),
            "hasUser": bool(self._config.username),
            "workspaceResolved": ws if ws else None,
        }

        if not ws:
            details["connectivity"] = False
            details["message"] = "Workspace not provided and BITBUCKET_WORKSPACE not set"
            return {"content": [{"type": "text", "text": json.dumps({"status": "error", "details": details}, indent=2)}]}

        try:
            # Light-weight call to validate credentials and access
            _ = self._client.list_repositories(ws, limit=1)
            details["connectivity"] = True
            return {"content": [{"type": "text", "text": json.dumps({"status": "ok", "details": details}, indent=2)}]}
        except Exception as exc:  # noqa: BLE001 - include error context for operators
            details["connectivity"] = False
            details["error"] = f"{type(exc).__name__}: {exc}"
            return {"content": [{"type": "text", "text": json.dumps({"status": "error", "details": details}, indent=2)}]}

    # ---------------- Repository tools ----------------
    def tool_list_repositories(self, *, workspace: Optional[str], limit: int = 10, name: Optional[str] = None) -> Dict[str, Any]:
        ws = workspace or self._config.default_workspace
        if not ws:
            raise ValueError("Workspace must be provided or set via BITBUCKET_WORKSPACE")
        items = self._client.list_repositories(ws, limit=limit, name=name)
        return {"content": [{"type": "text", "text": json.dumps(items, indent=2)}]}

    def tool_get_repository(self, *, workspace: str, repo_slug: str) -> Dict[str, Any]:
        data = self._client.get_repository(workspace, repo_slug)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    # ---------------- Pull request tools ----------------
    def tool_get_pull_requests(self, *, workspace: str, repo_slug: str, state: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        items = self._client.get_pull_requests(workspace, repo_slug, state=state, limit=limit)
        return {"content": [{"type": "text", "text": json.dumps(items, indent=2)}]}

    def tool_create_pull_request(
        self,
        *,
        workspace: str,
        repo_slug: str,
        title: str,
        description: str,
        sourceBranch: str,
        targetBranch: str,
        reviewers: Optional[list[str]] = None,
        draft: Optional[bool] = None,
    ) -> Dict[str, Any]:
        data = self._client.create_pull_request(
            workspace,
            repo_slug,
            title,
            description,
            source_branch=sourceBranch,
            target_branch=targetBranch,
            reviewers=reviewers,
            draft=draft,
        )
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_get_pull_request(self, *, workspace: str, repo_slug: str, pull_request_id: str) -> Dict[str, Any]:
        data = self._client.get_pull_request(workspace, repo_slug, pull_request_id)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_update_pull_request(self, *, workspace: str, repo_slug: str, pull_request_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        data = self._client.update_pull_request(workspace, repo_slug, pull_request_id, title=title, description=description)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_get_pull_request_activity(self, *, workspace: str, repo_slug: str, pull_request_id: str) -> Dict[str, Any]:
        items = self._client.get_pull_request_activity(workspace, repo_slug, pull_request_id)
        return {"content": [{"type": "text", "text": json.dumps(items, indent=2)}]}

    def tool_approve_pull_request(self, *, workspace: str, repo_slug: str, pull_request_id: str) -> Dict[str, Any]:
        data = self._client.approve_pull_request(workspace, repo_slug, pull_request_id)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_unapprove_pull_request(self, *, workspace: str, repo_slug: str, pull_request_id: str) -> Dict[str, Any]:
        self._client.unapprove_pull_request(workspace, repo_slug, pull_request_id)
        return {"content": [{"type": "text", "text": "Pull request approval removed successfully."}]}

    def tool_decline_pull_request(self, *, workspace: str, repo_slug: str, pull_request_id: str, message: Optional[str] = None) -> Dict[str, Any]:
        data = self._client.decline_pull_request(workspace, repo_slug, pull_request_id, message=message)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_merge_pull_request(self, *, workspace: str, repo_slug: str, pull_request_id: str, message: Optional[str] = None, strategy: Optional[str] = None) -> Dict[str, Any]:
        data = self._client.merge_pull_request(workspace, repo_slug, pull_request_id, message=message, strategy=strategy)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_get_pull_request_comments(self, *, workspace: str, repo_slug: str, pull_request_id: str) -> Dict[str, Any]:
        items = self._client.get_pull_request_comments(workspace, repo_slug, pull_request_id)
        return {"content": [{"type": "text", "text": json.dumps(items, indent=2)}]}

    def tool_get_pull_request_commits(self, *, workspace: str, repo_slug: str, pull_request_id: str) -> Dict[str, Any]:
        items = self._client.get_pull_request_commits(workspace, repo_slug, pull_request_id)
        return {"content": [{"type": "text", "text": json.dumps(items, indent=2)}]}

    def tool_get_pull_request_diff(self, *, workspace: str, repo_slug: str, pull_request_id: str) -> Dict[str, Any]:
        text = self._client.get_pull_request_diff(workspace, repo_slug, pull_request_id)
        return {"content": [{"type": "text", "text": text}]}

    def tool_add_pull_request_comment(self, *, workspace: str, repo_slug: str, pull_request_id: str, content: str, inline: Optional[dict] = None, pending: Optional[bool] = None) -> Dict[str, Any]:
        data = self._client.add_pull_request_comment(workspace, repo_slug, pull_request_id, content, inline=inline, pending=pending)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_add_pending_pull_request_comment(self, *, workspace: str, repo_slug: str, pull_request_id: str, content: str, inline: Optional[dict] = None) -> Dict[str, Any]:
        data = self._client.add_pull_request_comment(workspace, repo_slug, pull_request_id, content, inline=inline, pending=True)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_publish_pending_comments(self, *, workspace: str, repo_slug: str, pull_request_id: str) -> Dict[str, Any]:
        result = self._client.publish_pending_comments(workspace, repo_slug, pull_request_id)
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    def tool_create_draft_pull_request(self, *, workspace: str, repo_slug: str, title: str, description: str, sourceBranch: str, targetBranch: str, reviewers: Optional[list[str]] = None) -> Dict[str, Any]:
        data = self._client.create_pull_request(
            workspace,
            repo_slug,
            title,
            description,
            source_branch=sourceBranch,
            target_branch=targetBranch,
            reviewers=reviewers,
            draft=True,
        )
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_publish_draft_pull_request(self, *, workspace: str, repo_slug: str, pull_request_id: str) -> Dict[str, Any]:
        data = self._client.set_pull_request_draft(workspace, repo_slug, pull_request_id, draft=False)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_convert_to_draft(self, *, workspace: str, repo_slug: str, pull_request_id: str) -> Dict[str, Any]:
        data = self._client.set_pull_request_draft(workspace, repo_slug, pull_request_id, draft=True)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    # ---------------- Branching model tools ----------------
    def tool_get_repository_branching_model(self, *, workspace: str, repo_slug: str) -> Dict[str, Any]:
        data = self._client.get_repository_branching_model(workspace, repo_slug)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_get_repository_branching_model_settings(self, *, workspace: str, repo_slug: str) -> Dict[str, Any]:
        data = self._client.get_repository_branching_model_settings(workspace, repo_slug)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_update_repository_branching_model_settings(self, *, workspace: str, repo_slug: str, development: Optional[dict] = None, production: Optional[dict] = None, branch_types: Optional[list] = None) -> Dict[str, Any]:
        data = self._client.update_repository_branching_model_settings(workspace, repo_slug, development=development, production=production, branch_types=branch_types)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_get_effective_repository_branching_model(self, *, workspace: str, repo_slug: str) -> Dict[str, Any]:
        data = self._client.get_effective_repository_branching_model(workspace, repo_slug)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_get_project_branching_model(self, *, workspace: str, project_key: str) -> Dict[str, Any]:
        data = self._client.get_project_branching_model(workspace, project_key)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_get_project_branching_model_settings(self, *, workspace: str, project_key: str) -> Dict[str, Any]:
        data = self._client.get_project_branching_model_settings(workspace, project_key)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_update_project_branching_model_settings(self, *, workspace: str, project_key: str, development: Optional[dict] = None, production: Optional[dict] = None, branch_types: Optional[list] = None) -> Dict[str, Any]:
        data = self._client.update_project_branching_model_settings(workspace, project_key, development=development, production=production, branch_types=branch_types)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    # ---------------- Pipelines ----------------
    def tool_list_pipeline_runs(self, *, workspace: str, repo_slug: str, limit: Optional[int] = None, status: Optional[str] = None, target_branch: Optional[str] = None, trigger_type: Optional[str] = None) -> Dict[str, Any]:
        items = self._client.list_pipelines(workspace, repo_slug, limit=limit, status=status, target_branch=target_branch, trigger_type=trigger_type)
        return {"content": [{"type": "text", "text": json.dumps(items, indent=2)}]}

    def tool_get_pipeline_run(self, *, workspace: str, repo_slug: str, pipeline_uuid: str) -> Dict[str, Any]:
        data = self._client.get_pipeline(workspace, repo_slug, pipeline_uuid)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_run_pipeline(self, *, workspace: str, repo_slug: str, target: dict, variables: Optional[list[dict]] = None) -> Dict[str, Any]:
        data = self._client.run_pipeline(workspace, repo_slug, target=target, variables=variables)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_stop_pipeline(self, *, workspace: str, repo_slug: str, pipeline_uuid: str) -> Dict[str, Any]:
        self._client.stop_pipeline(workspace, repo_slug, pipeline_uuid)
        return {"content": [{"type": "text", "text": "Pipeline stop signal sent successfully."}]}

    def tool_get_pipeline_steps(self, *, workspace: str, repo_slug: str, pipeline_uuid: str) -> Dict[str, Any]:
        items = self._client.list_pipeline_steps(workspace, repo_slug, pipeline_uuid)
        return {"content": [{"type": "text", "text": json.dumps(items, indent=2)}]}

    def tool_get_pipeline_step(self, *, workspace: str, repo_slug: str, pipeline_uuid: str, step_uuid: str) -> Dict[str, Any]:
        data = self._client.get_pipeline_step(workspace, repo_slug, pipeline_uuid, step_uuid)
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}

    def tool_get_pipeline_step_logs(self, *, workspace: str, repo_slug: str, pipeline_uuid: str, step_uuid: str) -> Dict[str, Any]:
        text = self._client.get_pipeline_step_logs(workspace, repo_slug, pipeline_uuid, step_uuid)
        return {"content": [{"type": "text", "text": text}]}

    # ---------------- Convenience / derived ----------------
    def tool_get_pending_review_prs(self, *, workspace: Optional[str], limit: int = 50, repositoryList: Optional[list[str]] = None) -> Dict[str, Any]:
        ws = workspace or self._config.default_workspace
        if not ws:
            raise ValueError("Workspace must be provided or set via BITBUCKET_WORKSPACE")
        if not self._config.username:
            raise ValueError("BITBUCKET_USERNAME must be set to identify current reviewer")
        result = self._client.get_pending_review_prs(ws, current_user_nickname=self._config.username, limit=limit, repository_list=repositoryList)
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


