"""
_algorithms — pure stateless functions used across the container internals.

All functions here are side-effect-free: they take their full input as arguments
and return a result.  No Container state, no class instances.

Functions
---------
_registration_category   Classify a registration object for build dispatch.
_copy_object             Produce an independent copy of a function or instance.
_is_dynamic_entry        Decide whether a BuiltEntry needs re-resolution per call.
_find_param_key          Match a function parameter to a registered key.
_topological_sort        Order a dependency graph (Kahn's algorithm).
_find_cycle              Find one cycle in a graph (DFS), used for error messages.
"""

import copy
import functools
import inspect
from collections import deque
from inspect import isfunction
from types import FunctionType
from typing import Any

from partial_injector._entries import (
    BuiltEntry,
    GroupBuilt,
    SingletonBuilt,
    TransientBuilt,
)
from partial_injector._models import (
    ContainerKey,
    FromContainer,
)
from partial_injector.error_handling import PartialContainerError


def _registration_category(obj: Any, inject_items: bool) -> str:
    """
    Classify *obj* for dispatch in ``Container.__build_registration``.

    Returns one of: ``"from_container"``, ``"function"``, ``"list"``, ``"instance"``.
    """
    if isinstance(obj, FromContainer):
        return "from_container"
    if isfunction(obj):
        return "function"
    if isinstance(obj, list) and inject_items:
        return "list"
    return "instance"


def _copy_object(target: Any) -> Any:
    """
    Return an independent copy of *target*.

    Functions: a new ``FunctionType`` sharing the original's bytecode, globals,
    and closure but with its own ``__dict__``, so attribute mutations on one
    resolution cannot affect another.
    All other objects: ``copy.deepcopy``.
    """
    if isfunction(target):
        clone = FunctionType(
            target.__code__,
            target.__globals__,
            name=target.__name__,
            argdefs=target.__defaults__,
            closure=target.__closure__,
        )
        functools.update_wrapper(clone, target)
        if hasattr(target, "__signature__"):
            clone.__signature__ = inspect.signature(target)
        if hasattr(target, "__kwdefaults__"):
            clone.__kwdefaults__ = target.__kwdefaults__
        if hasattr(target, "__annotations__"):
            clone.__annotations__ = target.__annotations__
        return clone
    return copy.deepcopy(target)


def _is_dynamic_entry(entry: BuiltEntry) -> bool:
    """
    Return ``True`` when *entry* must be re-resolved on every function call.

    ``TransientBuilt`` is always dynamic.  ``GroupBuilt`` is dynamic when it
    contains at least one ``TransientBuilt`` item.  ``SingletonBuilt`` is static.
    """
    match entry:
        case TransientBuilt():
            return True
        case GroupBuilt(items=items):
            return any(isinstance(item, TransientBuilt) for item in items)
        case SingletonBuilt():
            return False


def _find_param_key(
    registered: dict,
    lod_class: type,
    param_name: str,
    param: inspect.Parameter,
) -> tuple[ContainerKey | None, bool]:
    """
    Find the registration key that best matches a function parameter.

    Lookup priority: parameter name → type annotation → ``lod_class[annotation]``
    (for grouped registrations).

    Returns ``(key, param_is_list)`` where *key* is ``None`` when nothing matched
    and *param_is_list* is ``True`` when the annotation is ``list[T]``.
    """
    annotation = param.annotation
    no_annotation = annotation is inspect.Parameter.empty

    param_is_list = (
        not no_annotation
        and hasattr(annotation, "__origin__")
        and annotation.__origin__ is list
    )

    if no_annotation:
        group_key = None
    elif param_is_list:
        group_key = lod_class[annotation.__args__[0]]
    else:
        group_key = lod_class[annotation]

    if param_name in registered:
        return param_name, param_is_list
    if not no_annotation and annotation in registered:
        return annotation, param_is_list
    if group_key is not None and group_key in registered:
        return group_key, param_is_list

    return None, param_is_list


def _topological_sort(
    graph: dict[ContainerKey, frozenset[ContainerKey]],
) -> list[ContainerKey]:
    """
    Return the keys of *graph* in dependency order (deps before dependents).

    Uses Kahn's algorithm (BFS).  Raises ``PartialContainerError`` when a cycle
    is detected, with a descriptive path produced by ``_find_cycle``.
    """
    in_degree: dict[ContainerKey, int] = {k: 0 for k in graph}
    reverse: dict[ContainerKey, list[ContainerKey]] = {k: [] for k in graph}
    for key, deps in graph.items():
        for dep in deps:
            in_degree[key] += 1
            reverse[dep].append(key)

    queue: deque[ContainerKey] = deque(k for k in graph if in_degree[k] == 0)
    order: list[ContainerKey] = []

    while queue:
        key = queue.popleft()
        order.append(key)
        for dependent in reverse[key]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(order) < len(graph):
        cycle = _find_cycle(graph)
        path = " → ".join(str(k) for k in cycle)
        raise PartialContainerError(f"Circular dependency detected: {path}")

    return order


def _find_cycle(
    graph: dict[ContainerKey, frozenset[ContainerKey]],
) -> list[ContainerKey]:
    """
    Find and return one cycle in *graph* using DFS.

    Returns a list that begins and ends at the same key, e.g. ``[A, B, C, A]``.
    """
    visited: set[ContainerKey] = set()
    path: list[ContainerKey] = []
    path_set: set[ContainerKey] = set()

    def dfs(node: ContainerKey) -> list[ContainerKey] | None:
        visited.add(node)
        path.append(node)
        path_set.add(node)
        for dep in graph.get(node, frozenset()):
            if dep not in graph:
                continue
            if dep in path_set:
                idx = path.index(dep)
                return [*path[idx:], dep]
            if dep not in visited:
                result = dfs(dep)
                if result is not None:
                    return result
        path.pop()
        path_set.discard(node)
        return None

    for node in graph:
        if node not in visited:
            cycle = dfs(node)
            if cycle:
                return cycle
    return []
