from typing import List, Dict, Any, Optional
from github.client import GitHubClient


class RepositorySearcher:

    def __init__(self, client: Optional[GitHubClient] = None):
        self.client = client or GitHubClient()

    def search(
        self,
        task: str,
        limit: int = 20,
        language: Optional[str] = None,
        min_stars: int = 0,
        sort: str = "best-match",
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search and rank GitHub repositories based on task description and optional filters.
        """
        base_query = self._build_query(task)

        # Append filters if requested
        query_parts = [base_query]
        if language and language.lower() != "all":
            query_parts.append(f"language:{language.lower()}")
        if min_stars > 0:
            query_parts.append(f"stars:>={min_stars}")

        full_query = " ".join(query_parts)

        result = self.client.search_repositories(
            query=full_query,
            per_page=limit,
            sort=sort
        )

        repositories = []
        for repo in result.get("items", []):
            repositories.append({
                "name": repo["full_name"],
                "description": repo.get("description") or "No description provided.",
                "url": repo["html_url"],
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language") or "Unknown",
                "updated_at": repo.get("updated_at", ""),
                "topics": repo.get("topics", []),
                "size": repo.get("size", 0),
                "default_branch": repo.get("default_branch", "main"),
                "open_issues": repo.get("open_issues_count", 0),
                "owner": repo.get("owner", {}).get("login", "") if isinstance(repo.get("owner"), dict) else "",
                "owner_avatar": repo.get("owner", {}).get("avatar_url", "") if isinstance(repo.get("owner"), dict) else "",
                "license": repo.get("license", {}).get("spdx_id") if isinstance(repo.get("license"), dict) else None,
                "clone_url": repo.get("clone_url") or f"{repo['html_url']}.git",
            })

        ranked = self.rank_repositories(task, repositories)
        return ranked[:top_k]

    def _build_query(self, task: str) -> str:
        task = task.lower().strip()

        stop_words = {
            "i", "want", "to", "build", "make", "create",
            "develop", "an", "a", "the", "using", "with",
            "for", "my", "project", "application", "app",
            "system", "please", "can", "you", "help",
            "me", "that", "should", "be", "would",
            "like", "need", "best", "good", "how", "what",
            "where", "give", "show", "find", "search"
        }

        # Clean punctuation
        for char in [",", ".", ";", ":", "!", "?", "(", ")", "[", "]", "{", "}"]:
            task = task.replace(char, " ")

        words = task.split()

        keywords = [
            word
            for word in words
            if word not in stop_words and len(word) > 2
        ]

        if not keywords:
            return task or "agent"

        return " ".join(keywords[:10])

    def rank_repositories(self, task: str, repositories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        task_words = set(self._build_query(task).lower().split())

        for repo in repositories:
            score = 0

            searchable_text = " ".join([
                repo["name"],
                repo["description"],
                repo["language"],
                " ".join(repo["topics"])
            ]).lower()

            # Keyword relevance in title and description
            matched_keywords = sum(
                1 for word in task_words if word in searchable_text
            )
            score += matched_keywords * 15

            # Name match bonus
            name_matches = sum(1 for word in task_words if word in repo["name"].lower())
            score += name_matches * 10

            # Stars tiering
            stars = repo.get("stars", 0)
            if stars >= 50000:
                score += 25
            elif stars >= 10000:
                score += 20
            elif stars >= 5000:
                score += 15
            elif stars >= 1000:
                score += 10
            elif stars >= 100:
                score += 5

            # Forks tiering
            forks = repo.get("forks", 0)
            if forks >= 5000:
                score += 12
            elif forks >= 1000:
                score += 8
            elif forks >= 100:
                score += 4

            repo["relevance_score"] = score
            repo["matched_keywords"] = matched_keywords

        repositories.sort(
            key=lambda x: x["relevance_score"],
            reverse=True
        )

        return repositories