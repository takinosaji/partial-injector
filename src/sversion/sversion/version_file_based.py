"""
version_file_based — retrieve a package version from a ``VERSION.txt`` file.

Starting at *start_search_path* (a file or directory), ``get_version`` walks up
the directory tree until it finds *version_file_name* or reaches the filesystem
root.  The first match wins; its trimmed contents are returned as the version string.
"""

import os

from .contracts import Version, VersionRetriever
from .error_handling import VersionNotFoundException


def __get_version(start_search_path: str, version_file_name: str = "VERSION.txt") -> Version:
    """Walk up the directory tree from *start_search_path* looking for *version_file_name*.

    Parameters
    ----------
    start_search_path:
        File or directory to start searching from.  When a file path is given
        the search begins in its parent directory.
    version_file_name:
        Name of the version file to look for (default: ``"VERSION.txt"``).

    Returns the trimmed content of the first matching file found.

    Raises ``VersionNotFoundException`` when no file is found or a directory
    cannot be read due to a permission error.
    """
    error_message = f"{version_file_name} was not found in the module folder or one of the parent folders."

    if os.path.isfile(start_search_path):
        start_search_path = os.path.dirname(start_search_path)

    current_path = start_search_path

    while current_path != os.path.dirname(current_path):
        version_file_path = os.path.join(current_path, version_file_name)
        try:
            if os.path.exists(version_file_path):
                with open(version_file_path) as f:
                    return f.read().strip()

            current_path = os.path.dirname(current_path)
        except PermissionError:
            raise VersionNotFoundException(error_message)

    raise VersionNotFoundException(error_message)


get_version: VersionRetriever = __get_version
