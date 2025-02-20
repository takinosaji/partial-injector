import os.path
import shutil
import subprocess
import argparse

def install_package(packages: list[str], version_file_path: str, editable: bool):
    for path in packages:
        try:
            version_file_target_path = f"{path}/VERSION.txt"
            if not os.path.exists(version_file_target_path):
                shutil.copyfile(version_file_path, version_file_target_path)

            command = ['pip', 'install', '--no-cache-dir']
            if editable:
                command.append('-e')
            command.append(path)
            subprocess.check_call(command)
            print(f'Successfully installed {path} in {'development' if editable else 'production'} mode.')
        except subprocess.CalledProcessError as e:
            print(f'Failed to install {path} in {'development' if editable else 'production'} mode. Error: {e}')
            raise e

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Primary Adapters')
    parser.add_argument('--editable', '-e', action='store_true', help='Editable')
    parser.add_argument('--version_file_path', type=str, help='Path to the version file')
    parser.add_argument('--packages', nargs='+', help='Paths to folders with setup.py files')
    args = parser.parse_args()

    install_package(args.packages, args.version_file_path, args.editable)