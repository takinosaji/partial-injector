"""
lists — LINQ-style helpers for Python lists.

Functions
---------
first_                    Return the first element matching a predicate; raise on miss.
first_or_none_            Return the first matching element or ``None``.
first_or_none_with_index_ Return ``(index, element)`` for the first match or ``None``.
last_                     Return the last matching element; raise on miss.
last_or_none_             Return the last matching element or ``None``.
single_                   Return the sole matching element; raise if 0 or >1 match.
single_or_none_           Return the sole matching element or ``None``; raise if >1 match.
filter_                   Keep elements that satisfy a predicate.
except_                   Remove elements present in an exclusion list.
without_                  Remove elements that satisfy a predicate.
union_                    Distinct union of two lists.
select_                   Project each element through a selector.
select_many_              Flat-map: project then flatten one level.
where_                    Alias for ``filter_``.
where_with_index_         Filter returning ``{index: element}`` for matched positions.
distinct_                 Remove duplicates (order not preserved).
order_by_                 Sort ascending by a key selector.
order_by_descending_      Sort descending by a key selector.
any_                      Return ``True`` if any element satisfies a predicate.
all_                      Return ``True`` if every element satisfies a predicate.
none_                     Return ``True`` if no element satisfies a predicate.
"""

from typing import Callable, TypeVar, Optional

T = TypeVar('T')
T2 = TypeVar('T2')
TKey = TypeVar('TKey')


def first_(sequence: list[T], predicate: Callable[[T], bool] = lambda x: True) -> T:
    """Return the first element in *sequence* that satisfies *predicate*.

    Raises ``ValueError`` when no element matches.
    """
    try:
        return next(x for x in sequence if predicate(x))
    except StopIteration:
        raise ValueError("No elements match the predicate.")


def first_or_none_(sequence: list[T], predicate: Callable[[T], bool] = lambda x: True) -> Optional[T]:
    """Return the first element in *sequence* that satisfies *predicate*, or ``None``."""
    return next((x for x in sequence if predicate(x)), None)


def first_or_none_with_index_(sequence: list[T], predicate: Callable[[T], bool] = lambda x: True) -> Optional[tuple[int, T]]:
    """Return ``(index, element)`` for the first match, or ``None`` when nothing matches."""
    return next(((i, x) for i, x in enumerate(sequence) if predicate(x)), None)


def last_(sequence: list[T], predicate: Callable[[T], bool] = lambda x: True) -> T:
    """Return the last element in *sequence* that satisfies *predicate*.

    Raises ``ValueError`` when no element matches.
    """
    try:
        return next(x for x in reversed(sequence) if predicate(x))
    except StopIteration:
        raise ValueError("No elements match the predicate.")


def last_or_none_(sequence: list[T], predicate: Callable[[T], bool] = lambda x: True) -> Optional[T]:
    """Return the last element in *sequence* that satisfies *predicate*, or ``None``."""
    return next((x for x in reversed(sequence) if predicate(x)), None)


def single_(sequence: list[T], predicate: Callable[[T], bool]) -> T:
    """Return the sole element in *sequence* that satisfies *predicate*.

    Raises ``ValueError`` when zero or more than one element matches.
    """
    filtered = [x for x in sequence if predicate(x)]
    if len(filtered) == 1:
        return filtered[0]
    if len(filtered) == 0:
        raise ValueError("No elements match the predicate.")
    raise ValueError("More than one element matches the predicate.")


def single_or_none_(sequence: list[T], predicate: Callable[[T], bool]) -> Optional[T]:
    """Return the sole matching element, ``None`` when nothing matches.

    Raises ``ValueError`` when more than one element satisfies *predicate*.
    """
    filtered = [x for x in sequence if predicate(x)]
    if len(filtered) == 1:
        return filtered[0]
    if len(filtered) == 0:
        return None
    raise ValueError("More than one element matches the predicate.")


def filter_(sequence: list[T], predicate: Callable[[T], bool]) -> list[T]:
    """Return all elements in *sequence* that satisfy *predicate*."""
    return [x for x in sequence if predicate(x)]


def except_(sequence: list[T], exclusions: list[T]) -> list[T]:
    """Return *sequence* with every element that appears in *exclusions* removed."""
    return [x for x in sequence if x not in exclusions]


def without_(sequence: list[T], predicate: Callable[[T], bool]) -> list[T]:
    """Return *sequence* with every element that satisfies *predicate* removed."""
    return [x for x in sequence if not predicate(x)]


def union_(sequence1: list[T], sequence2: list[T]) -> list[T]:
    """Return the distinct union of *sequence1* and *sequence2*.

    Order of the result is not guaranteed.
    """
    return list(set(sequence1) | set(sequence2))


def select_(sequence: list[T], selector: Callable[[T], T2]) -> list[T2]:
    """Project each element of *sequence* through *selector*."""
    return [selector(x) for x in sequence]


def select_many_(sequence: list[T], selector: Callable[[T], list[T2]]) -> list[T2]:
    """Flat-map *sequence*: apply *selector* to each element then flatten one level."""
    return [item for x in sequence for item in selector(x)]


def where_(sequence: list[T], predicate: Callable[[T], bool]) -> list[T]:
    """Return all elements in *sequence* that satisfy *predicate*.

    Alias for ``filter_``.
    """
    return [x for x in sequence if predicate(x)]


def where_with_index_(sequence: list[T], predicate: Callable[[T], bool]) -> dict[int, T]:
    """Return a ``{index: element}`` mapping for every element that satisfies *predicate*."""
    return {i: x for i, x in enumerate(sequence) if predicate(x)}


def distinct_(sequence: list[T]) -> list[T]:
    """Return *sequence* with duplicates removed.

    Order of the result is not guaranteed.
    """
    return list(set(sequence))


def order_by_(sequence: list[T], key_selector: Callable[[T], TKey]) -> list[T]:
    """Return *sequence* sorted in ascending order by the value returned from *key_selector*."""
    return sorted(sequence, key=key_selector)


def order_by_descending_(sequence: list[T], key_selector: Callable[[T], TKey]) -> list[T]:
    """Return *sequence* sorted in descending order by the value returned from *key_selector*."""
    return sorted(sequence, key=key_selector, reverse=True)


def any_(sequence: list[T], predicate: Callable[[T], bool]) -> bool:
    """Return ``True`` if at least one element in *sequence* satisfies *predicate*."""
    return any(predicate(x) for x in sequence)


def all_(sequence: list[T], predicate: Callable[[T], bool]) -> bool:
    """Return ``True`` if every element in *sequence* satisfies *predicate*."""
    return all(predicate(x) for x in sequence)


def none_(sequence: list[T], predicate: Callable[[T], bool]) -> bool:
    """Return ``True`` if no element in *sequence* satisfies *predicate*."""
    return all(not predicate(x) for x in sequence)
