import os
import requests
from typing import Dict, Any, Optional
from config.settings import GITHUB_TOKEN


class GitHubClient:

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or GITHUB_TOKEN
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "TalkToGitHub-Agent",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def search_repositories(
        self,
        query: str,
        per_page: int = 20,
        sort: str = "best-match",
        order: str = "desc"
    ) -> Dict[str, Any]:
        """Search GitHub repositories matching the query."""
        url = f"{self.BASE_URL}/search/repositories"
        params = {
            "q": query,
            "per_page": min(per_page, 100),
            "order": order,
        }
        if sort and sort != "best-match":
            params["sort"] = sort

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=15
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    raise RuntimeError("GitHub API 401 Unauthorized: Your GITHUB_TOKEN in .env is invalid or expired. Please update it with a valid GitHub Personal Access Token.") from e
                if e.response.status_code == 403:
                    raise RuntimeError("GitHub API rate limit exceeded (403). Please ensure a valid GITHUB_TOKEN is configured in .env.") from e
            raise RuntimeError(f"GitHub Search API request failed: {str(e)}") from e

    def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get detailed repository metadata."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers, timeout=15)
        response.raise_for_status()
        return response.json()

    def get_rate_limit(self) -> Dict[str, Any]:
        """Check current GitHub API rate limit status."""
        url = f"{self.BASE_URL}/rate_limit"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            core = data.get("resources", {}).get("core", {})
            search = data.get("resources", {}).get("search", {})
            return {
                "core_remaining": core.get("remaining", 0),
                "core_limit": core.get("limit", 0),
                "search_remaining": search.get("remaining", 0),
                "search_limit": search.get("limit", 0),
            }
        except Exception:
            return {
                "core_remaining": "unknown",
                "core_limit": "unknown",
                "search_remaining": "unknown",
                "search_limit": "unknown",
            }