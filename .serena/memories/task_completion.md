# Task Completion

Run from workspace root, in order:

```
uv run ruff format .
uv run ruff check . --fix
uv run bandit -r -c .bandit src tests sdlc
uv run pytest
```

Automated already — do not be surprised by it:
- `.claude/settings.json` registers a **PostToolUse** hook (`.claude/hooks/post_tool_use_lint_and_sast.py`) that runs ruff format-check + ruff check + bandit on every `.py` file you Write/Edit, and a **Stop** hook (`stop_lint_and_sast.py`) that runs ruff format + `check --fix` + bandit over the session's touched files. Hook failures surface as tool feedback; fix them rather than working around them.
- `pre-commit` runs ruff + bandit over `^(src|tests|sdlc)/` at commit time.

Additionally, when the change is user-visible in a published package (`partial-injector`, `spinq`, `sversion`):
1. bump `project.version` in that package's `pyproject.toml`,
2. add a dated keep-a-changelog entry to that package's `CHANGELOG.md`,
3. update the package's `CLAUDE.md` if module responsibilities or invariants changed,
4. verify runtime code still parses under Python 3.12 (`requires-python = ">=3.12"` despite the 3.14 dev env).

There is no type checker (no mypy/pyright) and no CI pipeline — these local commands are the entire gate.
