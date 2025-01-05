from typing import Callable, TypeVar, Optional

T = TypeVar('T')

def first(sequence: list[T], predicate: Callable[[T], bool]) -> T:
    return next((x for x in sequence if predicate(x)), iter([]))

def first_or_none(sequence: list[T], predicate: Callable[[T], bool]) -> Optional[T]:
    return next((x for x in sequence if predicate(x)), None)

def last(sequence: list[T], predicate: Callable[[T], bool]) -> T:
    return next((x for x in reversed(sequence) if predicate(x)), iter([]))

def last_or_none(sequence: list[T], predicate: Callable[[T], bool]) -> Optional[T]:
    return next((x for x in reversed(sequence) if predicate(x)), None)

def single(sequence: list[T], predicate: Callable[[T], bool]) -> T:
    filtered = [x for x in sequence if predicate(x)]
    if len(filtered) == 1:
        return filtered[0]
    elif len(filtered) == 0:
        raise ValueError("No elements match the predicate.")
    else:
        raise ValueError("More than one element matches the predicate.")

def single_or_none(sequence: list[T], predicate: Callable[[T], bool]) -> Optional[T]:
    filtered = [x for x in sequence if predicate(x)]
    if len(filtered) == 1:
        return filtered[0]
    elif len(filtered) == 0:
        return None
    else:
        raise ValueError("More than one element matches the predicate.")

def filter_(sequence: list[T], predicate: Callable[[T], bool]) -> list[T]:
    return [x for x in sequence if predicate(x)]

def except_(sequence: list[T], exclusions: list[T]) -> list[T]:
    return [x for x in sequence if x not in exclusions]

def union(sequence1: list[T], sequence2: list[T]) -> list[T]:
    return list(set(sequence1) | set(sequence2))

def select(sequence: list[T], selector: Callable[[T], T]) -> list[T]:
    return [selector(x) for x in sequence]

def where(sequence: list[T], predicate: Callable[[T], bool]) -> list[T]:
    return [x for x in sequence if predicate(x)]

def distinct(sequence: list[T]) -> list[T]:
    return list(set(sequence))

def order_by(sequence: list[T], key_selector: Callable[[T], T]) -> list[T]:
    return sorted(sequence, key=key_selector)

def order_by_descending(sequence: list[T], key_selector: Callable[[T], T]) -> list[T]:
    return sorted(sequence, key=key_selector, reverse=True)