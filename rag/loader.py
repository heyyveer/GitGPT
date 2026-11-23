from pathlib import Path
from typing import List, Dict, Any
from utils.file_filter import is_allowed_file


class RepositoryLoader:

    def load_files(self, repo_path: str | Path) -> List[Dict[str, Any]]:
        repo_path = Path(repo_path)
        documents = []

        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue

            try:
                relative_path = file_path.relative_to(repo_path).as_posix()
            except ValueError:
                continue

            if not is_allowed_file(relative_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    content = file_path.read_text(encoding="latin-1")
                except Exception:
                    continue
            except OSError:
                continue

            if not content.strip():
                continue

            documents.append({
                "content": content,
                "file_path": relative_path,
                "extension": file_path.suffix.lower(),
                "file_name": file_path.name,
                "size_bytes": len(content.encode("utf-8")),
            })

        return documents