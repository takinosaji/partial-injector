# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests in this package (from workspace root)
uv run pytest tests/test-partial-injector

# Run a single test file
uv run pytest tests/test-partial-injector/test_partial_injector/test_partial_container/test_case_singleton_resolution.py

# Run a single test by name
uv run pytest tests/test-partial-injector -k "test_transient_registration_returns_new_instance_each_time"
```

## Architecture

Tests are organised by feature under `test_partial_injector/test_partial_container/`, one file per scenario. There are no shared fixtures; each test builds its own `Container` inline (Arrange/Act/Assert pattern).

| Test file | Scenario covered |
|---|---|
| `test_case_singleton_resolution.py` | Singleton build, condition flags, `throw_if_condition_not_satisfied` |
| `test_case_transient_resolution.py` | Transient lifecycle, no captive-dependency, `FromContainer` transients |
| `test_case_singleton_factory_resolution.py` | `register_singleton_factory`, `factory_args`/`factory_kwargs` |
| `test_case_transient_factory_resolution.py` | `register_transient_factory` per-resolve semantics |
| `test_case_multiple_registrations_same_key.py` | `ListOfDependencies` grouping, `list[Key]` resolution |
| `test_from_container.py` | `FromContainer` descriptor with and without selector |
| `test_case_inject_items.py` | `inject_items=True` per-element wiring |
| `test_case_injected_async_output.py` | `inject_returns=True` with async functions |

The test package declares `partial-injector = { workspace = true }` so it always tests the local source, not the published package. `pytest-asyncio` is included for async test support.
