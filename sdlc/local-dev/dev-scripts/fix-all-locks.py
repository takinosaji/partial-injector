import os
import glob
import subprocess
import argparse


def find_pyproject_files(project_dir: str):
    """Find all pyproject.toml files sorted by nesting level (shallowest first)."""
    toml_files = glob.glob(os.path.join(project_dir, "**/pyproject.toml"), recursive=True)
    return sorted(toml_files, key=lambda x: x.count(os.sep))


def run_poetry_lock(toml_files):
    """Run `poetry lock` for each pyproject.toml file's project directory."""
    for toml_file in toml_files:
        project_path = os.path.dirname(toml_file)
        try:
            print(f"Locking dependencies for {project_path}...")
            subprocess.check_call(["poetry", "lock"], cwd=project_path)
            print(f"Successfully locked dependencies for {project_path}.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to lock dependencies for {project_path}. Error: {e}")
            raise e


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run 'poetry lock' for all nested pyproject.toml files.")
    parser.add_argument('project_dir', type=str, help="Path to the directory containing Poetry projects.")
    args = parser.parse_args()

    toml_files = find_pyproject_files(args.project_dir)
    if not toml_files:
        print(f"No pyproject.toml files found in {args.project_dir}.")
    else:
        run_poetry_lock(toml_files)

