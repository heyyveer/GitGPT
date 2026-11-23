import os
import re
import stat
import shutil
from pathlib import Path
from typing import Tuple, Optional, Any
from config.settings import (
    DEFAULT_GROQ_MODEL,
    DEFAULT_GEMINI_MODEL,
    GROQ_API_KEY,
    GEMINI_API_KEY,
)


def parse_github_url(repo_url: str) -> Tuple[str, str, str]:
    """
    Parse a GitHub URL and return (owner, repo_name, clean_url).
    Supports formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - owner/repo
    """
    clean = repo_url.strip()
    if clean.endswith(".git"):
        clean = clean[:-4]
    clean = clean.rstrip("/")

    # Check for owner/repo format
    if "/" in clean and not clean.startswith("http"):
        parts = clean.split("/")
        if len(parts) == 2:
            owner, repo = parts[0], parts[1]
            return owner, repo, f"https://github.com/{owner}/{repo}"

    # Check for full url format
    match = re.search(r"github\.com/([^/]+)/([^/]+)", clean)
    if match:
        owner = match.group(1)
        repo = match.group(2)
        return owner, repo, f"https://github.com/{owner}/{repo}"

    # Fallback to last segment
    repo_name = clean.split("/")[-1]
    return "unknown", repo_name, clean


def handle_remove_readonly(func, path, exc):
    """
    Error handler for shutil.rmtree on Windows when encountering
    read-only files (such as those created in .git directories).
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def safe_remove_directory(dir_path: Path | str) -> bool:
    """
    Safely delete a directory and all its contents on Windows/Linux.
    """
    path = Path(dir_path)
    if not path.exists():
        return True
    try:
        shutil.rmtree(path, onerror=handle_remove_readonly)
        return True
    except Exception:
        # Fallback retry
        try:
            for p in path.rglob("*"):
                try:
                    os.chmod(p, stat.S_IWRITE)
                except Exception:
                    pass
            shutil.rmtree(path, ignore_errors=True)
            return True
        except Exception:
            return False


def format_number(num: int | float) -> str:
    """Format numbers into human-readable strings with k/M suffixes."""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}k"
    return str(int(num))


def format_bytes(size_bytes: int) -> str:
    """Format byte counts into human-readable strings (KB, MB)."""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"


def get_llm(model: Optional[str] = None, temperature: float = 0.0) -> Any:
    """
    Factory function to get an LLM instance.
    Prioritizes Groq if available, falls back to Google Gemini.
    """
    if GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            selected_model = model or DEFAULT_GROQ_MODEL
            return ChatGroq(
                model=selected_model,
                temperature=temperature,
            )
        except Exception:
            pass

    if GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            selected_model = model or DEFAULT_GEMINI_MODEL
            return ChatGoogleGenerativeAI(
                model=selected_model,
                temperature=temperature,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gemini LLM: {str(e)}")

    raise ValueError("Neither GROQ_API_KEY nor GEMINI_API_KEY is configured.")
