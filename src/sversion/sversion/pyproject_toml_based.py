"""
pyproject_toml_based — retrieve a package version from ``pyproject.toml``.

Starting at *start_search_path* (a file or directory), ``get_version`` walks up
the directory tree until it finds *project_file_name* or reaches the filesystem
root.  The first match is parsed as TOML and the version is read from either
``project.version`` (PEP 517/518) or ``tool.poetry.version`` (Poetry layout).
"""

import os

import toml

from .contracts import Version, VersionRetriever
from .error_handling import VersionNotFoundException


def __get_version(
    start_search_path: str, project_file_name: str = "pyproject.toml"
) -> Version:
    """Walk up the directory tree from *start_search_path* looking for *project_file_name*.

    Parameters
    ----------
    start_search_path:
        File or directory to start searching from.  When a file path is given
        the search begins in its parent directory.
    project_file_name:
        Name of the project file to look for (default: ``"pyproject.toml"``).

    Checks ``project.version`` first, then ``tool.poetry.version``.

    Raises ``VersionNotFoundException`` when no file is found, the version key
    is absent in all candidates, or a directory cannot be read due to a
    permission error.
    """
    error_message = f"{project_file_name} was not found in the module folder or one of the parent folders."

    if os.path.isfile(start_search_path):
        start_search_path = os.path.dirname(start_search_path)

    current_path = start_search_path

    while current_path != os.path.dirname(current_path):
        project_file_path = os.path.join(current_path, project_file_name)
        try:
            if os.path.exists(project_file_path):
                with open(project_file_path) as project_file:
                    project_data = toml.load(project_file)
                    if (
                        "project" in project_data
                        and "version" in project_data["project"]
                    ):
                        return project_data["project"]["version"]
                    if "tool" in project_data and "poetry" in project_data["tool"]:
                        return project_data["tool"]["poetry"]["version"]

            current_path = os.path.dirname(current_path)
        except PermissionError:
            raise VersionNotFoundException(error_message) from None

    raise VersionNotFoundException(error_message)


get_version: VersionRetriever = __get_version
