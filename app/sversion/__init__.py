from .file_based import get_version
__version__ = get_version(__file__)
__author__ = "kostiantyn.chomakov@gmail.com"

# Import submodules

from . import file_based, error_handling, contracts

__all__ = ['file_based',
           'error_handling',
           'contracts']