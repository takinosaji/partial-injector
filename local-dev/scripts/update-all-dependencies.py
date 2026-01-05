import os
import glob
import subprocess
import argparse

def find_nested_toml_files(project_dir: str):
    """Find all pyproject.toml files sorted by nesting level (deepest first)."""
    toml_files = glob.glob(os.path.join(project_dir, "**/pyproject.toml"), recursive=True)
    return sorted(toml_files, key=lambda x: x.count(os.sep), reverse=True)

def update_packages(toml_files):
    """Run `poetry update` for each pyproject.toml file."""
    for toml_file in toml_files:
        project_path = os.path.dirname(toml_file)
        try:
            print(f"Updating packages for {project_path}...")
            subprocess.check_call(["poetry", "update"], cwd=project_path)
            print(f"Successfully updated packages for {project_path}.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to update packages for {project_path}. Error: {e}")
            raise e

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Recursively update packages for all nested pyproject.toml files.")
    parser.add_argument('project_dir', type=str, help="Path to the directory containing Poetry projects.")
    args = parser.parse_args()

    toml_files = find_nested_toml_files(args.project_dir)
    if not toml_files:
        print(f"No pyproject.toml files found in {args.project_dir}.")
    else:
        update_packages(toml_files)