import argparse
import glob
import logging
import os
import sys

logger = logging.getLogger(__name__)


def find_lock_files(project_dir: str, recursive: bool = False) -> list[str]:
    """Find uv.lock files under project_dir.

    If recursive is False, only uv.lock directly in project_dir is returned.
    If True, all nested uv.lock files are returned.
    """
    if recursive:
        return glob.glob(os.path.join(project_dir, "**", "uv.lock"), recursive=True)
    else:
        path = os.path.join(project_dir, "uv.lock")
        return [path] if os.path.exists(path) else []


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete uv.lock files found under the given directories."
    )
    parser.add_argument(
        "project_dirs",
        type=str,
        nargs="+",
        metavar="project_dir",
        help="One or more directories to search for uv.lock files.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Find and delete all uv.lock files recursively.",
    )
    args = parser.parse_args()

    lock_files = []
    for project_dir in args.project_dirs:
        lock_files.extend(find_lock_files(project_dir, recursive=args.recursive))

    if not lock_files:
        logger.info("No uv.lock files found.")
        sys.exit(0)

    for lock_file in lock_files:
        try:
            os.remove(lock_file)
            logger.info("Deleted: %s", lock_file)
        except OSError as e:
            logger.error("Failed to delete %s. Error: %s", lock_file, e)
            sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
