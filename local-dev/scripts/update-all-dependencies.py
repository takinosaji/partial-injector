import os
import glob
import subprocess
import argparse

def find_nested_toml_files(project_dir: str, recursive: bool = False):
    """Find pyproject.toml files.

    If ``recursive`` is False, only ``pyproject.toml`` directly inside
    ``project_dir`` is returned. If True, all nested files are returned,
    sorted by nesting level (deepest first).
    """
    if recursive:
        toml_files = glob.glob(os.path.join(project_dir, "**", "pyproject.toml"), recursive=True)
        return sorted(toml_files, key=lambda x: x.count(os.sep), reverse=True)
    else:
        toml_file = os.path.join(project_dir, "pyproject.toml")
        return [toml_file] if os.path.exists(toml_file) else []

def update_packages(toml_files):
    """Run `poetry update` for each pyproject.toml file."""
    original_cwd = os.getcwd()
    for toml_file in toml_files:
        project_path = os.path.dirname(toml_file)
        try:
            print(f"Updating packages for {project_path}...")
            os.chdir(project_path)
            subprocess.check_call(["poetry", "update"])
            print(f"Successfully updated packages for {project_path}.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to update packages for {project_path}. Error: {e}")
            raise e
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Update packages for Poetry projects inside a directory. "
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
        "--recursive",
        action="store_true",
        help=(
            "Search for pyproject.toml files recursively under project_dir. "
            "If omitted, only the top-level pyproject.toml in project_dir is used."
        ),
    )

    args = parser.parse_args()

    toml_files = find_nested_toml_files(args.project_dir, recursive=args.recursive)
    if not toml_files:
        print(f"No pyproject.toml files found in {args.project_dir} (recursive={args.recursive}).")
    else:
        update_packages(toml_files)