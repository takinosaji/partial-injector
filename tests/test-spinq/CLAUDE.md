# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests in this package (from workspace root)
uv run pytest tests/test-spinq

# Run a single test file
uv run pytest tests/test-spinq/test_spinq/test_lists/test_case_lookup.py

# Run a single test by name
uv run pytest tests/test-spinq -k "test_first_returns_first_matching_element"
```

## Architecture

Tests are organised as one folder per `spinq` module, one file per functional category. Every
function under test is pure, so there are no fixtures, no mocking, and no shared state — each
test builds its own literal input (Arrange/Act/Assert pattern).

| Test file | Functions covered |
|---|---|
| `test_lists/test_case_lookup.py` | `first_`, `first_or_none_`, `first_or_none_with_index_`, `last_`, `last_or_none_`, `single_`, `single_or_none_` |
| `test_lists/test_case_filtering.py` | `filter_`, `where_`, `without_`, `except_` |
| `test_lists/test_case_projection.py` | `select_`, `select_many_`, `where_with_index_` |
| `test_lists/test_case_set_ops.py` | `union_`, `distinct_` |
| `test_lists/test_case_sorting.py` | `order_by_`, `order_by_descending_` |
| `test_lists/test_case_quantifiers.py` | `any_`, `all_`, `none_` |
| `test_dicts/test_case_lookup.py` | `first_`, `first_or_none_` |
| `test_dicts/test_case_indexing.py` | `get_key_by_index_`, `get_key_value_by_index_` |
| `test_imports.py` | Smoke test: `spinq` resolves to workspace source and exposes every documented helper |

The test package declares `spinq = { workspace = true }` so it always tests the local source, not
the published package.

Two conventions worth preserving:

- `union_` and `distinct_` are asserted order-independently (`sorted(...)` / `set(...)`) because
  both docstrings state the result order is not guaranteed.
- The negative-index tests in `test_dicts/test_case_indexing.py` assert a bare `ValueError` with
  no message match. `islice` rejects negative indices before `spinq`'s `except StopIteration`
  branch can run, so the message comes from CPython, not from `spinq`.
