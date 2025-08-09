from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Optional

import httpx
import structlog

from config import BitbucketConfig


logger = structlog.get_logger(__name__)


class BitbucketClient:
    """Thin Bitbucket API client using httpx.

    Mirrors the axios-based calls in the JS implementation but keeps responses
    as-is (JSON or text) so the MCP layer can serialize output directly.
    """

    def __init__(self, config: BitbucketConfig, *, timeout: float = 30.0) -> None:
        self._config = config
        headers: Dict[str, str] = {}
        if config.token:
            headers["Authorization"] = f"Bearer {config.token}"
        else:
            headers["Content-Type"] = "application/json"

        auth = None
        if config.username and config.password:
            auth = (config.username, config.password)

        self._client = httpx.Client(
            base_url=config.base_url,
            headers=headers,
            timeout=timeout,
            auth=auth,
            follow_redirects=True,
        )

    # ---------- Repository operations ----------
    def list_repositories(self, workspace: str, *, limit: int = 10, name: Optional[str] = None) -> Any:
        params: Dict[str, Any] = {"limit": limit}
        if name:
            params["q"] = f'name~"{name}"'
        resp = self._client.get(f"/repositories/{workspace}", params=params)
        resp.raise_for_status()
        return resp.json().get("values", [])

    def get_repository(self, workspace: str, repo_slug: str) -> Any:
        resp = self._client.get(f"/repositories/{workspace}/{repo_slug}")
        resp.raise_for_status()
        return resp.json()

    # ---------- Pull request operations ----------
    def get_pull_requests(self, workspace: str, repo_slug: str, *, state: Optional[str] = None, limit: int = 10) -> Any:
        params: Dict[str, Any] = {"limit": limit}
        if state:
            params["state"] = state
        resp = self._client.get(f"/repositories/{workspace}/{repo_slug}/pullrequests", params=params)
        resp.raise_for_status()
        return resp.json().get("values", [])

    def create_pull_request(
        self,
        workspace: str,
        repo_slug: str,
        title: str,
        description: str,
        source_branch: str,
        target_branch: str,
        reviewers: Optional[Iterable[str]] = None,
        draft: Optional[bool] = None,
    ) -> Any:
        payload: Dict[str, Any] = {
            "title": title,
            "description": description,
            "source": {"branch": {"name": source_branch}},
            "destination": {"branch": {"name": target_branch}},
            "close_source_branch": True,
        }
        if reviewers:
            payload["reviewers"] = [{"username": u} for u in reviewers]
        if draft is True:
            payload["draft"] = True

        resp = self._client.post(f"/repositories/{workspace}/{repo_slug}/pullrequests", json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_pull_request(self, workspace: str, repo_slug: str, pr_id: str) -> Any:
        resp = self._client.get(f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}")
        resp.raise_for_status()
        return resp.json()

    def get_pull_request_activity(self, workspace: str, repo_slug: str, pr_id: str) -> Any:
        resp = self._client.get(
            f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/activity"
        )
        resp.raise_for_status()
        return resp.json().get("values", [])

    def update_pull_request(self, workspace: str, repo_slug: str, pr_id: str, *, title: Optional[str] = None, description: Optional[str] = None) -> Any:
        payload: Dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        resp = self._client.put(f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}", json=payload)
        resp.raise_for_status()
        return resp.json()

    def set_pull_request_draft(self, workspace: str, repo_slug: str, pr_id: str, *, draft: bool) -> Any:
        resp = self._client.put(
            f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}",
            json={"draft": draft},
        )
        resp.raise_for_status()
        return resp.json()

    def approve_pull_request(self, workspace: str, repo_slug: str, pr_id: str) -> Any:
        resp = self._client.post(f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/approve")
        resp.raise_for_status()
        return resp.json()

    def unapprove_pull_request(self, workspace: str, repo_slug: str, pr_id: str) -> None:
        resp = self._client.delete(f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/approve")
        resp.raise_for_status()

    def decline_pull_request(self, workspace: str, repo_slug: str, pr_id: str, *, message: Optional[str] = None) -> Any:
        payload: Dict[str, Any] = {"message": message} if message else {}
        resp = self._client.post(f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/decline", json=payload)
        resp.raise_for_status()
        return resp.json()

    def merge_pull_request(self, workspace: str, repo_slug: str, pr_id: str, *, message: Optional[str] = None, strategy: Optional[str] = None) -> Any:
        payload: Dict[str, Any] = {}
        if message:
            payload["message"] = message
        if strategy:
            payload["merge_strategy"] = strategy
        resp = self._client.post(f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/merge", json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_pull_request_comments(self, workspace: str, repo_slug: str, pr_id: str) -> Any:
        resp = self._client.get(f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/comments")
        resp.raise_for_status()
        return resp.json().get("values", [])

    def get_pull_request_commits(self, workspace: str, repo_slug: str, pr_id: str) -> Any:
        resp = self._client.get(
            f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/commits"
        )
        resp.raise_for_status()
        return resp.json().get("values", [])

    def get_pull_request_diff(self, workspace: str, repo_slug: str, pr_id: str) -> str:
        # Bitbucket supports a direct diff endpoint
        resp = self._client.get(
            f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/diff",
            headers={"Accept": "text/plain"},
        )
        resp.raise_for_status()
        return resp.text

    def add_pull_request_comment(
        self,
        workspace: str,
        repo_slug: str,
        pr_id: str,
        content: str,
        *,
        inline: Optional[dict] = None,
        pending: Optional[bool] = None,
    ) -> Any:
        payload: Dict[str, Any] = {"content": {"raw": content}}
        if inline:
            payload["inline"] = {k: v for k, v in inline.items() if v is not None}
        if pending is not None:
            payload["pending"] = pending
        resp = self._client.post(f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/comments", json=payload)
        resp.raise_for_status()
        return resp.json()

    def publish_pending_comments(self, workspace: str, repo_slug: str, pr_id: str) -> Any:
        # Fetch comments, filter pending, then PUT to set pending=False
        comments = self.get_pull_request_comments(workspace, repo_slug, pr_id)
        results = []
        for comment in comments:
            if comment.get("pending") is True:
                cid = comment.get("id")
                payload = {"content": comment.get("content"), "pending": False}
                if "inline" in comment:
                    payload["inline"] = comment["inline"]
                resp = self._client.put(
                    f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/comments/{cid}",
                    json=payload,
                )
                resp.raise_for_status()
                results.append({"commentId": cid, "status": "published", "data": resp.json()})
        return {"published": len(results), "results": results}

    def get_pending_review_prs(self, workspace: str, *, current_user_nickname: str, limit: int = 50, repository_list: Optional[list[str]] = None) -> Dict[str, Any]:
        # If repository list not provided, list all repos (name used as slug here)
        repos: list[str] = repository_list or [r.get("name") for r in self.list_repositories(workspace, limit=100)]
        pending: list[dict] = []
        for repo_slug in repos:
            try:
                prs = self.get_pull_requests(workspace, repo_slug, state="OPEN", limit=min(limit, 50))
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Failed to fetch PRs for repo", repo=repo_slug, error=str(exc))
                prs = []
            for pr in prs:
                participants = pr.get("participants") or []
                for p in participants:
                    user = (p or {}).get("user") or {}
                    if (
                        user.get("nickname") == current_user_nickname
                        and p.get("role") == "REVIEWER"
                        and p.get("approved") is False
                    ):
                        pr_with_repo = dict(pr)
                        pr_with_repo["repository"] = {"name": repo_slug, "full_name": f"{workspace}/{repo_slug}"}
                        pending.append(pr_with_repo)
                        break
            if len(pending) >= limit:
                break
        # sort by updated_on desc
        pending.sort(key=lambda x: x.get("updated_on", ""), reverse=True)
        pending = pending[:limit]
        return {
            "pending_review_prs": pending,
            "total_found": len(pending),
            "searched_repositories": len(repos),
            "user": current_user_nickname,
            "workspace": workspace,
        }

    # ---------- Branching model operations ----------
    def get_repository_branching_model(self, workspace: str, repo_slug: str) -> Any:
        resp = self._client.get(f"/repositories/{workspace}/{repo_slug}/branching-model")
        resp.raise_for_status()
        return resp.json()

    def get_repository_branching_model_settings(self, workspace: str, repo_slug: str) -> Any:
        resp = self._client.get(f"/repositories/{workspace}/{repo_slug}/branching-model/settings")
        resp.raise_for_status()
        return resp.json()

    def update_repository_branching_model_settings(self, workspace: str, repo_slug: str, *, development: Optional[dict] = None, production: Optional[dict] = None, branch_types: Optional[list] = None) -> Any:
        payload: Dict[str, Any] = {}
        if development is not None:
            payload["development"] = development
        if production is not None:
            payload["production"] = production
        if branch_types is not None:
            payload["branch_types"] = branch_types
        resp = self._client.put(f"/repositories/{workspace}/{repo_slug}/branching-model/settings", json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_effective_repository_branching_model(self, workspace: str, repo_slug: str) -> Any:
        resp = self._client.get(f"/repositories/{workspace}/{repo_slug}/effective-branching-model")
        resp.raise_for_status()
        return resp.json()

    def get_project_branching_model(self, workspace: str, project_key: str) -> Any:
        resp = self._client.get(f"/workspaces/{workspace}/projects/{project_key}/branching-model")
        resp.raise_for_status()
        return resp.json()

    def get_project_branching_model_settings(self, workspace: str, project_key: str) -> Any:
        resp = self._client.get(f"/workspaces/{workspace}/projects/{project_key}/branching-model/settings")
        resp.raise_for_status()
        return resp.json()

    def update_project_branching_model_settings(self, workspace: str, project_key: str, *, development: Optional[dict] = None, production: Optional[dict] = None, branch_types: Optional[list] = None) -> Any:
        payload: Dict[str, Any] = {}
        if development is not None:
            payload["development"] = development
        if production is not None:
            payload["production"] = production
        if branch_types is not None:
            payload["branch_types"] = branch_types
        resp = self._client.put(f"/workspaces/{workspace}/projects/{project_key}/branching-model/settings", json=payload)
        resp.raise_for_status()
        return resp.json()

    # ---------- Pipelines ----------
    def list_pipelines(self, workspace: str, repo_slug: str, *, limit: Optional[int] = None, status: Optional[str] = None, target_branch: Optional[str] = None, trigger_type: Optional[str] = None) -> Any:
        params: Dict[str, Any] = {}
        if limit:
            params["pagelen"] = limit
        if status:
            params["status"] = status
        if target_branch:
            params["target.branch"] = target_branch
        if trigger_type:
            params["trigger_type"] = trigger_type
        resp = self._client.get(f"/repositories/{workspace}/{repo_slug}/pipelines", params=params)
        resp.raise_for_status()
        return resp.json().get("values", [])

    def get_pipeline(self, workspace: str, repo_slug: str, pipeline_uuid: str) -> Any:
        resp = self._client.get(f"/repositories/{workspace}/{repo_slug}/pipelines/{pipeline_uuid}")
        resp.raise_for_status()
        return resp.json()

    def run_pipeline(self, workspace: str, repo_slug: str, *, target: dict, variables: Optional[Iterable[dict]] = None) -> Any:
        pipeline_target: Dict[str, Any] = {
            "type": "pipeline_commit_target" if target.get("commit_hash") else "pipeline_ref_target",
            "ref_type": target.get("ref_type"),
            "ref_name": target.get("ref_name"),
        }
        if target.get("commit_hash"):
            pipeline_target["commit"] = {"type": "commit", "hash": target["commit_hash"]}
        if target.get("selector_type") and target.get("selector_pattern"):
            pipeline_target["selector"] = {"type": target["selector_type"], "pattern": target["selector_pattern"]}

        payload: Dict[str, Any] = {"target": pipeline_target}
        if variables:
            payload["variables"] = [
                {"key": v["key"], "value": v["value"], "secured": bool(v.get("secured", False))}
                for v in variables
            ]
        resp = self._client.post(f"/repositories/{workspace}/{repo_slug}/pipelines", json=payload)
        resp.raise_for_status()
        return resp.json()

    def stop_pipeline(self, workspace: str, repo_slug: str, pipeline_uuid: str) -> None:
        resp = self._client.post(f"/repositories/{workspace}/{repo_slug}/pipelines/{pipeline_uuid}/stopPipeline")
        resp.raise_for_status()

    def list_pipeline_steps(self, workspace: str, repo_slug: str, pipeline_uuid: str) -> Any:
        resp = self._client.get(f"/repositories/{workspace}/{repo_slug}/pipelines/{pipeline_uuid}/steps")
        resp.raise_for_status()
        return resp.json().get("values", [])

    def get_pipeline_step(self, workspace: str, repo_slug: str, pipeline_uuid: str, step_uuid: str) -> Any:
        resp = self._client.get(f"/repositories/{workspace}/{repo_slug}/pipelines/{pipeline_uuid}/steps/{step_uuid}")
        resp.raise_for_status()
        return resp.json()

    def get_pipeline_step_logs(self, workspace: str, repo_slug: str, pipeline_uuid: str, step_uuid: str) -> str:
        resp = self._client.get(
            f"/repositories/{workspace}/{repo_slug}/pipelines/{pipeline_uuid}/steps/{step_uuid}/log",
            headers={"Accept": "text/plain"},
        )
        resp.raise_for_status()
        return resp.text


