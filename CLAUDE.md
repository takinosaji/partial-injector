# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install all workspace dependencies
uv sync

# Run all tests
uv run pytest

# Run tests for a specific package
uv run pytest tests/test-partial-injector
uv run pytest tests/test-sversion

# Run a single test file
uv run pytest tests/test-partial-injector/test_partial_injector/test_partial_container/test_case_singleton_resolution.py

# Lint
uv run ruff check .

# Fix lint issues automatically
uv run ruff check . --fix

# Build a package for publishing
cd src/<package>
uv build
uv publish
```

## Architecture

This is a **UV workspace** containing three independent publishable Python libraries (Python 3.14+ only) and their test packages. All packages use hatchling as the build backend.

```
src/
  partial-injector/   # DI container library (partial_injector package)
  spinq/              # LINQ-style collection helpers (spinq package)
  sversion/           # Version retrieval utilities (sversion package)
tests/
  test-partial-injector/   # Tests for partial-injector
  test-sversion/           # Tests for sversion
pyproject.toml        # Workspace root: UV workspace config, ruff config, pytest config
```

Test packages declare `workspace = true` dependencies so they reference local source packages. There is no dedicated test package for `spinq`.

### partial-injector

The core library. The main class is `Container` in `src/partial-injector/partial_injector/partial_container.py`.

**How it works:**
1. Register functions, instances, or factories with `register_singleton`, `register_transient`, `register_singleton_factory`, or `register_transient_factory`.
2. Call `container.build()` — the container inspects each registered function's parameter type annotations and parameter names, matches them against registered keys, and creates `functools.partial` objects with those dependencies pre-filled.
3. Call `container.resolve(key)` to get the wired object.

**Key concepts:**
- **Registration keys**: By default the registered object itself is the key. Pass `key=` to use a type, string, or `TypeAlias` instead.
- **Multiple registrations**: Registering two objects under the same key groups them; resolve the group as `list[Key]`.
- **`FromContainer`**: A descriptor that pulls a value from another registered key, optionally via a selector lambda. Used as a registration value or as `factory_args`/`factory_kwargs` elements.
- **`inject_returns=True`**: When a function returns another function, the container recursively wires that returned function's dependencies too (supports async).
- **`inject_items=True`**: When registering a list, each element is individually processed through the container's injection logic.
- **Conditional registrations**: `condition`, `condition_args`, `condition_kwargs` parameters. For `SINGLETON`/`SINGLETON_FACTORY` the condition is evaluated at `build()` time; for `TRANSIENT`/`TRANSIENT_FACTORY` it is evaluated lazily at each `resolve()`.
- All errors raise `PartialContainerException` from `partial_injector.error_handling`.

### spinq

LINQ-style helpers for Python lists (`first_`, `where_`, `select_`, `order_by_`, etc.) in `src/spinq/spinq/`.

### sversion

Version retrieval in `src/sversion/sversion/` — reads version from `pyproject.toml` or a dedicated version file. Defines contracts in `contracts.py` with implementations in `pyproject_toml_based.py` and `version_file_based.py`.
