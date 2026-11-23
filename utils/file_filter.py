from pathlib import Path


ALLOWED_EXTENSIONS = {
    ".py",
    ".pyi",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cc",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".scala",
    ".html",
    ".css",
    ".scss",
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".sh",
    ".bash",
    ".zsh",
    ".sql",
    ".graphql",
    ".proto",
    ".dockerfile",
}

ALLOWED_FILENAMES = {
    "dockerfile",
    "makefile",
    "gemfile",
    "procfile",
    "pipfile",
    "license",
    "readme",
}

IGNORED_DIRECTORIES = {
    ".git",
    ".github",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    "target",
    "bin",
    "obj",
    ".idea",
    ".vscode",
    ".next",
    ".nuxt",
    ".output",
    "coverage",
    ".turbo",
    "vendor",
    "site-packages",
    "eggs",
    ".eggs",
}

IGNORED_FILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
    "cargo.lock",
    "composer.lock",
    "gemfile.lock",
}


def is_allowed_file(file_path: str) -> bool:
    path = Path(file_path)

    # Check ignored directories in path
    if any(directory in IGNORED_DIRECTORIES for directory in path.parts):
        return False

    # Check ignored files (huge lock files)
    if path.name.lower() in IGNORED_FILES:
        return False

    # Check exact allowed filenames without extension
    if path.name.lower() in ALLOWED_FILENAMES:
        return True

    # Check extension
    if path.suffix.lower() in ALLOWED_EXTENSIONS:
        return True

    return False