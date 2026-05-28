"""
sversion — version string retrieval for Python packages.

Sub-modules
-----------
version_file_based   : Retrieve version from a ``VERSION.txt`` file.
pyproject_toml_based : Retrieve version from ``pyproject.toml``.
contracts            : Shared type aliases (``Version``, ``VersionRetriever``).
error_handling       : ``VersionNotFoundException``.
"""

__author__ = "kostiantyn.chomakov@gmail.com"

from . import contracts, error_handling, pyproject_toml_based, version_file_based

__all__ = ["version_file_based", "pyproject_toml_based", "error_handling", "contracts"]
