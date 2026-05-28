# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests in this package (from workspace root)
uv run pytest tests/test-sversion

# Run a single test file
uv run pytest tests/test-sversion/test_sversion/test_pyproject_toml_based.py

# Run a single test by name
uv run pytest tests/test-sversion -k "test_get_version_found_with_folder_path"
```

## Architecture

Two test files, each covering one `sversion` strategy. Tests use `unittest.mock.patch` on `os.path.exists` and `builtins.open` so no real filesystem traversal occurs.

| Test file | Coverage |
|---|---|
| `test_pyproject_toml_based.py` | PEP 621 (`project.version`) and Poetry (`tool.poetry.version`) layouts, precedence between them, custom filename override, `PermissionError`, not-found path. |
| `test_version_file_based.py` | Plain `VERSION.txt` read, custom filename override, not-found path, `PermissionError`. |

The test package declares `sversion = { workspace = true }` so it always tests the local source.
