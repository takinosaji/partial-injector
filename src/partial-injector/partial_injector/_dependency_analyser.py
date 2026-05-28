"""
_dependency_analyser — builds the dependency graph consumed by the topological sort.

``_DependencyAnalyser`` answers one question: *what does each registered key depend on?*
The resulting graph is passed to ``_topological_sort`` so ``Container.build()`` can
process keys in the correct order.
"""

import inspect
from collections.abc import Callable
from dataclasses import replace

from partial_injector._algorithms import _find_param_key, _registration_category
from partial_injector._models import (
    ContainerKey,
    ContainerObject,
    FromContainer,
    Registration,
    RegistrationType,
)


class _DependencyAnalyser:
    """
    Computes the dependency graph for all registered keys.

    Constructed with a live reference to ``Container._registered``; because
    Python dicts are passed by reference, the analyser always sees the current
    state of registrations at the time ``build_graph`` is called.
    """

    def __init__(self, registered: dict, lod_class: type) -> None:
        self._registered = registered
        self._lod = lod_class

    def build_graph(self) -> dict[ContainerKey, frozenset[ContainerKey]]:
        """Return ``{key: frozenset_of_deps}`` for every registered key."""
        return {k: self._key_deps(k) for k in self._registered}

    def _key_deps(self, key: ContainerKey) -> frozenset[ContainerKey]:
        """
        Return the set of *registered* keys that *key* depends on.

        Only keys present in ``_registered`` are returned — unregistered
        references are ignored here and raise an error at build time instead.
        """
        entry = self._registered[key]
        multiple = isinstance(entry, self._lod)
        regs: list[Registration] = entry.registrations if multiple else [entry]
        deps: set[ContainerKey] = set()
        for reg in regs:
            deps |= self._reg_deps(reg)
        return frozenset(deps & self._registered.keys())

    def _reg_deps(self, reg: Registration) -> frozenset[ContainerKey]:
        """
        Return all keys that a single ``Registration`` structurally depends on.

        Covers function parameter deps, ``FromContainer`` sources, factory
        args/kwargs, and condition args/kwargs.
        """
        cat = _registration_category(reg.obj, reg.inject_items)
        deps: set[ContainerKey] = set()

        match cat:
            case "from_container":
                deps.add(self._normalise_key(reg.obj.source_key))
            case "function":
                deps |= self._func_deps(reg.obj)
            case "list":
                for item in reg.obj:
                    deps |= self._reg_deps(replace(reg, obj=item))
            # "instance" has no structural deps

        if reg.type in (
            RegistrationType.SINGLETON_FACTORY,
            RegistrationType.TRANSIENT_FACTORY,
        ):
            deps |= self._injectable_arg_deps(reg.factory_args, reg.factory_kwargs)

        deps |= self._injectable_arg_deps(reg.condition_args, reg.condition_kwargs)
        return frozenset(deps)

    def _func_deps(self, func: Callable) -> frozenset[ContainerKey]:
        """Return the registered keys that *func*'s parameters resolve to."""
        deps: set[ContainerKey] = set()
        try:
            sig = inspect.signature(func)
        except ValueError, TypeError:
            return frozenset()
        for param_name, param in sig.parameters.items():
            reg_key, _ = _find_param_key(self._registered, self._lod, param_name, param)
            if reg_key is not None:
                deps.add(reg_key)
        return frozenset(deps)

    def _injectable_arg_deps(
        self,
        args: list[ContainerObject] | None,
        kwargs: dict[str, ContainerObject] | None,
    ) -> frozenset[ContainerKey]:
        """Return registered keys referenced by ``FromContainer`` items in *args*/*kwargs*."""
        deps: set[ContainerKey] = set()
        for item in args or []:
            if isinstance(item, FromContainer):
                deps.add(self._normalise_key(item.source_key))
        for item in (kwargs or {}).values():
            if isinstance(item, FromContainer):
                deps.add(self._normalise_key(item.source_key))
        return frozenset(deps)

    def _normalise_key(self, key: ContainerKey) -> ContainerKey:
        """
        Return *key* in the form it is stored in ``_registered``.

        When two registrations share the same key they are promoted to a group
        stored under ``lod_class[key]``.  This method returns the group key when
        one exists, otherwise the plain key.
        """
        group = self._lod[key]
        return group if group in self._registered else key
