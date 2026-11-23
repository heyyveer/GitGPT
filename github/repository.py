from pathlib import Path
from typing import List, Dict, Any, Optional
from git import Repo
from config.settings import REPOSITORIES_DIR
from utils.helpers import safe_remove_directory, parse_github_url
from utils.file_filter import is_allowed_file


class RepositoryManager:

    def __init__(self, base_dir: Path | str = REPOSITORIES_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_repo_dir(self, repo_url: str) -> Path:
        _, repo_name, _ = parse_github_url(repo_url)
        return self.base_dir / repo_name

    def is_cloned(self, repo_url: str) -> bool:
        repo_dir = self.get_repo_dir(repo_url)
        return repo_dir.exists() and (repo_dir / ".git").exists()

    def clone_repository(
        self,
        repo_url: str,
        force_reclone: bool = False,
        depth: int = 1
    ) -> str:
        """
        Clone a GitHub repository into the local storage folder.
        Uses shallow clone (depth=1) for speed and disk conservation.
        """
        _, repo_name, clean_url = parse_github_url(repo_url)
        repo_path = self.base_dir / repo_name

        if repo_path.exists():
            if not force_reclone and (repo_path / ".git").exists():
                return str(repo_path)
            # Remove existing folder cleanly
            safe_remove_directory(repo_path)

        # Clone using GitPython with shallow depth
        Repo.clone_from(
            clean_url,
            repo_path,
            depth=depth,
            multi_options=["--single-branch"]
        )

        return str(repo_path)

    def get_repository_files(self, repo_path: str | Path) -> List[str]:
        """List all allowed code & doc files in the cloned repository."""
        repo_path = Path(repo_path)
        files = []

        for path in repo_path.rglob("*"):
            if path.is_file():
                relative_path = path.relative_to(repo_path).as_posix()
                if is_allowed_file(relative_path):
                    files.append(relative_path)

        return sorted(files)

    def get_repository_stats(self, repo_path: str | Path) -> Dict[str, Any]:
        """Calculate statistics for the repository (files, lines of code, languages)."""
        repo_path = Path(repo_path)
        files = self.get_repository_files(repo_path)

        total_lines = 0
        total_size = 0
        lang_counts: Dict[str, int] = {}

        for rel_file in files:
            full_file = repo_path / rel_file
            try:
                size = full_file.stat().st_size
                total_size += size
                content = full_file.read_text(encoding="utf-8", errors="ignore")
                lines = len(content.splitlines())
                total_lines += lines

                ext = full_file.suffix.lower() or "other"
                lang_counts[ext] = lang_counts.get(ext, 0) + 1
            except Exception:
                continue

        return {
            "total_files": len(files),
            "total_lines": total_lines,
            "total_size_bytes": total_size,
            "languages": lang_counts,
        }