# Changelog

> The changelog **must** comply to the [keep a changelog](https://keepachangelog.com/en/1.1.0) standard.

## 1.6.0 - 2026-05-28

_*Fixed*_

- `get_key_by_index_` return type corrected from `tuple[K, V]` to `K` (the function iterates over keys, not items)
- Out-of-range index in `get_key_by_index_` and `get_key_value_by_index_` now raises `ValueError` as documented; previously `StopIteration` propagated silently to the caller
- `select_many_` reimplemented as a nested comprehension, removing an incorrect fallback that treated non-iterable selector results as scalars (the type contract requires `list[T2]`)

_*Changed*_

- `order_by_` and `order_by_descending_` key selector now typed as `Callable[[T], TKey]` instead of `Callable[[T], T]`, correctly expressing that the key and element types may differ
- Added module and function docstrings throughout

## 1.5.0 - 2026-05-19

_*Changed*_

- Lowered minimum supported Python version to 3.12

## 1.1.0 - 2025-04-29

_*Changed*_

- Project dependency and build system to poetry

## 1.0.1 - 2025-02-16

_*Fixed*_

- Missing package content

## 1.0.0 - 2025-02-16

_*Added*_

- First version of spinq
