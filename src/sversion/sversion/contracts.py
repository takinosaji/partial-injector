"""
contracts — shared type aliases for sversion.

Types
-----
Version          : A version string (e.g. ``"1.2.3"``).
VersionRetriever : Callable that accepts a path and returns a ``Version``.
"""

from collections.abc import Callable

type Version = str
type VersionRetriever = Callable[[str], Version]
