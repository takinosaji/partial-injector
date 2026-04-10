# spinq

LINQ-style collection helpers for Python. Provides familiar operations (`first`, `where`, `select`, `order_by`, etc.) as plain functions for lists and dicts, with a trailing `_` convention to avoid shadowing Python builtins.

## Requirements

Python 3.14+

## Installation

```bash
pip install spinq
```

## Lists

```python
from spinq.lists import (
    first_, first_or_none_, first_or_none_with_index_,
    last_, last_or_none_,
    single_, single_or_none_,
    filter_, where_, where_with_index_,
    except_, without_,
    select_, select_many_,
    union_, distinct_,
    order_by_, order_by_descending_,
    any_, all_, none_,
)
```

### Lookup

| Function | Description |
|----------|-------------|
| `first_(seq, predicate?)` | First matching element; raises `ValueError` if none. |
| `first_or_none_(seq, predicate?)` | First matching element or `None`. |
| `first_or_none_with_index_(seq, predicate?)` | First match as `(index, item)` or `None`. |
| `last_(seq, predicate?)` | Last matching element; raises `ValueError` if none. |
| `last_or_none_(seq, predicate?)` | Last matching element or `None`. |
| `single_(seq, predicate)` | Exactly one match; raises if zero or more than one. |
| `single_or_none_(seq, predicate)` | One match or `None`; raises if more than one. |

### Filtering

| Function | Description |
|----------|-------------|
| `filter_(seq, predicate)` | Elements that satisfy the predicate. |
| `where_(seq, predicate)` | Alias for `filter_`. |
| `where_with_index_(seq, predicate)` | Matching elements as `{index: item}` dict. |
| `except_(seq, exclusions)` | Elements not present in `exclusions`. |
| `without_(seq, predicate)` | Elements that do **not** satisfy the predicate. |
| `distinct_(seq)` | Deduplicated elements (order not guaranteed). |

### Projection

| Function | Description |
|----------|-------------|
| `select_(seq, selector)` | Map each element. |
| `select_many_(seq, selector)` | Flat-map each element (selector returns a list). |

### Set operations

| Function | Description |
|----------|-------------|
| `union_(seq1, seq2)` | Distinct union of two lists. |

### Sorting

| Function | Description |
|----------|-------------|
| `order_by_(seq, key_selector)` | Ascending sort. |
| `order_by_descending_(seq, key_selector)` | Descending sort. |

### Quantifiers

| Function | Description |
|----------|-------------|
| `any_(seq, predicate)` | `True` if any element satisfies the predicate. |
| `all_(seq, predicate)` | `True` if all elements satisfy the predicate. |
| `none_(seq, predicate)` | `True` if no element satisfies the predicate. |

### Examples

```python
from spinq.lists import where_, select_, first_, order_by_

numbers = [3, 1, 4, 1, 5, 9, 2, 6]

evens = where_(numbers, lambda x: x % 2 == 0)       # [4, 2, 6]
doubled = select_(evens, lambda x: x * 2)            # [8, 4, 12]
smallest_even = first_(numbers, lambda x: x % 2 == 0)  # 4
sorted_nums = order_by_(numbers, lambda x: x)        # [1, 1, 2, 3, 4, 5, 6, 9]
```

## Dicts

```python
from spinq.dicts import first_, first_or_none_, get_key_by_index_, get_key_value_by_index_
```

| Function | Description |
|----------|-------------|
| `first_(d, predicate?)` | First `(key, value)` tuple whose value satisfies the predicate; raises if none. |
| `first_or_none_(d, predicate?)` | Same, returns `None` if not found. |
| `get_key_by_index_(d, index)` | Key at insertion-order `index`. |
| `get_key_value_by_index_(d, index)` | `(key, value)` at insertion-order `index`. |

### Example

```python
from spinq.dicts import first_or_none_, get_key_value_by_index_

scores = {"alice": 95, "bob": 72, "carol": 88}

top = first_or_none_(scores, lambda v: v >= 90)   # ("alice", 95)
second = get_key_value_by_index_(scores, 1)        # ("bob", 72)
```

## License

MIT
