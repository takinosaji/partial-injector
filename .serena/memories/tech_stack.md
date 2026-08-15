# Tech Stack

- Python 3.14 dev env (`.venv` at repo root, shared by all workspace members). Library code must stay 3.12-compatible.
- **uv** — workspace manager, resolver, lockfile (`uv.lock`, single lock at root), publisher. Never use pip/poetry here.
- **hatchling** — build backend for every member; wheel contents selected via `[tool.hatch.build.targets.wheel] packages = ["<underscored_pkg>"]`.
- **ruff** — linter *and* formatter (no black/isort). Config at root `pyproject.toml`: line-length 88, select `E,W,F,I,N,UP,B,SIM`, ignore `E501,UP042`, `__init__.py` exempt from `F401`. `known-first-party` lists all five underscored package names — add new members there.
- **bandit** — SAST, config `.bandit` at root (skips B101, B104, B602, B603, B404, B607).
- **pytest** + **pytest-asyncio** (`asyncio_default_fixture_loop_scope = "session"`, `--import-mode=importlib`). **faker** is a test dep of test-partial-injector.
- **pre-commit** (`.pre-commit-config.yaml`): ruff + bandit over `^(src|tests|sdlc)/`.
- Runtime deps: `partial-injector` and `spinq` have **none**; `sversion` depends on `toml`.
- Dev-only deps live in the root `[dependency-groups] dev`, not in members.
