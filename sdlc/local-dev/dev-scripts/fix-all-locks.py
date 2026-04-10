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
    is returned. If True, all nested files are returned sorted shallowest-first.
    """
    if recursive:
        files = glob.glob(
            os.path.join(project_dir, "**", "pyproject.toml"), recursive=True
        )
        return sorted(files, key=lambda x: x.count(os.sep))
    else:
        path = os.path.join(project_dir, "pyproject.toml")
        return [path] if os.path.exists(path) else []


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run 'uv lock' for pyproject.toml files found under the given directories. "
            "Note: uv always writes a single uv.lock at the workspace root, "
            "so --recursive runs uv lock once per found project directory but "
            "all invocations update the same workspace lock file."
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
        logger.info("Locking dependencies for %s...", project_path)
        try:
            subprocess.check_call(["uv", "lock"], cwd=project_path)
            logger.info("Successfully locked dependencies for %s.", project_path)
        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to lock dependencies for %s. Error: %s", project_path, e
            )
            sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
