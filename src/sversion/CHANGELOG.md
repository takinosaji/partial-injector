# Changelog

> The changelog **must** comply to the [keep a changelog](https://keepachangelog.com/en/1.1.0) standard.

## 2.5.0 - 2026-05-28

_*Fixed*_

- `pyproject_toml_based` was listed in `__all__` but never imported in `__init__.py`; direct `from sversion import pyproject_toml_based` now works as expected
- Unclosed file handle in `version_file_based.get_version` replaced with a `with` statement

_*Changed*_

- Added module and function docstrings throughout

## 2.4.0 - 2026-05-19

_*Changed*_

- Lowered minimum supported Python version to 3.12

## 2.3.0 - 2026-03-21

_*Added*_

- uv support for pyproject_toml_based get_version method

## 2.2.1 - 2026-03-08

_*Added*_

- get_version method that works with pyproject.toml file


## 2.1.0 - 2025-04-29

_*Changed*_

- Project dependency and build system to poetry

## 2.0.0 - 2025-02-20

_*Changed*_

- File-based get_version method to use location to start search of version file from as a parameter


## 1.0.0 - 2025-02-20

_*Added*_

- First version of sversion
