import os
import glob
import subprocess
import argparse
from typing import List, Optional

def has_dependency_group(pyproject_file: str, group_name: str) -> bool:
    """Check if a specific dependency group exists in pyproject.toml."""
    try:
        with open(pyproject_file, "r") as f:
            return f"[tool.poetry.group.{group_name}.dependencies]" in f.read()
    except FileNotFoundError:
        return False

def install_poetry_projects(
    project_dir: str,
    no_root: bool = False,
    without: Optional[List[str]] = None,
    all_groups: bool = False,
    recursive: bool = False,
) -> None:
    """Find and install Poetry projects in the specified directory.

    If ``recursive`` is False, only a ``pyproject.toml`` directly inside
    ``project_dir`` is considered. If True, all matching files in
    subdirectories are processed as well.
    """
    original_cwd = os.getcwd()

    if recursive:
        pattern = os.path.join(project_dir, "**", "pyproject.toml")
    else:
        pattern = os.path.join(project_dir, "pyproject.toml")

    pyproject_files = sorted(glob.glob(pattern, recursive=recursive))

    if not pyproject_files:
        print(f"No pyproject.toml files found in {project_dir} (recursive={recursive}).")
        return

    try:
        for pyproject in pyproject_files:
            project_path = os.path.dirname(pyproject)

            command_flags: List[str] = []
            if no_root:
                command_flags.append("--no-root")
            if without:
                for group in without:
                    if has_dependency_group(pyproject, group):
                        command_flags.extend(["--without", group])
            if all_groups and not without:
                command_flags.append("--all-groups")

            try:
                print(f"Installing dependencies for {project_path}...")
                os.chdir(project_path)
                subprocess.check_call(["poetry", "install"] + command_flags)
                print(f"Successfully installed dependencies for {project_path}.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install dependencies for {project_path}. Error: {e}")
                raise e
            finally:
                os.chdir(original_cwd)
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Install Poetry dependencies for projects inside a directory. "
            "By default only the pyproject.toml directly in project_dir is used; "
            "use --recursive to also process subdirectories."
        )
    )
    parser.add_argument(
        "project_dir",
        type=str,
        help="Path to the directory containing Poetry projects.",
    )
    parser.add_argument(
        "--no-root",
        action="store_true",
        help="Include the --no-root option during installation.",
    )
    parser.add_argument(
        "--without",
        nargs="*",
        help="Dependency groups to exclude if they exist.",
    )
    parser.add_argument(
        "--all-groups",
        action="store_true",
        help="Include the --all-groups option during installation.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help=(
            "Search for pyproject.toml files recursively under project_dir. "
            "If omitted, only the top-level pyproject.toml in project_dir is used."
        ),
    )

    args = parser.parse_args()

    install_poetry_projects(
        args.project_dir,
        args.no_root,
        args.without,
        args.all_groups,
        args.recursive,
    )
