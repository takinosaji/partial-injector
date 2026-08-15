# Core

UV **workspace** publishing three independent PyPI packages. Repo name (`partial-injector`) == one of the packages; the repo is *not* a single project.

## Source map

| Path | Package (PyPI name) | Notes |
|---|---|---|
| `src/partial-injector/partial_injector/` | `partial-injector` | DI container over `functools.partial`. Largest package. |
| `src/spinq/spinq/` | `spinq` | LINQ-style list/dict helpers. |
| `src/sversion/sversion/` | `sversion` | Version retrieval from `pyproject.toml` / `VERSION.txt`. Only package with a runtime dep (`toml`). |
| `tests/test-partial-injector/test_partial_injector/` | `partial-injector-tests` (unpublished, v0.0.0) | |
| `tests/test-spinq/test_spinq/` | `spinq-tests` (unpublished, v0.0.0) | Folder per source module, file per category. |
| `tests/test-sversion/test_sversion/` | `sversion-tests` (unpublished, v0.0.0) | |
| `sdlc/` | — | Python helper scripts for CI/local dev, see `mem:suggested_commands`. |

Directory names are hyphenated; **Python package dirs inside them are underscored**. Each workspace member has its own `pyproject.toml` that duplicates the root `[tool.ruff]` config; the root config is what pre-commit and the hooks use.

## Per-package architecture

Authoritative architecture docs are the committed `CLAUDE.md` files — read them instead of re-deriving:
`src/partial-injector/CLAUDE.md` (module responsibilities, container lifecycle, key invariants),
`src/spinq/CLAUDE.md`, `src/sversion/CLAUDE.md`,
`tests/test-partial-injector/CLAUDE.md` and `tests/test-sversion/CLAUDE.md` (which test file covers which scenario).
Keep these files updated when changing a package's structure.

## Invariants

- Test packages pin their subject via `[tool.uv.sources] <pkg> = { workspace = true }` — tests always exercise local source, never PyPI.
- Published packages declare `requires-python = ">=3.12"` but ruff `target-version = "py314"`; test packages pin `>=3.14,<3.15`. Runtime code must stay 3.12-compatible (past releases 4.0.1/4.0.2 were pure 3.12/3.13 syntax breakages).
- Version lives **only** in each package's `pyproject.toml` `project.version`. No `__version__` attribute anywhere.
- Every published package keeps a `CHANGELOG.md` that **must** follow keep-a-changelog 1.1.0; section headers are written `_*Added*_` / `_*Fixed*_` / `_*Changed*_`. Bump version + changelog entry (dated) in the same change.
- No CI workflows (`.github/` absent). Quality gates are pre-commit + Claude Code hooks only — see `mem:task_completion`.

Further: `mem:tech_stack`, `mem:conventions`, `mem:suggested_commands`, `mem:task_completion`.
