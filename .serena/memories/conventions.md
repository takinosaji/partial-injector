# Conventions

## Module & API surface
- Internal modules are `_`-prefixed (`_models.py`, `_entries.py`, `_algorithms.py`, `_dependency_analyser.py`, `_function_wirer.py`); public ones are not (`partial_container.py`, `error_handling.py`, `contracts.py`).
- `__init__.py` re-exports **modules, not symbols**: `from . import error_handling, partial_container` + `__all__ = [...]`, plus `__author__ = "kostiantyn.chomakov@gmail.com"`. Consumers import `from partial_injector.partial_container import Container`. Keep it that way — do not flatten the API into `__init__`.
- `_models.py` exists purely to break import cycles; put shared dataclasses/aliases there rather than cross-importing sibling modules.
- One exception class per package in `error_handling.py` (`PartialContainerError`, `VersionNotFoundException`).

## Style
- Full type hints on public signatures; type aliases collected in a `contracts.py` when a package has them (`Version = str`, `VersionRetriever = Callable[[str], Version]`).
- To type a public function as an alias, define it privately and rebind: `get_version = __get_version` — not a bare `def`.
- Class-private helpers use double-underscore name mangling (`Container.__ensure_built`, `__resolve_value`); only the documented lifecycle methods are public.
- `spinq` public functions end in a trailing `_` (`first_`, `where_`, `all_`) to avoid shadowing builtins. Raising variants raise `ValueError`; `*_or_none_` variants return `None`.
- Dispatch on variant types with `match` statements over sealed dataclass hierarchies (`BuiltEntry` union in `_entries.py`), not isinstance chains.
- Docstrings are sparse in library code; used in `sdlc/` scripts. Logging via module-level `logger = logging.getLogger(__name__)` with `%s` lazy formatting.

## Tests
- One file per scenario, named `test_case_<scenario>.py` (`test_from_container.py` is the exception), grouped in a folder per subject (`test_partial_container/`).
- **No conftest.py, no shared fixtures** — each test constructs its own `Container` inline.
- Explicit `# Arrange` / `# Act` / `# Assert` (or `# Act / Assert`) comment blocks in every test.
- Assert on exception messages with `pytest.raises(Err, match=re.escape("..."))` — messages are part of the contract; changing one requires updating tests.
- `sversion` tests patch `os.path.exists` / `builtins.open` (`unittest.mock.patch`); they never touch the real filesystem.
