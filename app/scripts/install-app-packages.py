import subprocess
import argparse

def install_editable(packages: list[str], editable: bool):
    for path in packages:
        try:
            command = ['pip', 'install']
            if editable:
                command.append('-e')
            command.append(path)
            subprocess.check_call(command)
            print(f'Successfully installed {path} in {'development' if editable else 'production'} mode.')
        except subprocess.CalledProcessError as e:
            print(f'Failed to install {path} in {'development' if editable else 'production'} mode. Error: {e}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Kafka Primary Adapter')
    parser.add_argument('--editable', '-e', action='store_true', help='Editable')
    parser.add_argument('--packages', nargs='+', help='Paths to folders with setup.py files')
    args = parser.parse_args()

    install_editable(args.packages, args.editable)