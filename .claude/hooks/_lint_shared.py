"""Shared lint/SAST runners used by both PostToolUse and Stop hooks."""

import subprocess


def run_ruff_format(targets: list[str], check: bool = False) -> str | None:
    flags = ["--check"] if check else []
    result = subprocess.run(
        ["uv", "run", "ruff", "format"] + flags + targets,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"ruff format: file needs reformatting:\n{result.stdout}{result.stderr}".strip()
    return None


def run_ruff_check(targets: list[str], fix: bool = False) -> str | None:
    flags = ["--fix"] if fix else []
    result = subprocess.run(
        ["uv", "run", "ruff", "check"] + flags + targets,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        label = "unfixable violations remain" if fix else "violations"
        return f"ruff check — {label}:\n{result.stdout}{result.stderr}".strip()
    return None


def run_bandit(targets: list[str], recursive: bool = False) -> str | None:
    flags = ["-r"] if recursive else []
    result = subprocess.run(
        ["uv", "run", "bandit"] + flags + ["-c", ".bandit"] + targets,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return (
            f"bandit — security issues found:\n{result.stdout}{result.stderr}".strip()
        )
    return None
