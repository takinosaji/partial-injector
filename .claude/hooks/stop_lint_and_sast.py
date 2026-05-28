"""Stop hook: applies ruff format, ruff check --fix, and bandit across src/ and tests/.

Only runs if Python files were modified (tracked by git or untracked).
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _lint_shared import run_bandit, run_ruff_check, run_ruff_format  # noqa: E402

_TARGETS = ["src", "tests"]


def _has_python_changes() -> bool:
    """Return True if any .py files are modified, staged, or untracked."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    return any(line.endswith(".py") for line in result.stdout.splitlines())


def main() -> int:
    if not _has_python_changes():
        return 0

    run_ruff_format(_TARGETS, check=False)

    issues = [
        result
        for result in [
            run_ruff_check(_TARGETS, fix=True),
            run_bandit(_TARGETS, recursive=True),
        ]
        if result is not None
    ]

    if issues:
        message = "Formatting applied. Remaining issues:\n\n" + "\n\n".join(issues)
    else:
        message = "Formatting and lint fixes applied. No remaining issues."

    print(json.dumps({"systemMessage": message}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
