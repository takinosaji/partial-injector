"""
dicts — LINQ-style helpers for Python dictionaries.

Functions
---------
first_                  Return the first ``(key, value)`` pair matching a predicate; raise on miss.
first_or_none_          Return the first matching ``(key, value)`` pair or ``None``.
get_key_by_index_       Return the key at a given insertion-order position.
get_key_value_by_index_ Return the ``(key, value)`` pair at a given insertion-order position.
"""

from itertools import islice
from typing import Callable, TypeVar, Optional

K = TypeVar('K')
V = TypeVar('V')


def first_(dictionary: dict[K, V], predicate: Callable[[V], bool] = lambda x: True) -> tuple[K, V]:
    """Return the first ``(key, value)`` pair whose value satisfies *predicate*.

    Raises ``ValueError`` when no value matches.
    """
    try:
        return next((k, v) for k, v in dictionary.items() if predicate(v))
    except StopIteration:
        raise ValueError("No elements match the predicate.")


def first_or_none_(dictionary: dict[K, V], predicate: Callable[[V], bool] = lambda x: True) -> Optional[tuple[K, V]]:
    """Return the first ``(key, value)`` pair whose value satisfies *predicate*, or ``None``."""
    return next(((k, v) for k, v in dictionary.items() if predicate(v)), None)


def get_key_by_index_(dictionary: dict[K, V], index: int) -> K:
    """Return the key at insertion-order position *index*.

    Raises ``ValueError`` when *index* is out of range.
    """
    try:
        return next(islice(dictionary, index, index + 1))
    except StopIteration:
        raise ValueError("Index out of range.")


def get_key_value_by_index_(dictionary: dict[K, V], index: int) -> tuple[K, V]:
    """Return the ``(key, value)`` pair at insertion-order position *index*.

    Raises ``ValueError`` when *index* is out of range.
    """
    try:
        return next(islice(dictionary.items(), index, index + 1))
    except StopIteration:
        raise ValueError("Index out of range.")
