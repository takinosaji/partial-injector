from sversion.file_based import get_version
__version__ = get_version(__file__)
__author__ = "kostiantyn.chomakov@gmail.com"

# Import submodules

from . import partial_container, error_handling

__all__ = ['partial_container', 'error_handling']