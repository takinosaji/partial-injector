from sversion.file_based import get_version
__version__ = get_version(__file__)
__author__ = "kostiantyn.chomakov@gmail.com"

# Import submodules

from . import test_case_injected_async_output

__all__ = ['test_case_injected_async_output']