import re
from pathlib import Path
from typing import List, Dict, Any, Optional


class SourceLocator:

    def __init__(self, repository_path: str | Path):
        self.repository_path = Path(repository_path)

    def find_code(
        self,
        file_path: str,
        search_text: str,
        context_lines: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Locate search_text in the given repository file.
        Returns line number, matched content, and optional context.
        """
        norm_path = file_path.replace("\\", "/").lstrip("/")
        full_path = self.repository_path / norm_path

        if not full_path.exists():
            return []

        try:
            lines = full_path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            return []

        search_text = search_text.strip()
        if not search_text:
            return []

        matches = []

        for index, line in enumerate(lines, 1):
            if search_text in line:
                match_data = {
                    "file_path": norm_path,
                    "line": index,
                    "content": line.strip(),
                }

                if context_lines > 0:
                    start_idx = max(0, index - 1 - context_lines)
                    end_idx = min(len(lines), index + context_lines)
                    match_data["context"] = "\n".join(lines[start_idx:end_idx])
                    match_data["start_line"] = start_idx + 1
                    match_data["end_line"] = end_idx

                matches.append(match_data)

        return matches

    def find_term(
        self,
        file_path: str,
        term: str
    ) -> List[Dict[str, Any]]:
        return self.find_code(file_path=file_path, search_text=term)

    def find_symbol(
        self,
        symbol_name: str,
        target_file: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find class or function definitions matching symbol_name across repo or in target_file.
        """
        results = []
        files = [self.repository_path / target_file] if target_file else list(self.repository_path.rglob("*"))

        pattern = re.compile(rf"\b(def|class|async\s+def|function|const|let|var)\s+{re.escape(symbol_name)}\b")

        for p in files:
            if not p.is_file():
                continue
            try:
                lines = p.read_text(encoding="utf-8").splitlines()
                rel_path = p.relative_to(self.repository_path).as_posix()
                for idx, line in enumerate(lines, 1):
                    if pattern.search(line):
                        results.append({
                            "file_path": rel_path,
                            "line": idx,
                            "content": line.strip(),
                            "symbol": symbol_name
                        })
            except Exception:
                continue

        return results