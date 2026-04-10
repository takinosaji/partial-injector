import argparse
import glob
import logging
import os
import subprocess

logger = logging.getLogger(__name__)


def install_latest_wheel(wheel_folder: str, package: str | None = None) -> None:
    """Find and install the latest wheel file from the specified folder."""
    wheel_files = glob.glob(os.path.join(wheel_folder, "*.whl"))

    if package:
        wheel_files = [
            w for w in wheel_files if os.path.basename(w).startswith(package)
        ]

    wheel_files = sorted(wheel_files, key=os.path.getmtime, reverse=True)

    if not wheel_files:
        logger.info("No wheel files found in %s.", wheel_folder)
        return

    latest_wheel = wheel_files[0]

    try:
        subprocess.check_call(
            [
                "pip",
                "install",
                "--no-cache-dir",
                "--find-links",
                wheel_folder,
                latest_wheel,
            ]
        )
        logger.info("Successfully installed %s.", latest_wheel)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to install %s. Error: %s", latest_wheel, e)
        raise e


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Install the latest wheel from a specified directory."
    )
    parser.add_argument(
        "wheel_folder", type=str, help="Path to the directory containing wheel files."
    )
    parser.add_argument(
        "--package",
        type=str,
        default=None,
        help="Filter wheels by package name prefix (e.g. new_python_app_primary_adapter).",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    install_latest_wheel(args.wheel_folder, args.package)
