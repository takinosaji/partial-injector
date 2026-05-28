# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run tests for this package (from workspace root)
uv run pytest tests/test-sversion

# Lint
uv run ruff check src/sversion

# Fix lint issues
uv run ruff check src/sversion --fix

# Build for publishing
cd src/sversion
uv build
uv publish
```

## Architecture

`sversion` exposes two independent version-retrieval strategies; each is a module with a single public `get_version: VersionRetriever` callable.

| Module | Strategy |
|---|---|
| `pyproject_toml_based.py` | Walks up from `start_search_path` looking for `pyproject.toml`. Reads `project.version` (PEP 621) first, then `tool.poetry.version`. |
| `version_file_based.py` | Walks up from `start_search_path` looking for `VERSION.txt`. Returns the file's trimmed contents. |
| `contracts.py` | Type aliases only: `Version = str`, `VersionRetriever = Callable[[str], Version]`. |
| `error_handling.py` | Single exception: `VersionNotFoundException`. Raised when no file is found before reaching the filesystem root, or on `PermissionError`. |

Both strategies accept a file **or** directory path as `start_search_path`. When a file path is given the search starts in its parent directory. The second parameter (`project_file_name` / `version_file_name`) allows overriding the default filename.

The public functions are module-level names (`get_version = __get_version`) rather than direct `def get_version(...)` so they can be typed as `VersionRetriever`.
