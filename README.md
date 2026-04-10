# Python FP Utilities

A UV workspace containing three small Python libraries for functional-programming-style code.

Requires Python 3.14+.

## Packages

### [partial-injector](src/partial-injector/README.md)

Dependency injection container built around `functools.partial`. Register plain functions and instances, then let the container wire their dependencies and hand back ready-to-call partials.

```bash
pip install partial-injector
```

### spinq

LINQ-style collection helpers for Python lists (`first_`, `where_`, `select_`, `order_by_`, etc.).

```bash
pip install spinq
```

### sversion

Simple version retrieval for Python projects — reads the current version from a `pyproject.toml` or a dedicated version file.

```bash
pip install sversion
```

## Development

This repo uses [UV](https://docs.astral.sh/uv/) workspaces.

```bash
# install all workspace dependencies
uv sync

# run tests
uv run pytest

# lint
uv run ruff check .
```

## Build and Publish

Build and upload a package from its directory:

```bash
cd src/<package>
uv build
uv publish
```

or 

```powershell
python -m build (or pyproject-build.exe . on Windows)
twine upload .\dist\*
```