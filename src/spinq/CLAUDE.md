# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Lint (from workspace root)
uv run ruff check src/spinq

# Fix lint issues
uv run ruff check src/spinq --fix

# Build for publishing
cd src/spinq
uv build
uv publish
```

Tests live in `tests/test-spinq` — run them with `uv run pytest tests/test-spinq` from the workspace root.

## Architecture

`spinq` is a thin, stateless utility library — two modules, no shared state, no classes.

| Module | Contents |
|---|---|
| `lists.py` | LINQ-style helpers for Python lists: lookup (`first_`, `last_`, `single_`, `*_or_none_`), filtering (`where_`, `filter_`, `without_`, `except_`, `distinct_`), projection (`select_`, `select_many_`), set ops (`union_`), sorting (`order_by_`, `order_by_descending_`), quantifiers (`any_`, `all_`, `none_`). |
| `dicts.py` | Helpers for dicts: `first_`, `first_or_none_`, `get_key_by_index_`, `get_key_value_by_index_`. `first_*` predicates operate on **values**, not keys. |

All function names carry a trailing `_` to avoid shadowing Python builtins (`filter`, `all`, `any`, etc.).

Functions that raise on miss (`first_`, `last_`, `single_`, `get_key_by_index_`) raise `ValueError`. The `_or_none_` variants return `None` instead.
