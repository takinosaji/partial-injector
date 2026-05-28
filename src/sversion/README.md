# sversion

[![PyPI version](https://img.shields.io/pypi/v/sversion.svg)](https://pypi.org/project/sversion/)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Zero-config version retrieval for Python packages. Pass `__file__` and get your package version back — no hard-coding, no import tricks, no build-time templating.

Supports `pyproject.toml` (PEP 621 and Poetry layouts) and plain `VERSION.txt` files.

## Install

```bash
pip install sversion
```

## Quick start

The most common use is exposing `__version__` from a package `__init__.py`:

```python
# my_package/__init__.py
from sversion.pyproject_toml_based import get_version

__version__ = get_version(__file__)
```

`get_version` walks up from `my_package/` until it finds `pyproject.toml` and reads the version from it. No path configuration needed.

## How the search works

Starting at the path you pass, both strategies walk up the directory tree level by level until the target file is found or the filesystem root is reached:

```
my_repo/
├── my_package/
│   └── __init__.py   ← pass __file__ here
├── tests/
└── pyproject.toml    ← found here, version returned
```

Both file paths and directory paths are accepted. When a file is passed, the search starts in its parent directory.

---

## From `pyproject.toml`

Reads `project.version` (PEP 621) or `tool.poetry.version`:

```python
from sversion.pyproject_toml_based import get_version

version = get_version(__file__)             # "1.2.3"
version = get_version("/path/to/project")  # directory path also works
```

Use `project_file_name` to look for a non-standard filename:

```python
version = get_version(__file__, project_file_name="my_project.toml")
```

## From a version file

Reads the trimmed contents of a `VERSION.txt` file:

```python
from sversion.version_file_based import get_version

version = get_version(__file__)
version = get_version(__file__, version_file_name="RELEASE")  # custom filename
```

## Error handling

Both functions raise `VersionNotFoundException` when no matching file is found before reaching the filesystem root:

```python
from sversion.pyproject_toml_based import get_version
from sversion.error_handling import VersionNotFoundException

try:
    version = get_version(__file__)
except VersionNotFoundException as e:
    version = "unknown"
```

## API

```python
# pyproject_toml_based
get_version(start_search_path: str, project_file_name: str = "pyproject.toml") -> str

# version_file_based
get_version(start_search_path: str, version_file_name: str = "VERSION.txt") -> str
```

Both raise `sversion.error_handling.VersionNotFoundException` on failure.

---

## License

MIT
