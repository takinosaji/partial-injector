import os
import toml

from .contracts import Version, VersionRetriever
from .error_handling import VersionNotFoundException

def __get_version(start_search_path: str, project_file_name: str = "pyproject.toml") -> Version:
    error_message = f"{project_file_name} was not found in the module folder or one of the parent folders."

    if os.path.isfile(start_search_path):
        start_search_path = os.path.dirname(start_search_path)

    current_path = start_search_path

    while current_path != os.path.dirname(current_path):
        project_file_path = os.path.join(current_path, project_file_name)
        try:
            if os.path.exists(project_file_path):
                with open(project_file_path, 'r') as project_file:
                    project_data = toml.load(project_file)
                    if "tool" in project_data and "poetry" in project_data["tool"]:
                        return project_data["tool"]["poetry"]["version"]

            current_path = os.path.dirname(current_path)
        except PermissionError:
            raise VersionNotFoundException(error_message)

    raise VersionNotFoundException(error_message)
get_version: VersionRetriever = __get_version