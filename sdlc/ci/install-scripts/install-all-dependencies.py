import argparse
import glob
import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)


def find_pyproject_files(project_dir: str, recursive: bool = False) -> list[str]:
    """Find pyproject.toml files under project_dir.

    If recursive is False, only the pyproject.toml directly in project_dir
    is returned. If True, all nested files are returned sorted shallowest-first
    so outer workspace members are installed before inner ones.
    """
    if recursive:
        files = glob.glob(
            os.path.join(project_dir, "**", "pyproject.toml"), recursive=True
        )
        return sorted(files, key=lambda x: x.count(os.sep))
    else:
        path = os.path.join(project_dir, "pyproject.toml")
        return [path] if os.path.exists(path) else []


def sync_project(
    project_path: str,
    all_groups: bool = False,
    no_dev: bool = False,
    without: list[str] | None = None,
    only_group: list[str] | None = None,
    all_extras: bool = False,
    extras: list[str] | None = None,
) -> None:
    """Run uv sync in the given project directory."""
    command = ["uv", "sync"]
    if all_groups:
        command.append("--all-groups")
    if no_dev:
        command.append("--no-dev")
    if without:
        for group in without:
            command += ["--no-group", group]
    if only_group:
        for group in only_group:
            command += ["--group", group]
    if all_extras:
        command.append("--all-extras")
    elif extras:
        for extra in extras:
            command += ["--extra", extra]

    logger.info("Installing dependencies for %s...", project_path)
    try:
        subprocess.check_call(command, cwd=project_path)
        logger.info("Successfully installed dependencies for %s.", project_path)
    except subprocess.CalledProcessError as e:
        logger.error(
            "Failed to install dependencies for %s. Error: %s", project_path, e
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run 'uv sync' for pyproject.toml files found under project_dir. "
            "Without --recursive, only the pyproject.toml directly in project_dir "
            "is processed. With --recursive, all nested pyproject.toml files are "
            "processed shallowest-first."
        )
    )
    parser.add_argument(
        "project_dirs",
        type=str,
        nargs="+",
        metavar="project_dir",
        help="One or more directories containing pyproject.toml files.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Find and process all pyproject.toml files recursively.",
    )
    parser.add_argument(
        "--all-groups",
        action="store_true",
        help="Include all dependency groups.",
    )
    parser.add_argument(
        "--no-dev",
        action="store_true",
        help="Exclude the default dev dependency group.",
    )
    parser.add_argument(
        "--without",
        nargs="+",
        metavar="GROUP",
        help="Exclude specific dependency groups.",
    )
    parser.add_argument(
        "--only-group",
        nargs="+",
        metavar="GROUP",
        help="Include only the specified dependency groups.",
    )
    parser.add_argument(
        "--all-extras",
        action="store_true",
        help="Include all optional extras.",
    )
    parser.add_argument(
        "--extra",
        nargs="+",
        metavar="EXTRA",
        help="Include specific optional extras (e.g. --extra llm-all monitoring).",
    )
    args = parser.parse_args()

    files = []
    for project_dir in args.project_dirs:
        found = find_pyproject_files(project_dir, recursive=args.recursive)
        if not found:
            logger.info("No pyproject.toml files found in %s.", project_dir)
            sys.exit(1)
        files.extend(found)

    for pyproject in files:
        project_path = os.path.dirname(pyproject)
        try:
            sync_project(
                project_path,
                all_groups=args.all_groups,
                no_dev=args.no_dev,
                without=args.without,
                only_group=args.only_group,
                all_extras=args.all_extras,
                extras=args.extra,
            )
        except subprocess.CalledProcessError:
            sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
