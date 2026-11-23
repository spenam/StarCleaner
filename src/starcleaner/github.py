"""Small, dependency-free GitHub REST API client."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_URL = "https://api.github.com"
API_VERSION = "2026-03-10"


class GitHubAPIError(RuntimeError):
    """An HTTP or API error returned by GitHub."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class GitHubClient:
    def __init__(self, token: str, timeout: int = 30) -> None:
        if not token.strip():
            raise ValueError("A GitHub token is required.")
        self.token = token.strip()
        self.timeout = timeout

    def _request(self, path: str, method: str = "GET") -> Any:
        url = f"{API_URL}{path}"
        request = urllib.request.Request(
            url,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "StarCleaner/0.1.0",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = response.read()
                if not payload:
                    return None
                return json.loads(payload.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                message = json.loads(body).get("message", body)
            except (json.JSONDecodeError, AttributeError):
                message = body or exc.reason
            if exc.code == 401:
                hint = " Check that STARCLEANER_TOKEN is valid."
            elif exc.code == 403:
                hint = " Check your token permissions and GitHub API rate limit."
            else:
                hint = ""
            raise GitHubAPIError(f"GitHub API returned {exc.code}: {message}.{hint}", exc.code) from exc
        except urllib.error.URLError as exc:
            raise GitHubAPIError(f"Could not reach GitHub: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise GitHubAPIError("GitHub returned an invalid JSON response.") from exc

    def list_starred_repositories(self) -> list[dict[str, Any]]:
        """Fetch every repository starred by the authenticated user."""
        repositories: list[dict[str, Any]] = []
        page = 1
        while True:
            query = urllib.parse.urlencode({"per_page": 100, "page": page})
            result = self._request(f"/user/starred?{query}")
            if not isinstance(result, list):
                raise GitHubAPIError("Unexpected response while listing starred repositories.")
            repositories.extend(result)
            if len(result) < 100:
                return repositories
            page += 1

    def unstar(self, full_name: str) -> None:
        """Remove one star. GitHub returns HTTP 204 on success."""
        parts = full_name.split("/", 1)
        if len(parts) != 2 or not all(parts):
            raise ValueError(f"Invalid repository name: {full_name!r}")
        owner, repo = (urllib.parse.quote(part, safe="") for part in parts)
        self._request(f"/user/starred/{owner}/{repo}", method="DELETE")
