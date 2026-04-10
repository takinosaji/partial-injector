# Partial Injector

A dependency injection container for Python designed around functional programming. It uses `functools.partial` to wire dependencies into functions, making it a natural fit for FP-style code where services are plain functions rather than class instances.

## Requirements

Python 3.14+

## Installation

```bash
pip install partial-injector
```

## Quick Start

```python
from partial_injector.partial_container import Container

def get_multiplier() -> int:
    return 6

def get_answer(get_multiplier: callable) -> int:
    return get_multiplier() * 7

container = Container()
container.register_singleton(get_multiplier)
container.register_singleton(get_answer)
container.build()

answer = container.resolve(get_answer)
print(answer())  # 42
```

The container inspects `get_answer`'s parameter annotations, finds `get_multiplier` is registered, and creates a partial that pre-fills it.

## Core Concepts

### Registration Keys

Every registration has a key used to look it up later. By default the registered object itself (function, class, or instance) is the key. Pass `key=` to use something else — a type, a string, or a `TypeAlias`.

```python
container.register_singleton(42, key=int)
container.register_singleton("hello", key="greeting")
```

### Registration Types

| Method | Behaviour |
|--------|-----------|
| `register_singleton` | Built once at `build()` time; every `resolve()` returns the same object. |
| `register_transient` | A fresh deep copy (or new partial) is produced on each `resolve()`. |
| `register_singleton_factory` | Calls a factory at `build()` time; result is cached like a singleton. |
| `register_transient_factory` | Calls the factory on every `resolve()`. |

### Build and Resolve

```python
container.build()          # wire all dependencies; no new registrations allowed after this
value = container.resolve(key)
```

## Dependency Injection into Functions

The container resolves function parameters by matching each parameter's **type annotation** (or **parameter name**) against registered keys:

```python
from typing import Callable

type Greeter = Callable[[str], str]

def make_greeter(prefix: str) -> Greeter:
    def greet(name: str) -> str:
        return f"{prefix}, {name}!"
    return greet

container = Container()
container.register_singleton("Hello", key=str)
container.register_singleton_factory(make_greeter, key=Greeter)
container.build()

greeter = container.resolve(Greeter)
print(greeter("World"))  # Hello, World!
```

Parameters that cannot be resolved are left unbound — they become arguments the caller supplies.

## FromContainer

`FromContainer` lets one registration derive its value from another, optionally via a selector lambda:

```python
from partial_injector.partial_container import Container, FromContainer
from dataclasses import dataclass

@dataclass
class Config:
    db_url: str
    debug: bool

container = Container()
container.register_singleton(Config(db_url="postgresql://localhost/mydb", debug=True), key=Config)
container.register_singleton(FromContainer(Config, lambda c: c.db_url), key="db_url")
container.register_singleton(FromContainer(Config, lambda c: c.debug), key="debug")
container.build()

db_url = container.resolve("db_url")  # "postgresql://localhost/mydb"
```

`FromContainer` can also be passed as a `factory_args` or `factory_kwargs` value, and it will be resolved at that point.

## Multiple Registrations for the Same Key

Registering more than one object under the same key groups them automatically. Resolve the group as `list[Key]`:

```python
from typing import Callable

type Validator = Callable[[str], bool]

def not_empty(value: str) -> bool:
    return len(value) > 0

def no_spaces(value: str) -> bool:
    return " " not in value

container = Container()
container.register_singleton(not_empty, key=Validator)
container.register_singleton(no_spaces, key=Validator)
container.build()

validators = container.resolve(list[Validator])
all_pass = all(v("hello") for v in validators)  # True
```

If only one of several registrations survives its condition, it can still be resolved as a single item by the bare key.

## Conditional Registrations

Every `register_*` method accepts `condition`, `condition_args`, `condition_kwargs`, and `throw_if_condition_not_satisfied`. The condition is a callable that returns `bool`; if it returns `False` the registration is skipped.

```python
import os

container = Container()
container.register_singleton(
    RealDatabase(),
    key="db",
    condition=lambda: os.getenv("ENV") == "production",
)
container.register_singleton(
    FakeDatabase(),
    key="db",
    condition=lambda: os.getenv("ENV") != "production",
)
container.build()
```

Set `throw_if_condition_not_satisfied=True` to raise `PartialContainerException` when no registration for a key passes its condition.

For `TRANSIENT` and `TRANSIENT_FACTORY` registrations the condition is evaluated lazily at each `resolve()` call rather than at `build()` time.

## inject\_returns

When a registered function *returns* another function, set `inject_returns=True` to wire that returned function's dependencies too:

```python
from typing import Callable

type Handler = Callable[[str], str]
type HandlerFactory = Callable[[], Handler]

def make_handler(logger: Callable[[str], None]) -> Handler:
    def handle(message: str) -> str:
        logger(message)
        return f"handled: {message}"
    return handle

container = Container()
container.register_singleton(print, key=Callable[[str], None])
container.register_singleton(make_handler, key=HandlerFactory, inject_returns=True)
container.build()

factory = container.resolve(HandlerFactory)
handler = factory()           # returns handle with logger already injected
handler("ping")               # prints "ping", returns "handled: ping"
```

This works recursively and supports `async` functions.

## inject\_items

Register a list of objects and set `inject_items=True` to have each element processed through the container's injection logic individually:

```python
type Processor = Callable[[int], int]

def double(factor: int, value: int) -> int:
    return value * factor

container = Container()
container.register_singleton(2, key=int)
container.register_singleton([double, double], key=list[Processor], inject_items=True)
container.build()

processors = container.resolve(list[Processor])
results = [p(3) for p in processors]  # [6, 6]
```

## Error Handling

All errors raise `PartialContainerException` from `partial_injector.error_handling`.

| Situation | Message |
|-----------|---------|
| Register after `build()` | `"Container already built"` |
| `resolve()` before `build()` | `"Container not built"` |
| Key not registered | `"Object with key <key> not registered"` |
| Key not built (condition failed, no throw) | key absent from resolved result |
| Key not built, `throw_if_condition_not_satisfied=True` | `"No object with key <key> was built because the built condition has not been met."` |
| Unresolvable parameter before a resolvable one | `"Cannot build partial function without registered parameter <name>:<type>"` |

## License

MIT
