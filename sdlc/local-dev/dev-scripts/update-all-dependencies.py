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
    is returned. If True, all nested files are returned sorted deepest-first
    so inner packages are upgraded before outer ones.
    """
    if recursive:
        files = glob.glob(
            os.path.join(project_dir, "**", "pyproject.toml"), recursive=True
        )
        return sorted(files, key=lambda x: x.count(os.sep), reverse=True)
    else:
        path = os.path.join(project_dir, "pyproject.toml")
        return [path] if os.path.exists(path) else []


def upgrade_project(project_path: str) -> None:
    """Run uv lock --upgrade and uv sync in the given project directory."""
    logger.info("Upgrading dependencies for %s...", project_path)
    try:
        subprocess.check_call(["uv", "lock", "--upgrade"], cwd=project_path)
        subprocess.check_call(["uv", "sync", "--all-groups"], cwd=project_path)
        logger.info("Successfully upgraded dependencies for %s.", project_path)
    except subprocess.CalledProcessError as e:
        logger.error(
            "Failed to upgrade dependencies for %s. Error: %s", project_path, e
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Upgrade dependencies to their latest allowed versions. "
            "Without --recursive, only the pyproject.toml directly in project_dir "
            "is processed. With --recursive, all nested pyproject.toml files are "
            "processed deepest-first."
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
            upgrade_project(project_path)
        except subprocess.CalledProcessError:
            sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
