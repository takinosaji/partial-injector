# sversion

Simple version retrieval for Python projects. Walks up the directory tree from a given path and reads the version from a `pyproject.toml` or a plain `VERSION.txt` file.

## Requirements

Python 3.14+

## Installation

```bash
pip install sversion
```

## Usage

### From `pyproject.toml`

Reads `project.version` (PEP 621) or `tool.poetry.version`:

```python
from sversion.pyproject_toml_based import get_version

version = get_version(__file__)
print(version)  # e.g. "1.2.3"
```

Pass a custom filename to look for a differently named TOML file:

```python
version = get_version(__file__, project_file_name="my_project.toml")
```

### From a version file

Reads the first non-whitespace content of a `VERSION.txt` file:

```python
from sversion.version_file_based import get_version

version = get_version(__file__)
print(version)  # e.g. "1.2.3"
```

Pass a custom filename:

```python
version = get_version(__file__, version_file_name="RELEASE")
```

### How the search works

Both functions accept either a file path or a directory path as `start_search_path`. Starting from that location they walk up the directory tree, checking each level for the target file, and return the version from the first match found.

## API

```python
# pyproject_toml_based
get_version(start_search_path: str, project_file_name: str = "pyproject.toml") -> str

# version_file_based
get_version(start_search_path: str, version_file_name: str = "VERSION.txt") -> str
```

Both raise `VersionNotFoundException` (from `sversion.error_handling`) when no matching file is found before reaching the filesystem root.

## License

MIT
