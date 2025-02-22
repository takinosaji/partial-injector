from sversion.file_based import get_version
__version__ = get_version(__file__)
__author__ = "kostiantyn.chomakov@gmail.com"

# Import submodules

from . import test_file_based

__all__ = ['test_file_based']