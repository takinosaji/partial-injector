# spinq

[![PyPI version](https://img.shields.io/pypi/v/spinq.svg)](https://pypi.org/project/spinq/)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LINQ-style collection helpers for Python lists and dicts. Functions like `first_`, `where_`, `select_`, and `order_by_` do exactly what their .NET equivalents do — plain functions, no method chaining, no new types.

Names carry a trailing `_` to avoid shadowing Python builtins (`filter`, `all`, `any`, etc.).

## Install

```bash
pip install spinq
```

## Quick start

```python
from spinq.lists import where_, select_, order_by_, first_

products = [
    {"name": "Laptop",   "price": 999, "in_stock": True},
    {"name": "Mouse",    "price": 25,  "in_stock": True},
    {"name": "Monitor",  "price": 349, "in_stock": False},
    {"name": "Keyboard", "price": 79,  "in_stock": True},
]

available  = where_(products, lambda p: p["in_stock"])
names      = select_(available, lambda p: p["name"])       # ["Laptop", "Mouse", "Keyboard"]
cheapest   = first_(available, lambda p: p["price"] < 100) # {"name": "Mouse", ...}
by_price   = order_by_(available, lambda p: p["price"])    # sorted ascending
```

---

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

| Function | Returns |
|---|---|
| `first_(seq, predicate?)` | First match; raises `ValueError` if none. |
| `first_or_none_(seq, predicate?)` | First match or `None`. |
| `first_or_none_with_index_(seq, predicate?)` | `(index, item)` tuple or `None`. |
| `last_(seq, predicate?)` | Last match; raises `ValueError` if none. |
| `last_or_none_(seq, predicate?)` | Last match or `None`. |
| `single_(seq, predicate)` | Exactly one match; raises if zero or more than one. |
| `single_or_none_(seq, predicate)` | One match or `None`; raises if more than one. |

### Filtering

| Function | Returns |
|---|---|
| `where_(seq, predicate)` | Elements that satisfy the predicate. |
| `filter_(seq, predicate)` | Alias for `where_`. |
| `where_with_index_(seq, predicate)` | `{index: item}` dict for each match. |
| `without_(seq, predicate)` | Elements that do **not** satisfy the predicate. |
| `except_(seq, exclusions)` | Elements not present in `exclusions`. |
| `distinct_(seq)` | Deduplicated elements (order not guaranteed). |

### Projection

| Function | Returns |
|---|---|
| `select_(seq, selector)` | Each element projected through `selector`. |
| `select_many_(seq, selector)` | Flat-map: `selector` returns a list, one level is flattened. |

```python
from spinq.lists import select_many_

sentences = ["hello world", "foo bar baz"]
words = select_many_(sentences, lambda s: s.split())
# ["hello", "world", "foo", "bar", "baz"]
```

### Set operations

| Function | Returns |
|---|---|
| `union_(seq1, seq2)` | Distinct union of two lists (order not guaranteed). |

### Sorting

| Function | Returns |
|---|---|
| `order_by_(seq, key_selector)` | Ascending sort by key. |
| `order_by_descending_(seq, key_selector)` | Descending sort by key. |

### Quantifiers

| Function | Returns |
|---|---|
| `any_(seq, predicate)` | `True` if at least one element satisfies the predicate. |
| `all_(seq, predicate)` | `True` if every element satisfies the predicate. |
| `none_(seq, predicate)` | `True` if no element satisfies the predicate. |

---

## Dicts

```python
from spinq.dicts import first_, first_or_none_, get_key_by_index_, get_key_value_by_index_
```

| Function | Returns |
|---|---|
| `first_(d, predicate?)` | First `(key, value)` whose value matches; raises if none. |
| `first_or_none_(d, predicate?)` | First `(key, value)` match or `None`. |
| `get_key_by_index_(d, index)` | Key at insertion-order position `index`. |
| `get_key_value_by_index_(d, index)` | `(key, value)` at insertion-order position `index`. |

```python
from spinq.dicts import first_or_none_, get_key_value_by_index_

scores = {"alice": 95, "bob": 72, "carol": 88}

winner = first_or_none_(scores, lambda v: v >= 90)  # ("alice", 95)
second = get_key_value_by_index_(scores, 1)          # ("bob", 72)
```

---

## License

MIT
