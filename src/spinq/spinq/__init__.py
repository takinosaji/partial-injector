"""
spinq — LINQ-style collection helpers for Python.

Sub-modules
-----------
lists : Functions for filtering, searching, projecting, and aggregating lists.
dicts : Functions for searching and indexing dictionaries.
"""

__author__ = "kostiantyn.chomakov@gmail.com"

from . import dicts, lists

__all__ = ["lists", "dicts"]
