# partial-injector

**Dependency injection for functional Python.** Wire plain functions together with `functools.partial` — no decorators, no metaclasses, no framework lock-in.

```python
from partial_injector.partial_container import Container

def get_db_url() -> str:
    return "postgresql://localhost/mydb"

def find_user(db_url: str, user_id: int) -> dict:
    ...  # db_url pre-filled by the container

container = Container()
container.register_singleton(get_db_url)
container.register_singleton(find_user)
container.build()

find = container.resolve(find_user)
user = find(user_id=42)   # db_url already injected
```

---

## Why partial-injector?

Most Python DI frameworks are built around **classes** — you annotate `__init__` parameters, inherit from a base, or stack decorators. That works fine for OOP, but Python's best code is often just functions.

`partial-injector` is built differently:

- **Functions are first-class citizens.** Register a plain function; the container inspects its type annotations, finds matching registrations, and returns a `functools.partial` with those arguments pre-filled. You call it as normal.
- **No decorators required.** Your business logic has zero knowledge of the container. Swap the container out in tests without touching production code.
- **Proper transient lifecycle.** Transient dependencies registered as functions or instances are cloned fresh on every resolution — no captive-dependency anti-pattern where a singleton ends up holding a permanently frozen copy of what should be a live object.
- **Automatic build order.** `build()` runs a topological sort of all registered keys and detects cycles with a descriptive path — you see exactly which keys form the loop.
- **Async-native.** Everything works transparently with `async def` functions: injected wrappers, factory results, and return-injection.

---

## Installation

```bash
pip install partial-injector
```

**Requires Python 3.12+**

---

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Registration Types](#registration-types)
3. [Registration Keys](#registration-keys)
4. [Dependency Matching](#dependency-matching)
5. [FromContainer](#fromcontainer)
6. [Multiple Registrations for the Same Key](#multiple-registrations-for-the-same-key)
7. [Conditional Registrations](#conditional-registrations)
8. [inject\_returns — wiring factory outputs](#inject_returns--wiring-factory-outputs)
9. [inject\_items — per-element injection in lists](#inject_items--per-element-injection-in-lists)
10. [Async Support](#async-support)
11. [Transient Lifecycle in Depth](#transient-lifecycle-in-depth)
12. [Error Handling](#error-handling)
13. [API Reference](#api-reference)

---

## Core Concepts

### The three-step lifecycle

```python
container = Container()

# 1. Register — declare what exists and how to build it
container.register_singleton(my_service, key=MyService)

# 2. Build — resolve dependency order, wire everything up
container.build()

# 3. Resolve — retrieve the wired object
svc = container.resolve(MyService)
```

No registrations are allowed after `build()`. No resolution is allowed before it.

---

## Registration Types

| Method | When it builds | What `resolve()` returns |
|---|---|---|
| `register_singleton` | Once, at `build()` time | The same wired object every time |
| `register_transient` | Deferred until `resolve()` | A **fresh copy** on every call |
| `register_singleton_factory` | Calls the factory once at `build()` | Cached result of that factory call |
| `register_transient_factory` | Calls the factory on every `resolve()` | New result each time |

```python
container = Container()

# singleton — one shared instance
container.register_singleton(DatabasePool(max_connections=10), key=DatabasePool)

# transient — fresh copy per resolve
container.register_transient(RequestContext(), key=RequestContext)

# singleton factory — builds once from a callable
container.register_singleton_factory(lambda: connect("postgresql://localhost/db"), key="conn")

# transient factory — calls the factory fresh each time
container.register_transient_factory(lambda: uuid.uuid4(), key="request_id")

container.build()
```

---

## Registration Keys

Every registration needs a key for later lookup. The default key is the registered object itself — convenient for functions and types:

```python
container.register_singleton(my_function)         # key = my_function
container.register_singleton(MyService())         # key = MyService() (the instance — rarely useful)
container.register_singleton(MyService(), key=MyService)  # key = MyService (the class — good)
```

Keys can be **any hashable value**: a type, a string, a `TypeAlias`, or a function:

```python
# string key
container.register_singleton("postgresql://localhost/db", key="db_url")

# type key
container.register_singleton(42, key=int)

# TypeAlias key (PEP 695)
type Greeter = Callable[[str], str]
container.register_singleton(make_greeter, key=Greeter)
```

---

## Dependency Matching

When the container wires a function, it inspects every parameter and tries to find a match in the registry. The lookup order is:

1. **Parameter name** — is there a registration whose key equals the parameter name?
2. **Type annotation** — is there a registration whose key equals the annotation?
3. **Group key** — is there a group of registrations under `list[annotation]`?

Parameters with no match are left **unbound** — the caller supplies them.

```python
type Multiplier = Callable[[], int]

def get_multiplier() -> int:
    return 6

def compute(get_multiplier: Multiplier, x: int) -> int:
    # get_multiplier is resolved from the container
    # x is left for the caller to supply
    return get_multiplier() * x

container = Container()
container.register_singleton(get_multiplier, key=Multiplier)
container.register_singleton(compute)
container.build()

fn = container.resolve(compute)
print(fn(x=7))   # 42
```

> **Tip:** Using `TypeAlias` keys for callable types (`type Greeter = Callable[[str], str]`) gives your dependency graph a vocabulary beyond raw types and avoids accidental collisions with built-in types like `str` or `int`.

---

## FromContainer

`FromContainer` lets one registration derive its value from another, with an optional selector lambda. This is especially useful for slicing a configuration object into individual settings:

```python
from partial_injector.partial_container import Container, FromContainer
from dataclasses import dataclass

@dataclass
class Config:
    db_url: str
    secret_key: str
    debug: bool

container = Container()
container.register_singleton(
    Config(db_url="postgresql://localhost/db", secret_key="s3cr3t", debug=False),
    key=Config,
)
container.register_singleton(FromContainer(Config, lambda c: c.db_url),    key="db_url")
container.register_singleton(FromContainer(Config, lambda c: c.secret_key), key="secret_key")
container.register_singleton(FromContainer(Config, lambda c: c.debug),      key="debug")
container.build()

db_url = container.resolve("db_url")  # "postgresql://localhost/db"
```

`FromContainer` can also appear inside `factory_args` and `factory_kwargs`, where it is resolved just before the factory is called:

```python
def connect(url: str, debug: bool) -> Connection: ...

container.register_singleton_factory(
    connect,
    key=Connection,
    factory_args=[FromContainer(Config, lambda c: c.db_url)],
    factory_kwargs={"debug": FromContainer(Config, lambda c: c.debug)},
)
```

---

## Multiple Registrations for the Same Key

Register more than one object under the same key and the container automatically groups them. Resolve as `list[Key]` to get all, or as the bare `Key` if only one survives its condition:

```python
type Middleware = Callable[[Request], Request]

def auth_middleware(request: Request) -> Request: ...
def logging_middleware(request: Request) -> Request: ...
def rate_limit_middleware(request: Request) -> Request: ...

container = Container()
container.register_singleton(auth_middleware,       key=Middleware)
container.register_singleton(logging_middleware,    key=Middleware)
container.register_singleton(rate_limit_middleware, key=Middleware)
container.build()

middlewares = container.resolve(list[Middleware])   # [auth, logging, rate_limit]
```

**Injecting a group into a function** — annotate the parameter as `list[Key]`:

```python
type Validator = Callable[[str], bool]

def validate_all(validators: list[Validator], value: str) -> bool:
    return all(v(value) for v in validators)

container.register_singleton(validate_all)
container.build()

fn = container.resolve(validate_all)
fn(value="hello")   # all validators pre-filled, only value is open
```

---

## Conditional Registrations

Every `register_*` method accepts a `condition` callable. The result determines whether the registration is included at all.

```python
import os

container = Container()
container.register_singleton(
    ProductionDatabase(),
    key="db",
    condition=lambda: os.getenv("ENV") == "production",
)
container.register_singleton(
    InMemoryDatabase(),
    key="db",
    condition=lambda: os.getenv("ENV") != "production",
)
container.build()

db = container.resolve("db")   # whichever condition passed
```

**Condition evaluation timing:**

| Registration type | When condition runs |
|---|---|
| `SINGLETON` / `SINGLETON_FACTORY` | At `build()` time |
| `TRANSIENT` / `TRANSIENT_FACTORY` | Lazily, at each `resolve()` call |

This means transient conditions can respond to runtime state — a feature flag read from a database, a per-request context, etc.

**Conditions with injected arguments** — pass `condition_args` or `condition_kwargs` to inject `FromContainer` values into the condition callable:

```python
def is_feature_enabled(config: Config) -> bool:
    return config.feature_flags.get("new_ui", False)

container.register_singleton(
    NewUIRenderer(),
    key=Renderer,
    condition=is_feature_enabled,
    condition_args=[FromContainer(Config)],
)
```

**Strict mode** — set `throw_if_condition_not_satisfied=True` to raise `PartialContainerError` when no registration for a key passes its condition, instead of silently omitting it.

---

## inject_returns — wiring factory outputs

When a registered function *returns another function*, set `inject_returns=True` to wire that returned function's parameters through the container too. This supports factory patterns without any boilerplate:

```python
type Handler = Callable[[str], None]
type HandlerFactory = Callable[[], Handler]

def make_handler(logger: Callable[[str], None]) -> Handler:
    def handle(message: str) -> None:
        logger(f"[handler] {message}")
    return handle

container = Container()
container.register_singleton(print, key=Callable[[str], None])
container.register_singleton(make_handler, key=HandlerFactory, inject_returns=True)
container.build()

factory = container.resolve(HandlerFactory)
handler = factory()       # returns `handle` with `logger` already injected
handler("ping")           # prints "[handler] ping"
```

Return injection is **recursive** — the returned function can itself return a function that also gets wired — and works transparently with `async def`.

---

## inject_items — per-element injection in lists

Register a list and set `inject_items=True` to have each element wired individually rather than treating the list as a single opaque object:

```python
type Processor = Callable[[int], int]

def scale(factor: int, value: int) -> int:
    return value * factor

def shift(offset: int, value: int) -> int:
    return value + offset

container = Container()
container.register_singleton(3, key=int)
container.register_singleton([scale, shift], key=list[Processor], inject_items=True)
container.build()

processors = container.resolve(list[Processor])
# scale has `factor=3` pre-filled; shift has `offset=3` pre-filled
results = [p(10) for p in processors]  # [30, 13]
```

---

## Async Support

There is nothing special to configure. The container handles `async def` functions at every level:

```python
async def fetch_user(db: Database, user_id: int) -> User: ...

async def handle_request(fetch_user: Callable, request: Request) -> Response:
    user = await fetch_user(user_id=request.user_id)
    ...

container = Container()
container.register_singleton(db_instance, key=Database)
container.register_singleton(fetch_user)
container.register_singleton(handle_request)
container.build()

handler = container.resolve(handle_request)
response = await handler(request=req)   # db pre-filled; request supplied by caller
```

Async functions also work with `inject_returns` — the wrapper awaits the outer function and wires the returned callable before handing it back.

---

## Transient Lifecycle in Depth

`partial-injector` enforces strict transient semantics with no captive-dependency anti-pattern.

**What is captive dependency?**
It occurs when a singleton captures a transient at build time and holds onto that single frozen instance permanently — defeating the purpose of registering it as transient.

**How partial-injector prevents it:**
When a singleton *function* depends on a transient, the container does not resolve the transient eagerly. Instead it builds a closure that re-resolves the transient on every invocation:

```python
from dataclasses import dataclass, field
import uuid

@dataclass
class RequestContext:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

def process(ctx: RequestContext, payload: str) -> str:
    return f"[{ctx.request_id}] {payload}"

container = Container()
container.register_transient(RequestContext(), key=RequestContext)
container.register_singleton(process)
container.build()

fn = container.resolve(process)
print(fn(payload="a"))   # [3f2a...] a
print(fn(payload="b"))   # [9c1e...] b  ← fresh RequestContext every time
```

**Transient copy semantics:**

| Registered object | What `resolve()` returns |
|---|---|
| Plain instance | `copy.deepcopy` of the original |
| Function | New `FunctionType` sharing bytecode but with independent `__dict__` |
| List with `inject_items=True` | Each element deep-copied and re-wired independently |

---

## Error Handling

All errors raise `PartialContainerError` from `partial_injector.error_handling`:

```python
from partial_injector.error_handling import PartialContainerError

try:
    container.resolve(MyService)
except PartialContainerError as e:
    print(e.message)
```

| Situation | Error message |
|---|---|
| Register after `build()` | `"Container already built"` |
| `resolve()` before `build()` | `"Container not built"` |
| Key not registered | `"Object with key <key> not registered"` |
| Key registered but not built | `"Object with key <key> not built"` |
| Condition not met, `throw=True` | `"No object with key <key> was built because the built condition has not been met."` |
| Circular dependency | `"Circular dependency detected: A → B → C → A"` |

---

## API Reference

### `Container`

```python
from partial_injector.partial_container import Container
```

#### Registration

```python
container.register_singleton(
    instance,
    key=None,              # lookup key; defaults to instance itself
    inject_returns=False,  # wire the callable returned by this function
    inject_items=False,    # wire each element of a registered list individually
    condition=None,        # () -> bool; False skips this registration
    condition_args=None,   # positional args passed to condition
    condition_kwargs=None, # keyword args passed to condition
    throw_if_condition_not_satisfied=False,
)

container.register_transient(instance, key=None, ...)   # same signature

container.register_singleton_factory(
    factory,
    key=None,
    factory_args=None,     # positional args for factory (FromContainer allowed)
    factory_kwargs=None,   # keyword args for factory (FromContainer allowed)
    inject_returns=False,
    condition=None, ...,
)

container.register_transient_factory(factory, key=None, ...)  # same signature
```

#### Lifecycle

```python
container.build()            # topological sort + wire; must be called before resolve
container.resolve(key)       # return the wired object for key
```

---

### `FromContainer`

```python
from partial_injector.partial_container import FromContainer

FromContainer(source_key)                        # resolve source_key as-is
FromContainer(source_key, lambda val: val.attr)  # apply selector to resolved value
```

Used as a registration value or as an element inside `factory_args` / `factory_kwargs`.

---

## License

MIT
