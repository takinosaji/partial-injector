"""
_function_wirer — produces wired callables from registered functions.

``_FunctionWirer`` inspects a callable's signature and returns a version with
registered dependencies pre-filled:

- **Singleton deps** are resolved once and baked in via ``functools.partial``.
- **Transient deps** are deferred — a closure wrapper re-resolves them fresh on
  every call, avoiding the "captive dependency" anti-pattern where a singleton
  holds a permanently frozen copy of what should be a transient.

The wirer owns no build state.  It communicates with ``Container`` through two
callbacks supplied at construction time (see ``__init__`` docstring).
"""

import functools
import inspect
from collections.abc import Callable
from inspect import isfunction
from typing import Any

from partial_injector._algorithms import _find_param_key, _is_dynamic_entry
from partial_injector._entries import BuiltEntry
from partial_injector._models import ContainerKey


class _FunctionWirer:
    """
    Produces wired callables from registered functions.

    Constructor parameters
    ----------------------
    registered : dict
        Live reference to ``Container._registered`` — read-only, used for
        parameter key lookup.
    lod_class : type
        ``Container.ListOfDependencies`` — needed to construct group keys.
    lookup_entry : (reg_key, param_is_list) -> BuiltEntry | None
        Ensures *reg_key* is built and returns its ``BuiltEntry``, or ``None``
        when condition-blocked or when multiple registrations exist for a
        scalar-typed parameter.
    resolve_value : (entry) -> Any
        Materialises a ``BuiltEntry`` into its concrete value.
    """

    def __init__(
        self,
        registered: dict,
        lod_class: type,
        lookup_entry: Callable[[ContainerKey, bool], BuiltEntry | None],
        resolve_value: Callable[[BuiltEntry], Any],
    ) -> None:
        self._registered = registered
        self._lod = lod_class
        self._lookup_entry = lookup_entry
        self._resolve_value = resolve_value

    def wire(self, func: Callable, inject_returns: bool) -> Callable:
        """
        Return a wired version of *func* with registered dependencies pre-filled.

        Each parameter is matched against the registration store by name first,
        then by type annotation.  Parameters with no registered match are left
        open for the caller to supply.

        When *inject_returns* is ``True`` and the wired function itself returns
        a callable, that returned callable is recursively wired before being
        handed back to the caller.  This supports factory patterns where a
        function produces another function that also needs injection.

        ``VAR_POSITIONAL`` (``*args``), ``VAR_KEYWORD`` (``**kwargs``), and
        ``POSITIONAL_ONLY`` (``/``) parameters are never injected by keyword
        and are always left open.
        """
        sig = inspect.signature(func)
        if not sig.parameters:
            return self._wrap_for_return_injection(func) if inject_returns else func

        static_kwargs: dict[str, Any] = {}
        dynamic_deps: dict[str, BuiltEntry] = {}

        for param_name, param in sig.parameters.items():
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
                inspect.Parameter.POSITIONAL_ONLY,
            ):
                continue

            reg_key, param_is_list = _find_param_key(
                self._registered, self._lod, param_name, param
            )
            if reg_key is None:
                continue

            entry = self._lookup_entry(reg_key, param_is_list)
            if entry is None:
                continue

            if _is_dynamic_entry(entry):
                dynamic_deps[param_name] = entry
            else:
                static_kwargs[param_name] = self._resolve_value(entry)

        if not static_kwargs and not dynamic_deps:
            return self._wrap_for_return_injection(func) if inject_returns else func

        wired = (
            self._make_dynamic_wrapper(func, static_kwargs, dynamic_deps)
            if dynamic_deps
            else functools.partial(func, **static_kwargs)
        )
        return self._wrap_for_return_injection(wired) if inject_returns else wired

    def _make_dynamic_wrapper(
        self,
        func: Callable,
        static_kwargs: dict[str, Any],
        dynamic_deps: dict[str, BuiltEntry],
    ) -> Callable:
        """
        Wrap *func* so transient dependencies are re-resolved on every call.

        *static_kwargs* (singleton deps) are pre-applied once via ``functools.partial``.
        *dynamic_deps* entries are resolved fresh on each invocation so callers
        always receive a new transient instance rather than a captive copy.
        Both sync and async callables are supported.
        """
        partially_applied: Callable = (
            functools.partial(func, **static_kwargs) if static_kwargs else func
        )
        resolve = self._resolve_value

        if inspect.iscoroutinefunction(func):

            async def _async_dynamic_wrapper(*args: Any, **kwargs: Any) -> Any:
                fresh = {name: resolve(dep) for name, dep in dynamic_deps.items()}
                return await partially_applied(*args, **fresh, **kwargs)

            functools.update_wrapper(_async_dynamic_wrapper, func)
            return _async_dynamic_wrapper

        def _dynamic_wrapper(*args: Any, **kwargs: Any) -> Any:
            fresh = {name: resolve(dep) for name, dep in dynamic_deps.items()}
            return partially_applied(*args, **fresh, **kwargs)

        functools.update_wrapper(_dynamic_wrapper, func)
        return _dynamic_wrapper

    def _wrap_for_return_injection(self, func: Callable) -> Callable:
        """
        Wrap *func* so that when it returns a callable, that callable is itself
        wired through the container before being returned to the caller.

        Wiring is applied recursively — the returned function is treated as if
        ``inject_returns=True`` had been set on it too.  Both sync and async
        callables are supported.
        """
        if inspect.iscoroutinefunction(func):

            async def _async_wrapper(*args: Any, **kwargs: Any) -> Any:
                result = await func(*args, **kwargs)
                if isfunction(result):
                    return self.wire(result, inject_returns=True)
                return result

            return _async_wrapper

        def _sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            if isfunction(result):
                return self.wire(result, inject_returns=True)
            return result

        return _sync_wrapper
