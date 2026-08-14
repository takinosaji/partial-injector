# Suggested Commands

Run everything from the **workspace root** unless noted. Shell is PowerShell on Windows (`;` chains, `Get-Content`/`ls`); use forward slashes in paths passed to uv/pytest.

## Setup / deps
```
uv sync --all-groups
```

## Test
```
uv run pytest                                   # all three test packages (testpaths = ["tests"])
uv run pytest tests/test-partial-injector
uv run pytest tests/test-spinq
uv run pytest tests/test-sversion
uv run pytest tests/test-partial-injector -k "<test_name>"
```

## Lint / format / SAST
```
uv run ruff check .
uv run ruff check . --fix
uv run ruff format .
uv run bandit -r -c .bandit src tests sdlc
uv run pre-commit run --all-files
```

## Build / publish (per package)
```
cd src/<package> ; uv build ; uv publish
```

## sdlc scripts (argparse-driven, run with `uv run python <path>`)
- `sdlc/local-dev/dev-scripts/update-all-dependencies.py` — `uv lock --upgrade` + `uv sync --all-groups` per project; `--recursive` walks deepest-first.
- `sdlc/local-dev/dev-scripts/upgrade-pyproject-versions.py`
- `sdlc/local-dev/dev-scripts/delete-all-locks.py`, `fix-all-locks.py`
- `sdlc/ci/install-scripts/install-all-dependencies.py` — `uv sync` per project, shallowest-first.
- `sdlc/ci/install-scripts/install-latest-wheel.py`
