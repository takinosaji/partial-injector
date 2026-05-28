"""PostToolUse hook: check-only ruff format, ruff lint, and bandit on edited Python files.

No files are modified. Issues are injected into Claude's context so the agent can fix them.
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _lint_shared import run_bandit, run_ruff_check, run_ruff_format  # noqa: E402


@dataclass(frozen=True)
class ToolInput:
    file_path: str = ""


@dataclass(frozen=True)
class HookInput:
    tool_name: str = ""
    tool_input: ToolInput = field(default_factory=ToolInput)


def parse_hook_input(raw: dict) -> HookInput:
    raw_tool_input: dict = raw.get("tool_input") or {}
    return HookInput(
        tool_name=raw.get("tool_name", ""),
        tool_input=ToolInput(file_path=raw_tool_input.get("file_path", "")),
    )


def main() -> int:
    try:
        hook_input = parse_hook_input(json.load(sys.stdin))
    except Exception as exc:
        print(f"Hook failed unexpectedly: {exc}", file=sys.stderr)
        return 2

    file_path = hook_input.tool_input.file_path
    if not file_path.endswith(".py"):
        return 0

    issues = [
        result
        for result in [
            run_ruff_format([file_path], check=True),
            run_ruff_check([file_path], fix=False),
            run_bandit([file_path], recursive=False),
        ]
        if result is not None
    ]

    if issues:
        payload = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    f"Lint/SAST check for {file_path} — issues require your attention:\n\n"
                    + "\n\n".join(issues)
                ),
            }
        }
        print(json.dumps(payload))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
