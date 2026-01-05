import os
import glob
import argparse

def delete_poetry_lock_files(project_dir: str):
    """Find and delete all poetry.lock files in the specified directory."""
    lock_files = glob.glob(os.path.join(project_dir, "**/poetry.lock"), recursive=True)

    if not lock_files:
        print(f"No poetry.lock files found in {project_dir}.")
        return

    for lock_file in lock_files:
        try:
            os.remove(lock_file)
            print(f"Deleted: {lock_file}")
        except OSError as e:
            print(f"Failed to delete {lock_file}. Error: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Delete all poetry.lock files in a specified directory.")
    parser.add_argument('project_dir', type=str, help="Path to the directory containing Poetry projects.")
    args = parser.parse_args()

    delete_poetry_lock_files(args.project_dir)