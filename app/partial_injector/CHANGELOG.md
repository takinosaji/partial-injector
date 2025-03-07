# Changelog

> The changelog **must** comply to the [keep a changelog](https://keepachangelog.com/en/1.1.0) standard.

## 2.3.4 - 2025-03-06

_*Added*_

- Ability to ignore the registrations, discarded by condition, during container build.
- Registration of both list and single key for a single registration remained after condition checks

## 2.2.2 - 2025-03-03

_*Fixed*_

- Broken build of FromContainer dependencies

## 2.2.0 - 2025-03-03

_*Added*_

- Ability to pass list to register_instance method with new argument `inject_items=True`. 
  This will make container to register each list item separately and bound all of them to the provided key
  instead of registering whole list as a single instance.

## 2.1.2 - 2025-02-28

_*Fixed*_

- More scenarios of registrations of dependencies with same key

## 2.1.1 - 2025-02-27

_*Fixed*_

- Multiple registrations of dependencies with same key

## 2.1.0 - 2025-02-22

_*Added*_

- Support for async injected outputs

## 2.0.2 - 2025-02-21

_*Fixed*_

- Erroneous usage of typing-extensions module

## 2.0.1 - 2025-02-16

_*Fixed*_

- Missing package content

## 2.0.0 - 2025-02-16

_*Removed*_

- pinq module from the package scope

## 1.0.1 - 2025-02-16

_*Fixed*_

- BOM in README files

## 1.0.0 - 2025-02-16

_*Added*_

- First version of partial-injector
