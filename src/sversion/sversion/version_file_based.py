import os

from .contracts import Version, VersionRetriever
from .error_handling import VersionNotFoundException

def __get_version(start_search_path: str, version_file_name: str = "VERSION.txt") -> Version:
    error_message = f"{version_file_name} was not found in the module folder or one of the parent folders."

    if os.path.isfile(start_search_path):
        start_search_path = os.path.dirname(start_search_path)

    current_path = start_search_path

    while current_path != os.path.dirname(current_path):
        version_file_path = os.path.join(current_path, version_file_name)
        try:
            if os.path.exists(version_file_path):
                return open(version_file_path).read().strip()

            current_path = os.path.dirname(current_path)
        except PermissionError:
            raise VersionNotFoundException(error_message)

    raise VersionNotFoundException(error_message)
get_version: VersionRetriever = __get_version