# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run tests for this package (from workspace root)
uv run pytest tests/test-partial-injector

# Run a single test file
uv run pytest tests/test-partial-injector/test_partial_injector/test_partial_container/test_case_singleton_resolution.py

# Lint
uv run ruff check src/partial-injector

# Fix lint issues
uv run ruff check src/partial-injector --fix

# Build for publishing
cd src/partial-injector
uv build
uv publish
```

## Architecture

This is the `partial_injector` package — a `functools.partial`-based DI container for plain Python functions. No decorators, no metaclasses.

### Module responsibilities

| Module | Role |
|---|---|
| `partial_container.py` | Public API: `Container` and `FromContainer`. All registration, build, and resolve logic lives here. |
| `_models.py` | Shared data types: `Registration`, `FromContainer`, `ContainerKey`, `RegistrationType`. Kept separate to avoid circular imports. |
| `_entries.py` | Sealed `BuiltEntry` hierarchy: `SingletonBuilt`, `TransientBuilt`, `GroupBuilt`, and `TransientContainer`. These represent the built state of a registration. |
| `_algorithms.py` | Pure stateless functions: `_topological_sort` (Kahn's), `_find_cycle` (DFS), `_find_param_key`, `_copy_object`, `_is_dynamic_entry`, `_registration_category`. |
| `_dependency_analyser.py` | Builds the `{key: frozenset_of_deps}` graph consumed by `_topological_sort`. |
| `_function_wirer.py` | Produces wired callables: singleton deps via `functools.partial`, transient deps via a closure wrapper that re-resolves on every call (avoids captive-dependency anti-pattern). |
| `error_handling.py` | Single exception class: `PartialContainerError`. |

### Container lifecycle

1. **Register** — `register_singleton`, `register_transient`, `register_singleton_factory`, `register_transient_factory`. Each call creates a `Registration` dataclass and stores it in `_registered`. Registering two objects under the same key automatically promotes them to a `ListOfDependencies` group.
2. **Build** — `build()` runs `_DependencyAnalyser.build_graph()` then `_topological_sort`, and for each key calls `__ensure_built`, which dispatches on `(RegistrationType, object_category)` via a `match` statement. Singleton conditions are evaluated here; transient conditions are deferred.
3. **Resolve** — `resolve(key)` calls `__resolve_value` on the cached `BuiltEntry`. `SingletonBuilt` returns its value directly; `TransientBuilt` calls the stored `TransientContainer` factory for a fresh value; `GroupBuilt` resolves each item into a list.

### Key invariants

- **Transient functions are cloned** via `FunctionType` reconstruction (sharing bytecode/globals but with an independent `__dict__`) so attribute mutations on one resolution cannot affect another.
- **Singleton-depends-on-transient** is handled by `_FunctionWirer._make_dynamic_wrapper`: a closure that re-resolves the transient entry on every invocation rather than capturing it once at build time.
- **`inject_returns=True`** wraps the wired callable so when it returns a function, that function is recursively wired through the same wirer before being returned to the caller. Works transparently with `async def`.
- **Parameter matching priority**: name → type annotation → `ListOfDependencies[annotation]` (for grouped registrations).
