# spinq Test Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `tests/test-spinq` workspace member with ~97 tests covering all 25 helpers in `spinq.lists` and `spinq.dicts`.

**Architecture:** A new uv workspace member modeled on `tests/test-sversion`, containing one folder per source module (`test_lists/`, `test_dicts/`) and one file per functional category inside each. Tests are plain functions over literal data — no fixtures, no mocking, no shared state, because every function under test is pure.

**Tech Stack:** Python 3.14 dev env, uv workspace, hatchling, pytest, ruff, bandit.

## Global Constraints

- **This is characterization testing of existing, working code — there is no red phase.** New tests are expected to PASS the first time they run. If a new test fails, either the test is wrong or a real bug was found: stop, report it, and do not modify `src/spinq/spinq/*.py` to make a test pass.
- **No source changes.** `src/spinq/spinq/lists.py` and `dicts.py` are read-only for this plan. No `spinq` version bump, no `src/spinq/CHANGELOG.md` entry.
- Run every command from the workspace root `C:\github\opensource\partial-injector`.
- Shell is PowerShell. Chain with `;` or `&&`. Use forward slashes in paths passed to `uv`/`pytest`.
- Line length 88. Ruff rules `E,W,F,I,N,UP,B,SIM`, ignoring `E501,UP042`.
- Import order in every test file: stdlib, blank line, `pytest`, blank line, `spinq.*`.
- Every test uses explicit `# Arrange` / `# Act` / `# Assert` comment blocks, or `# Arrange` / `# Act / Assert` where `pytest.raises` collapses the last two.
- Assert exact exception messages with `pytest.raises(ValueError, match=re.escape("..."))` **only** where the message originates in `spinq`. Where CPython raises, assert the bare type.
- Set-based helpers (`distinct_`, `union_`) are asserted order-independently via `sorted(...)` or `set(...)`.
- A `.claude/hooks` PostToolUse hook runs ruff + bandit on every `.py` file written. Fix what it reports before moving on.
- Work happens on branch `feature/spinq-tests`, which already exists and already holds the design spec commit.

---

### Task 1: Scaffold the test-spinq workspace member

**Files:**
- Create: `tests/test-spinq/pyproject.toml`
- Create: `tests/test-spinq/test_spinq/__init__.py`
- Create: `tests/test-spinq/test_spinq/test_lists/__init__.py`
- Create: `tests/test-spinq/test_spinq/test_dicts/__init__.py`
- Create: `tests/test-spinq/test_spinq/test_imports.py`
- Modify: `pyproject.toml` (root) — `[tool.uv.workspace] members` and `[tool.ruff.lint.isort] known-first-party`

**Interfaces:**
- Consumes: nothing.
- Produces: an importable `test_spinq` package resolving `spinq` from local workspace source, so all later tasks can `from spinq.lists import ...`.

- [ ] **Step 1: Create the member pyproject**

Create `tests/test-spinq/pyproject.toml`:

```toml
[project]
name = "spinq-tests"
version = "0.0.0"
description = "spinq unit tests"
license = { text = "MIT" }
authors = [{ name = "Kostiantyn Chomakov", email = "kostiantyn.chomakov@gmail.com" }]
requires-python = ">=3.14,<3.15"
dependencies = [
  "pytest>=8.3.5",
  "spinq",
]

[tool.uv.sources]
spinq = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["test_spinq"]

[tool.ruff]
line-length = 88
target-version = "py314"
extend-exclude = [".venv", "dist", "build", ".mypy_cache", ".pytest_cache", ".ruff_cache"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "SIM"]
ignore = ["E501", "UP042"]

[tool.ruff.lint.per-file-ignores]
"**/__init__.py" = ["F401"]

[tool.ruff.lint.isort]
known-first-party = ["spinq", "test_spinq"]

[tool.pytest.ini_options]
addopts = "--import-mode=importlib"
testpaths = ["test_spinq"]
```

Note: unlike `test-sversion`, there is no `asyncio_default_fixture_loop_scope` and no
`pytest-asyncio` / `faker` dependency — nothing in `spinq` is async and the tests use literal data.

- [ ] **Step 2: Create the three empty package markers**

Create these three files, each with **empty** content:
- `tests/test-spinq/test_spinq/__init__.py`
- `tests/test-spinq/test_spinq/test_lists/__init__.py`
- `tests/test-spinq/test_spinq/test_dicts/__init__.py`

- [ ] **Step 3: Register the member in the root pyproject**

In `pyproject.toml` at the repo root, change:

```toml
[tool.uv.workspace]
members = [
  "src/partial-injector",
  "src/spinq",
  "src/sversion",
  "tests/test-partial-injector",
  "tests/test-sversion",
]
```

to:

```toml
[tool.uv.workspace]
members = [
  "src/partial-injector",
  "src/spinq",
  "src/sversion",
  "tests/test-partial-injector",
  "tests/test-spinq",
  "tests/test-sversion",
]
```

And change:

```toml
known-first-party = ["partial_injector", "spinq", "sversion", "test_partial_injector", "test_sversion"]
```

to:

```toml
known-first-party = ["partial_injector", "spinq", "sversion", "test_partial_injector", "test_spinq", "test_sversion"]
```

- [ ] **Step 4: Write the smoke test**

Create `tests/test-spinq/test_spinq/test_imports.py`:

```python
import spinq.dicts
import spinq.lists


def test_spinq_resolves_to_local_workspace_source():
    # Arrange
    module_path = spinq.lists.__file__

    # Act
    is_local_source = "site-packages" not in module_path.replace("\\", "/")

    # Assert
    assert is_local_source, f"spinq resolved to {module_path}, not workspace source"


def test_lists_module_exposes_every_documented_helper():
    # Arrange
    expected = {
        "first_",
        "first_or_none_",
        "first_or_none_with_index_",
        "last_",
        "last_or_none_",
        "single_",
        "single_or_none_",
        "filter_",
        "except_",
        "without_",
        "union_",
        "select_",
        "select_many_",
        "where_",
        "where_with_index_",
        "distinct_",
        "order_by_",
        "order_by_descending_",
        "any_",
        "all_",
        "none_",
    }

    # Act
    actual = {name for name in vars(spinq.lists) if name.endswith("_")}

    # Assert
    assert expected <= actual


def test_dicts_module_exposes_every_documented_helper():
    # Arrange
    expected = {
        "first_",
        "first_or_none_",
        "get_key_by_index_",
        "get_key_value_by_index_",
    }

    # Act
    actual = {name for name in vars(spinq.dicts) if name.endswith("_")}

    # Assert
    assert expected <= actual
```

- [ ] **Step 5: Sync the workspace**

Run: `uv sync --all-groups`
Expected: succeeds, `uv.lock` updated, output mentions `spinq-tests`.

- [ ] **Step 6: Run the smoke test**

Run: `uv run pytest tests/test-spinq -v`
Expected: 3 passed.

If `spinq` cannot be imported, the member was not picked up — re-check Step 3 and re-run Step 5.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock tests/test-spinq
git commit -m "test: scaffold test-spinq workspace member"
```

---

### Task 2: List lookup helpers

**Files:**
- Create: `tests/test-spinq/test_spinq/test_lists/test_case_lookup.py`

**Interfaces:**
- Consumes: the `test_spinq.test_lists` package from Task 1.
- Produces: module-level constants `NO_MATCH_MESSAGE` and `MULTIPLE_MATCH_MESSAGE` and the predicate `is_even(value: int) -> bool`. Later task files declare their own copies rather than importing these — each test file stands alone.

- [ ] **Step 1: Write the tests**

Create `tests/test-spinq/test_spinq/test_lists/test_case_lookup.py`:

```python
import re

import pytest

from spinq.lists import (
    first_,
    first_or_none_,
    first_or_none_with_index_,
    last_,
    last_or_none_,
    single_,
    single_or_none_,
)

NO_MATCH_MESSAGE = "No elements match the predicate."
MULTIPLE_MATCH_MESSAGE = "More than one element matches the predicate."


def is_even(value: int) -> bool:
    return value % 2 == 0


def test_first_returns_first_matching_element():
    # Arrange
    sequence = [1, 2, 3, 4]

    # Act
    result = first_(sequence, is_even)

    # Assert
    assert result == 2


def test_first_without_predicate_returns_head():
    # Arrange
    sequence = [7, 8, 9]

    # Act
    result = first_(sequence)

    # Assert
    assert result == 7


def test_first_with_no_match_raises():
    # Arrange
    sequence = [1, 3, 5]

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        first_(sequence, is_even)


def test_first_on_empty_list_raises():
    # Arrange
    sequence: list[int] = []

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        first_(sequence)


def test_first_or_none_returns_first_matching_element():
    # Arrange
    sequence = [1, 2, 3, 4]

    # Act
    result = first_or_none_(sequence, is_even)

    # Assert
    assert result == 2


def test_first_or_none_without_predicate_returns_head():
    # Arrange
    sequence = [7, 8, 9]

    # Act
    result = first_or_none_(sequence)

    # Assert
    assert result == 7


def test_first_or_none_with_no_match_returns_none():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = first_or_none_(sequence, is_even)

    # Assert
    assert result is None


def test_first_or_none_on_empty_list_returns_none():
    # Arrange
    sequence: list[int] = []

    # Act
    result = first_or_none_(sequence)

    # Assert
    assert result is None


def test_first_or_none_with_index_returns_position_in_original_list():
    # Arrange
    sequence = [1, 3, 4, 6]

    # Act
    result = first_or_none_with_index_(sequence, is_even)

    # Assert
    assert result == (2, 4)


def test_first_or_none_with_index_without_predicate_returns_head_at_zero():
    # Arrange
    sequence = [7, 8]

    # Act
    result = first_or_none_with_index_(sequence)

    # Assert
    assert result == (0, 7)


def test_first_or_none_with_index_with_no_match_returns_none():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = first_or_none_with_index_(sequence, is_even)

    # Assert
    assert result is None


def test_first_or_none_with_index_on_empty_list_returns_none():
    # Arrange
    sequence: list[int] = []

    # Act
    result = first_or_none_with_index_(sequence)

    # Assert
    assert result is None


def test_last_returns_last_matching_element():
    # Arrange
    sequence = [1, 2, 3, 4]

    # Act
    result = last_(sequence, is_even)

    # Assert
    assert result == 4


def test_last_without_predicate_returns_tail():
    # Arrange
    sequence = [7, 8, 9]

    # Act
    result = last_(sequence)

    # Assert
    assert result == 9


def test_last_with_no_match_raises():
    # Arrange
    sequence = [1, 3, 5]

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        last_(sequence, is_even)


def test_last_on_empty_list_raises():
    # Arrange
    sequence: list[int] = []

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        last_(sequence)


def test_last_or_none_returns_last_matching_element():
    # Arrange
    sequence = [1, 2, 3, 4]

    # Act
    result = last_or_none_(sequence, is_even)

    # Assert
    assert result == 4


def test_last_or_none_without_predicate_returns_tail():
    # Arrange
    sequence = [7, 8, 9]

    # Act
    result = last_or_none_(sequence)

    # Assert
    assert result == 9


def test_last_or_none_with_no_match_returns_none():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = last_or_none_(sequence, is_even)

    # Assert
    assert result is None


def test_last_or_none_on_empty_list_returns_none():
    # Arrange
    sequence: list[int] = []

    # Act
    result = last_or_none_(sequence)

    # Assert
    assert result is None


def test_single_returns_sole_matching_element():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = single_(sequence, is_even)

    # Assert
    assert result == 2


def test_single_with_no_match_raises():
    # Arrange
    sequence = [1, 3, 5]

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        single_(sequence, is_even)


def test_single_on_empty_list_raises():
    # Arrange
    sequence: list[int] = []

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        single_(sequence, is_even)


def test_single_with_multiple_matches_raises():
    # Arrange
    sequence = [2, 3, 4]

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(MULTIPLE_MATCH_MESSAGE)):
        single_(sequence, is_even)


def test_single_or_none_returns_sole_matching_element():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = single_or_none_(sequence, is_even)

    # Assert
    assert result == 2


def test_single_or_none_with_no_match_returns_none():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = single_or_none_(sequence, is_even)

    # Assert
    assert result is None


def test_single_or_none_on_empty_list_returns_none():
    # Arrange
    sequence: list[int] = []

    # Act
    result = single_or_none_(sequence, is_even)

    # Assert
    assert result is None


def test_single_or_none_with_multiple_matches_raises():
    # Arrange
    sequence = [2, 3, 4]

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(MULTIPLE_MATCH_MESSAGE)):
        single_or_none_(sequence, is_even)
```

- [ ] **Step 2: Run the tests**

Run: `uv run pytest tests/test-spinq/test_spinq/test_lists/test_case_lookup.py -v`
Expected: 28 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test-spinq/test_spinq/test_lists/test_case_lookup.py
git commit -m "test: cover spinq.lists lookup helpers"
```

---

### Task 3: List filtering helpers

**Files:**
- Create: `tests/test-spinq/test_spinq/test_lists/test_case_filtering.py`

**Interfaces:**
- Consumes: the `test_spinq.test_lists` package from Task 1.
- Produces: nothing consumed elsewhere.

- [ ] **Step 1: Write the tests**

Create `tests/test-spinq/test_spinq/test_lists/test_case_filtering.py`:

```python
from spinq.lists import except_, filter_, where_, without_


def is_even(value: int) -> bool:
    return value % 2 == 0


def test_filter_keeps_matching_elements_in_original_order():
    # Arrange
    sequence = [4, 1, 2, 3, 6]

    # Act
    result = filter_(sequence, is_even)

    # Assert
    assert result == [4, 2, 6]


def test_filter_with_no_match_returns_empty_list():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = filter_(sequence, is_even)

    # Assert
    assert result == []


def test_filter_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[int] = []

    # Act
    result = filter_(sequence, is_even)

    # Assert
    assert result == []


def test_where_keeps_matching_elements_in_original_order():
    # Arrange
    sequence = [4, 1, 2, 3, 6]

    # Act
    result = where_(sequence, is_even)

    # Assert
    assert result == [4, 2, 6]


def test_where_returns_same_result_as_filter():
    # Arrange
    sequence = [4, 1, 2, 3, 6]

    # Act
    where_result = where_(sequence, is_even)
    filter_result = filter_(sequence, is_even)

    # Assert
    assert where_result == filter_result


def test_without_removes_matching_elements():
    # Arrange
    sequence = [4, 1, 2, 3, 6]

    # Act
    result = without_(sequence, is_even)

    # Assert
    assert result == [1, 3]


def test_without_is_complement_of_filter():
    # Arrange
    sequence = [4, 1, 2, 3, 6]

    # Act
    kept = filter_(sequence, is_even)
    removed = without_(sequence, is_even)

    # Assert
    assert sorted(kept + removed) == sorted(sequence)


def test_without_with_no_match_returns_all_elements():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = without_(sequence, is_even)

    # Assert
    assert result == [1, 3, 5]


def test_without_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[int] = []

    # Act
    result = without_(sequence, is_even)

    # Assert
    assert result == []


def test_except_removes_excluded_values():
    # Arrange
    sequence = [1, 2, 3, 4]

    # Act
    result = except_(sequence, [2, 4])

    # Assert
    assert result == [1, 3]


def test_except_removes_every_duplicate_occurrence():
    # Arrange
    sequence = [1, 2, 2, 3, 2]

    # Act
    result = except_(sequence, [2])

    # Assert
    assert result == [1, 3]


def test_except_preserves_order_of_remaining_elements():
    # Arrange
    sequence = [5, 1, 4, 2]

    # Act
    result = except_(sequence, [4])

    # Assert
    assert result == [5, 1, 2]


def test_except_with_empty_exclusions_returns_equal_list():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = except_(sequence, [])

    # Assert
    assert result == [1, 2, 3]


def test_except_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[int] = []

    # Act
    result = except_(sequence, [1, 2])

    # Assert
    assert result == []
```

- [ ] **Step 2: Run the tests**

Run: `uv run pytest tests/test-spinq/test_spinq/test_lists/test_case_filtering.py -v`
Expected: 14 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test-spinq/test_spinq/test_lists/test_case_filtering.py
git commit -m "test: cover spinq.lists filtering helpers"
```

---

### Task 4: List projection helpers

**Files:**
- Create: `tests/test-spinq/test_spinq/test_lists/test_case_projection.py`

**Interfaces:**
- Consumes: the `test_spinq.test_lists` package from Task 1.
- Produces: nothing consumed elsewhere.

- [ ] **Step 1: Write the tests**

Create `tests/test-spinq/test_spinq/test_lists/test_case_projection.py`:

```python
from spinq.lists import select_, select_many_, where_with_index_


def is_even(value: int) -> bool:
    return value % 2 == 0


def double(value: int) -> int:
    return value * 2


def test_select_applies_selector_to_every_element():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = select_(sequence, double)

    # Assert
    assert result == [2, 4, 6]


def test_select_preserves_order_and_length():
    # Arrange
    sequence = [3, 1, 2]

    # Act
    result = select_(sequence, str)

    # Assert
    assert result == ["3", "1", "2"]


def test_select_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[int] = []

    # Act
    result = select_(sequence, double)

    # Assert
    assert result == []


def test_select_many_flattens_projected_lists():
    # Arrange
    sequence = [1, 2]

    # Act
    result = select_many_(sequence, lambda x: [x, x * 10])

    # Assert
    assert result == [1, 10, 2, 20]


def test_select_many_flattens_only_one_level():
    # Arrange
    sequence = [1, 2]

    # Act
    result = select_many_(sequence, lambda x: [[x]])

    # Assert
    assert result == [[1], [2]]


def test_select_many_skips_empty_inner_lists():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = select_many_(sequence, lambda x: [x] if is_even(x) else [])

    # Assert
    assert result == [2]


def test_select_many_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[int] = []

    # Act
    result = select_many_(sequence, lambda x: [x])

    # Assert
    assert result == []


def test_where_with_index_returns_positions_in_original_list():
    # Arrange
    sequence = [1, 4, 3, 6]

    # Act
    result = where_with_index_(sequence, is_even)

    # Assert
    assert result == {1: 4, 3: 6}


def test_where_with_index_with_no_match_returns_empty_dict():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = where_with_index_(sequence, is_even)

    # Assert
    assert result == {}


def test_where_with_index_on_empty_list_returns_empty_dict():
    # Arrange
    sequence: list[int] = []

    # Act
    result = where_with_index_(sequence, is_even)

    # Assert
    assert result == {}
```

- [ ] **Step 2: Run the tests**

Run: `uv run pytest tests/test-spinq/test_spinq/test_lists/test_case_projection.py -v`
Expected: 10 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test-spinq/test_spinq/test_lists/test_case_projection.py
git commit -m "test: cover spinq.lists projection helpers"
```

---

### Task 5: List set operations

**Files:**
- Create: `tests/test-spinq/test_spinq/test_lists/test_case_set_ops.py`

**Interfaces:**
- Consumes: the `test_spinq.test_lists` package from Task 1.
- Produces: nothing consumed elsewhere.

- [ ] **Step 1: Write the tests**

Create `tests/test-spinq/test_spinq/test_lists/test_case_set_ops.py`:

```python
import pytest

from spinq.lists import distinct_, union_


def test_distinct_removes_duplicates():
    # Arrange
    sequence = [3, 1, 3, 2, 1]

    # Act
    result = distinct_(sequence)

    # Assert
    assert sorted(result) == [1, 2, 3]


def test_distinct_on_already_distinct_list_returns_same_members():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = distinct_(sequence)

    # Assert
    assert sorted(result) == [1, 2, 3]


def test_distinct_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[int] = []

    # Act
    result = distinct_(sequence)

    # Assert
    assert result == []


def test_distinct_with_unhashable_elements_raises_type_error():
    # Arrange
    sequence = [[1], [2]]

    # Act / Assert
    # Message comes from CPython's set(), not from spinq, so only the type is asserted.
    with pytest.raises(TypeError):
        distinct_(sequence)


def test_union_returns_distinct_union_of_overlapping_lists():
    # Arrange
    sequence1 = [1, 2, 3]
    sequence2 = [3, 4]

    # Act
    result = union_(sequence1, sequence2)

    # Assert
    assert set(result) == {1, 2, 3, 4}
    assert len(result) == 4


def test_union_of_disjoint_lists_contains_all_members():
    # Arrange
    sequence1 = [1, 2]
    sequence2 = [3, 4]

    # Act
    result = union_(sequence1, sequence2)

    # Assert
    assert set(result) == {1, 2, 3, 4}


def test_union_deduplicates_within_a_single_operand():
    # Arrange
    sequence1 = [1, 1, 2]
    sequence2: list[int] = []

    # Act
    result = union_(sequence1, sequence2)

    # Assert
    assert set(result) == {1, 2}
    assert len(result) == 2


def test_union_with_empty_operand_returns_members_of_other():
    # Arrange
    sequence1: list[int] = []
    sequence2 = [5, 6]

    # Act
    result = union_(sequence1, sequence2)

    # Assert
    assert set(result) == {5, 6}


def test_union_of_two_empty_lists_returns_empty_list():
    # Arrange
    sequence1: list[int] = []
    sequence2: list[int] = []

    # Act
    result = union_(sequence1, sequence2)

    # Assert
    assert result == []


def test_union_with_unhashable_elements_raises_type_error():
    # Arrange
    sequence1 = [[1]]
    sequence2 = [[2]]

    # Act / Assert
    # Message comes from CPython's set(), not from spinq, so only the type is asserted.
    with pytest.raises(TypeError):
        union_(sequence1, sequence2)
```

- [ ] **Step 2: Run the tests**

Run: `uv run pytest tests/test-spinq/test_spinq/test_lists/test_case_set_ops.py -v`
Expected: 10 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test-spinq/test_spinq/test_lists/test_case_set_ops.py
git commit -m "test: cover spinq.lists set operations"
```

---

### Task 6: List sorting helpers

**Files:**
- Create: `tests/test-spinq/test_spinq/test_lists/test_case_sorting.py`

**Interfaces:**
- Consumes: the `test_spinq.test_lists` package from Task 1.
- Produces: nothing consumed elsewhere.

The data is a list of `(label, rank)` tuples whose natural tuple ordering differs from the
ordering by `rank`, so a test would fail if the implementation ignored the key selector.

- [ ] **Step 1: Write the tests**

Create `tests/test-spinq/test_spinq/test_lists/test_case_sorting.py`:

```python
from spinq.lists import order_by_, order_by_descending_


def by_rank(pair: tuple[str, int]) -> int:
    return pair[1]


def test_order_by_sorts_by_key_selector_not_by_element():
    # Arrange
    sequence = [("b", 3), ("a", 1), ("c", 2)]

    # Act
    result = order_by_(sequence, by_rank)

    # Assert
    assert result == [("a", 1), ("c", 2), ("b", 3)]


def test_order_by_descending_sorts_by_key_selector_not_by_element():
    # Arrange
    sequence = [("b", 3), ("a", 1), ("c", 2)]

    # Act
    result = order_by_descending_(sequence, by_rank)

    # Assert
    assert result == [("b", 3), ("c", 2), ("a", 1)]


def test_order_by_descending_is_reverse_of_order_by():
    # Arrange
    sequence = [("b", 3), ("a", 1), ("c", 2)]

    # Act
    ascending = order_by_(sequence, by_rank)
    descending = order_by_descending_(sequence, by_rank)

    # Assert
    assert descending == list(reversed(ascending))


def test_order_by_does_not_mutate_input():
    # Arrange
    sequence = [("b", 3), ("a", 1), ("c", 2)]

    # Act
    order_by_(sequence, by_rank)

    # Assert
    assert sequence == [("b", 3), ("a", 1), ("c", 2)]


def test_order_by_descending_does_not_mutate_input():
    # Arrange
    sequence = [("b", 3), ("a", 1), ("c", 2)]

    # Act
    order_by_descending_(sequence, by_rank)

    # Assert
    assert sequence == [("b", 3), ("a", 1), ("c", 2)]


def test_order_by_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[tuple[str, int]] = []

    # Act
    result = order_by_(sequence, by_rank)

    # Assert
    assert result == []


def test_order_by_descending_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[tuple[str, int]] = []

    # Act
    result = order_by_descending_(sequence, by_rank)

    # Assert
    assert result == []
```

- [ ] **Step 2: Run the tests**

Run: `uv run pytest tests/test-spinq/test_spinq/test_lists/test_case_sorting.py -v`
Expected: 7 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test-spinq/test_spinq/test_lists/test_case_sorting.py
git commit -m "test: cover spinq.lists sorting helpers"
```

---

### Task 7: List quantifiers

**Files:**
- Create: `tests/test-spinq/test_spinq/test_lists/test_case_quantifiers.py`

**Interfaces:**
- Consumes: the `test_spinq.test_lists` package from Task 1.
- Produces: nothing consumed elsewhere.

- [ ] **Step 1: Write the tests**

Create `tests/test-spinq/test_spinq/test_lists/test_case_quantifiers.py`:

```python
from spinq.lists import all_, any_, none_


def is_even(value: int) -> bool:
    return value % 2 == 0


def test_any_returns_true_when_one_element_matches():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = any_(sequence, is_even)

    # Assert
    assert result is True


def test_any_returns_false_when_no_element_matches():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = any_(sequence, is_even)

    # Assert
    assert result is False


def test_any_on_empty_list_returns_false():
    # Arrange
    sequence: list[int] = []

    # Act
    result = any_(sequence, is_even)

    # Assert
    assert result is False


def test_all_returns_true_when_every_element_matches():
    # Arrange
    sequence = [2, 4, 6]

    # Act
    result = all_(sequence, is_even)

    # Assert
    assert result is True


def test_all_returns_false_when_one_element_does_not_match():
    # Arrange
    sequence = [2, 3, 6]

    # Act
    result = all_(sequence, is_even)

    # Assert
    assert result is False


def test_all_on_empty_list_returns_true():
    # Arrange
    sequence: list[int] = []

    # Act
    result = all_(sequence, is_even)

    # Assert
    assert result is True


def test_none_returns_true_when_no_element_matches():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = none_(sequence, is_even)

    # Assert
    assert result is True


def test_none_returns_false_when_one_element_matches():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = none_(sequence, is_even)

    # Assert
    assert result is False


def test_none_on_empty_list_returns_true():
    # Arrange
    sequence: list[int] = []

    # Act
    result = none_(sequence, is_even)

    # Assert
    assert result is True
```

- [ ] **Step 2: Run the tests**

Run: `uv run pytest tests/test-spinq/test_spinq/test_lists/test_case_quantifiers.py -v`
Expected: 9 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test-spinq/test_spinq/test_lists/test_case_quantifiers.py
git commit -m "test: cover spinq.lists quantifiers"
```

---

### Task 8: Dict lookup helpers

**Files:**
- Create: `tests/test-spinq/test_spinq/test_dicts/test_case_lookup.py`

**Interfaces:**
- Consumes: the `test_spinq.test_dicts` package from Task 1.
- Produces: nothing consumed elsewhere.

The keys-vs-values tests use `{2: 3, 3: 4}`: applying `is_even` to values selects `(3, 4)`,
while applying it to keys would select `(2, 3)`. The assertion therefore fails if the predicate
is ever applied to keys.

- [ ] **Step 1: Write the tests**

Create `tests/test-spinq/test_spinq/test_dicts/test_case_lookup.py`:

```python
import re

import pytest

from spinq.dicts import first_, first_or_none_

NO_MATCH_MESSAGE = "No elements match the predicate."


def is_even(value: int) -> bool:
    return value % 2 == 0


def test_first_applies_predicate_to_values_not_keys():
    # Arrange
    dictionary = {2: 3, 3: 4}

    # Act
    result = first_(dictionary, is_even)

    # Assert
    assert result == (3, 4)


def test_first_returns_key_value_tuple():
    # Arrange
    dictionary = {"a": 1, "b": 2}

    # Act
    result = first_(dictionary, is_even)

    # Assert
    assert result == ("b", 2)


def test_first_without_predicate_returns_first_inserted_pair():
    # Arrange
    dictionary = {"b": 1, "a": 2}

    # Act
    result = first_(dictionary)

    # Assert
    assert result == ("b", 1)


def test_first_with_no_match_raises():
    # Arrange
    dictionary = {"a": 1, "b": 3}

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        first_(dictionary, is_even)


def test_first_on_empty_dict_raises():
    # Arrange
    dictionary: dict[str, int] = {}

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        first_(dictionary)


def test_first_or_none_applies_predicate_to_values_not_keys():
    # Arrange
    dictionary = {2: 3, 3: 4}

    # Act
    result = first_or_none_(dictionary, is_even)

    # Assert
    assert result == (3, 4)


def test_first_or_none_without_predicate_returns_first_inserted_pair():
    # Arrange
    dictionary = {"b": 1, "a": 2}

    # Act
    result = first_or_none_(dictionary)

    # Assert
    assert result == ("b", 1)


def test_first_or_none_with_no_match_returns_none():
    # Arrange
    dictionary = {"a": 1, "b": 3}

    # Act
    result = first_or_none_(dictionary, is_even)

    # Assert
    assert result is None


def test_first_or_none_on_empty_dict_returns_none():
    # Arrange
    dictionary: dict[str, int] = {}

    # Act
    result = first_or_none_(dictionary)

    # Assert
    assert result is None
```

- [ ] **Step 2: Run the tests**

Run: `uv run pytest tests/test-spinq/test_spinq/test_dicts/test_case_lookup.py -v`
Expected: 9 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test-spinq/test_spinq/test_dicts/test_case_lookup.py
git commit -m "test: cover spinq.dicts lookup helpers"
```

---

### Task 9: Dict indexing helpers

**Files:**
- Create: `tests/test-spinq/test_spinq/test_dicts/test_case_indexing.py`

**Interfaces:**
- Consumes: the `test_spinq.test_dicts` package from Task 1.
- Produces: nothing consumed elsewhere.

The dict literal `{"b": 1, "a": 2, "c": 3}` is deliberately not in key order, so index `0`
returning `"b"` proves insertion order rather than sorted order.

- [ ] **Step 1: Write the tests**

Create `tests/test-spinq/test_spinq/test_dicts/test_case_indexing.py`:

```python
import re

import pytest

from spinq.dicts import get_key_by_index_, get_key_value_by_index_

OUT_OF_RANGE_MESSAGE = "Index out of range."


def test_get_key_by_index_returns_key_at_insertion_position():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act
    result = get_key_by_index_(dictionary, 0)

    # Assert
    assert result == "b"


def test_get_key_by_index_returns_middle_key():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act
    result = get_key_by_index_(dictionary, 1)

    # Assert
    assert result == "a"


def test_get_key_by_index_past_end_raises():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(OUT_OF_RANGE_MESSAGE)):
        get_key_by_index_(dictionary, 5)


def test_get_key_by_index_on_empty_dict_raises():
    # Arrange
    dictionary: dict[str, int] = {}

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(OUT_OF_RANGE_MESSAGE)):
        get_key_by_index_(dictionary, 0)


def test_get_key_by_index_negative_raises():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act / Assert
    # islice rejects negative indices itself, so the except StopIteration branch never runs
    # and the message comes from CPython rather than from spinq. Only the type is asserted.
    with pytest.raises(ValueError):
        get_key_by_index_(dictionary, -1)


def test_get_key_value_by_index_returns_pair_at_insertion_position():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act
    result = get_key_value_by_index_(dictionary, 0)

    # Assert
    assert result == ("b", 1)


def test_get_key_value_by_index_returns_middle_pair():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act
    result = get_key_value_by_index_(dictionary, 1)

    # Assert
    assert result == ("a", 2)


def test_get_key_value_by_index_past_end_raises():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(OUT_OF_RANGE_MESSAGE)):
        get_key_value_by_index_(dictionary, 5)


def test_get_key_value_by_index_on_empty_dict_raises():
    # Arrange
    dictionary: dict[str, int] = {}

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(OUT_OF_RANGE_MESSAGE)):
        get_key_value_by_index_(dictionary, 0)


def test_get_key_value_by_index_negative_raises():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act / Assert
    # islice rejects negative indices itself, so the except StopIteration branch never runs
    # and the message comes from CPython rather than from spinq. Only the type is asserted.
    with pytest.raises(ValueError):
        get_key_value_by_index_(dictionary, -1)
```

- [ ] **Step 2: Run the tests**

Run: `uv run pytest tests/test-spinq/test_spinq/test_dicts/test_case_indexing.py -v`
Expected: 10 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test-spinq/test_spinq/test_dicts/test_case_indexing.py
git commit -m "test: cover spinq.dicts indexing helpers"
```

---

### Task 10: Documentation and full verification

**Files:**
- Create: `tests/test-spinq/CLAUDE.md`
- Modify: `src/spinq/CLAUDE.md` — replace the "There is no dedicated test package for spinq." line
- Modify: `.serena/memories/core.md` — the spinq row in the source-map table
- Modify: `.serena/memories/suggested_commands.md` — the "No tests exist for `spinq`." line

- [ ] **Step 1: Write the test package CLAUDE.md**

Create `tests/test-spinq/CLAUDE.md`:

```markdown
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
```

- [ ] **Step 2: Update the spinq package CLAUDE.md**

In `src/spinq/CLAUDE.md`, replace this line:

```
There is no dedicated test package for spinq.
```

with:

```
Tests live in `tests/test-spinq` — run them with `uv run pytest tests/test-spinq` from the workspace root.
```

- [ ] **Step 3: Update the Serena core memory**

In `.serena/memories/core.md`, in the source-map table, replace:

```
| `src/spinq/spinq/` | `spinq` | LINQ-style list/dict helpers. **No test package exists.** |
```

with:

```
| `src/spinq/spinq/` | `spinq` | LINQ-style list/dict helpers. |
```

and add this row directly after the `tests/test-partial-injector` row:

```
| `tests/test-spinq/test_spinq/` | `spinq-tests` (unpublished, v0.0.0) | Folder per source module, file per category. |
```

- [ ] **Step 4: Update the Serena suggested_commands memory**

In `.serena/memories/suggested_commands.md`, make two edits.

First, replace this command block:

```
uv run pytest                                   # both test packages (testpaths = ["tests"])
uv run pytest tests/test-partial-injector
uv run pytest tests/test-sversion
uv run pytest tests/test-partial-injector -k "<test_name>"
```

with:

```
uv run pytest                                   # all three test packages (testpaths = ["tests"])
uv run pytest tests/test-partial-injector
uv run pytest tests/test-spinq
uv run pytest tests/test-sversion
uv run pytest tests/test-partial-injector -k "<test_name>"
```

Second, delete the sentence that immediately follows that block:

```
No tests exist for `spinq`.
```

- [ ] **Step 5: Format and lint the whole workspace**

Run: `uv run ruff format . ; uv run ruff check . --fix`
Expected: files reformatted if needed, `All checks passed!`.

- [ ] **Step 6: Run bandit**

Run: `uv run bandit -r -c .bandit src tests sdlc`
Expected: `No issues identified.`

- [ ] **Step 7: Run the full suite**

Run: `uv run pytest`
Expected: all tests pass. The `test-spinq` contribution is 100 tests (3 smoke + 28 + 14 + 10 + 10 + 7 + 9 + 9 + 10), and the pre-existing `test-partial-injector` and `test-sversion` tests must all still pass.

- [ ] **Step 8: Verify the new package is collected under the root config**

Run: `uv run pytest tests/test-spinq --collect-only -q`
Expected: the final line reports 100 tests collected.

- [ ] **Step 9: Commit**

```bash
git add tests/test-spinq/CLAUDE.md src/spinq/CLAUDE.md .serena/memories/core.md .serena/memories/suggested_commands.md
git commit -m "docs: document the test-spinq package"
```

---

## Self-Review

**Spec coverage:** Every section of `docs/superpowers/specs/2026-08-14-spinq-tests-design.md` maps to a task — scaffolding and repo touchpoints to Task 1, the eight coverage sections to Tasks 2-9 in order, the conventions section to the Global Constraints, and the verification plus follow-up sections to Task 10. All 25 functions appear in exactly one test file.

**Placeholder scan:** No TBD/TODO markers; every code step contains complete, runnable content; no task refers to another task's code by reference.

**Type consistency:** Function names and signatures used in the tests match `src/spinq/spinq/lists.py` and `dicts.py` exactly — checked against the module symbol lists. `is_even` is redefined independently in each file that needs it rather than imported across test modules, so no cross-file symbol contract exists to drift.
