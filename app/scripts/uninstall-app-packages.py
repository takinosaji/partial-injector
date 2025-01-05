import subprocess

# TODO: move to dev folder in root and include resolution of venv

# List of package names to be uninstalled
packages_to_uninstall = [
    'partial-injector',
    'partial-injector-demo',
    'partial-injector-tests'
]

def uninstall_packages(package_paths):
    for package in package_paths:
        try:
            subprocess.check_call(['pip', 'uninstall', '-y', package])
            print(f'Successfully uninstalled {package}.')
        except subprocess.CalledProcessError as e:
            print(f'Failed to uninstall {package}. Error: {e}')

if __name__ == '__main__':
    uninstall_packages(packages_to_uninstall)