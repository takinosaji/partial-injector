"""
partial_container — the DI container and its public surface.

Public surface
--------------
- ``Container``       The DI container.
- ``FromContainer``   Descriptor for pulling values from the container.

Internal modules
----------------
_entries.py              Sealed BuiltEntry hierarchy and TransientContainer.
_algorithms.py           Pure stateless functions (topo sort, copy, key lookup …).
_dependency_analyser.py  Builds the dependency graph for topological ordering.
_function_wirer.py       Wires callables with registered dependencies.
"""

from collections.abc import Callable
from dataclasses import replace
from inspect import isfunction
from typing import Any, Generic, TypeVar

from partial_injector._models import (
    ContainerKey,
    ContainerObject,
    FromContainer,
    Registration,
    RegistrationType,
)
from partial_injector._entries import (
    BuiltEntry,
    GroupBuilt,
    SingletonBuilt,
    TransientBuilt,
    TransientContainer,
)
from partial_injector._algorithms import (
    _copy_object,
    _registration_category,
    _topological_sort,
)
from partial_injector._dependency_analyser import _DependencyAnalyser
from partial_injector._function_wirer import _FunctionWirer
from partial_injector.error_handling import PartialContainerError

# Re-export FromContainer so existing ``from partial_injector.partial_container import FromContainer``
# imports keep working.
__all__ = ["Container", "FromContainer"]


class Container:
    """
    Dependency injection container based on ``functools.partial``.

    Usage::

        container = Container()
        container.register_singleton(my_service, key=MyService)
        container.register_singleton_factory(make_other, key=OtherService)
        container.build()

        svc = container.resolve(MyService)

    **Registration**
    Register functions, instances, or factories with ``register_singleton``,
    ``register_transient``, ``register_singleton_factory``, or
    ``register_transient_factory``.

    **Building**
    ``build()`` performs a topological sort of all registered keys, detects
    circular dependencies (raising a clear error with the cycle path), and then
    builds each key in dependency order.  Registered callables have their
    parameter annotations matched against registered keys and are wrapped in
    ``functools.partial`` with those dependencies pre-filled by keyword.

    **Resolution**
    ``resolve(key)`` returns the wired object.

    **Multiple registrations under the same key**
    Registering two objects under the same key groups them; resolve as ``list[Key]``.

    All errors raise ``PartialContainerError``.
    """

    type RegistrationsDictValue = Registration | "Container.ListOfDependencies[Registration]"

    _T = TypeVar("_T")  # local TypeVar used only by ListOfDependencies

    class ListOfDependencies(Generic[_T]):
        """
        Groups multiple ``Registration`` objects that share the same key.

        Kept as an inner class so its fully-qualified name
        ``partial_injector.partial_container.Container.ListOfDependencies``
        appears in error messages.
        """

        def __init__(self, *args: Any) -> None:
            if len(args) == 0:
                self.registrations: list[Registration] = []
            elif len(args) == 1 and isinstance(args[0], list):
                self.registrations = args[0]
            else:
                self.registrations = list(args)

        def append(self, registration: Registration) -> None:
            self.registrations.append(registration)

        def extend(self, registrations: list[Registration]) -> None:
            self.registrations.extend(registrations)

    def __init__(self) -> None:
        self._registered: dict[ContainerKey, Container.RegistrationsDictValue] = {}
        self.__built: dict[ContainerKey, BuiltEntry] = {}
        self.__is_built = False
        self.__analyser = _DependencyAnalyser(self._registered, Container.ListOfDependencies)
        self.__wirer = _FunctionWirer(
            self._registered,
            Container.ListOfDependencies,
            self.__lookup_param_entry,
            self.__resolve_value,
        )

    def register_singleton(
        self,
        instance: ContainerObject,
        key: ContainerKey | None = None,
        inject_returns: bool = False,
        inject_items: bool = False,
        condition: Callable[..., bool] | None = None,
        condition_args: list[ContainerObject] | None = None,
        condition_kwargs: dict[str, ContainerObject] | None = None,
        throw_if_condition_not_satisfied: bool = False,
    ) -> None:
        """
        Register *instance* as a singleton.

        The same object (or wired callable) is returned on every ``resolve`` call.

        ``key`` — the lookup key used later with ``resolve``.  Defaults to
        *instance* itself, which works well for functions and types.

        ``inject_returns`` — when ``True`` and *instance* is a function that
        returns another function, the returned function is itself wired through
        the container before being handed back to the caller.

        ``inject_items`` — when ``True`` and *instance* is a list, each element
        is individually processed through the container's injection logic.

        ``condition`` / ``condition_args`` / ``condition_kwargs`` — optional
        callable evaluated at ``build()`` time.  When it returns ``False`` the
        registration is skipped.

        ``throw_if_condition_not_satisfied`` — when ``True`` a skipped condition
        raises ``PartialContainerError`` instead of silently omitting the entry.
        """
        self.__register(
            RegistrationType.SINGLETON, instance, key,
            None, None, inject_returns, inject_items,
            condition, condition_args, condition_kwargs,
            throw_if_condition_not_satisfied,
        )

    def register_transient(
        self,
        instance: ContainerObject,
        key: ContainerKey | None = None,
        inject_returns: bool = False,
        inject_items: bool = False,
        condition: Callable[..., bool] | None = None,
        condition_args: list[ContainerObject] | None = None,
        condition_kwargs: dict[str, ContainerObject] | None = None,
        throw_if_condition_not_satisfied: bool = False,
    ) -> None:
        """
        Register *instance* as a transient.

        A fresh copy is produced on every ``resolve`` call: functions are cloned
        via ``FunctionType`` reconstruction, all other objects via ``deepcopy``.

        ``condition`` is evaluated lazily at each ``resolve`` call (not at
        ``build()`` time), so the condition can depend on runtime state.

        See ``register_singleton`` for a description of the remaining parameters.
        """
        self.__register(
            RegistrationType.TRANSIENT, instance, key,
            None, None, inject_returns, inject_items,
            condition, condition_args, condition_kwargs,
            throw_if_condition_not_satisfied,
        )

    def register_singleton_factory(
        self,
        factory: Callable,
        key: ContainerKey | None = None,
        factory_args: list[ContainerObject] | None = None,
        factory_kwargs: dict[str, ContainerObject] | None = None,
        inject_returns: bool = False,
        condition: Callable[..., bool] | None = None,
        condition_args: list[ContainerObject] | None = None,
        condition_kwargs: dict[str, ContainerObject] | None = None,
        throw_if_condition_not_satisfied: bool = False,
    ) -> None:
        """
        Register *factory* as a singleton factory.

        *factory* is called once at ``build()`` time; its return value is cached
        and returned on every subsequent ``resolve`` call.

        ``factory_args`` / ``factory_kwargs`` — positional and keyword arguments
        passed to *factory*.  Items that are ``FromContainer`` descriptors are
        resolved from the container before the call.

        See ``register_singleton`` for a description of the remaining parameters.
        """
        self.__register(
            RegistrationType.SINGLETON_FACTORY, factory, key,
            factory_args, factory_kwargs, inject_returns, False,
            condition, condition_args, condition_kwargs,
            throw_if_condition_not_satisfied,
        )

    def register_transient_factory(
        self,
        factory: Callable,
        key: ContainerKey | None = None,
        factory_args: list[ContainerObject] | None = None,
        factory_kwargs: dict[str, ContainerObject] | None = None,
        inject_returns: bool = False,
        condition: Callable[..., bool] | None = None,
        condition_args: list[ContainerObject] | None = None,
        condition_kwargs: dict[str, ContainerObject] | None = None,
        throw_if_condition_not_satisfied: bool = False,
    ) -> None:
        """
        Register *factory* as a transient factory.

        *factory* is called on every ``resolve`` call, producing a fresh object
        each time.  ``condition`` is evaluated lazily at each ``resolve`` call.

        See ``register_singleton_factory`` for a description of the remaining
        parameters.
        """
        self.__register(
            RegistrationType.TRANSIENT_FACTORY, factory, key,
            factory_args, factory_kwargs, inject_returns, False,
            condition, condition_args, condition_kwargs,
            throw_if_condition_not_satisfied,
        )

    def __register(
        self,
        registration_type: RegistrationType,
        obj: ContainerObject,
        key: ContainerKey | None,
        factory_args: list[ContainerObject] | None,
        factory_kwargs: dict[str, ContainerObject] | None,
        inject_returns: bool,
        inject_items: bool,
        condition: Callable[..., bool] | None,
        condition_args: list[ContainerObject] | None,
        condition_kwargs: dict[str, ContainerObject] | None,
        throw_if_condition_not_satisfied: bool,
    ) -> None:
        """
        Common implementation for all ``register_*`` methods.

        When the same *key* is registered a second time, both registrations are
        promoted to a ``ListOfDependencies`` group stored under the group key
        ``ListOfDependencies[actual_key]``.  A third registration appends to the
        existing group.
        """
        if self.__is_built:
            raise PartialContainerError("Container already built")

        actual_key = key if key is not None else obj
        registration = Registration(
            type=registration_type,
            key=actual_key,
            obj=obj,
            factory_args=factory_args,
            factory_kwargs=factory_kwargs,
            inject_returns=inject_returns,
            inject_items=inject_items,
            condition=condition,
            condition_args=condition_args,
            condition_kwargs=condition_kwargs,
            throw_if_condition_not_satisfied=throw_if_condition_not_satisfied,
        )

        group_key = Container.ListOfDependencies[actual_key]
        if group_key in self._registered:
            self._registered[group_key].append(registration)
        elif actual_key in self._registered:
            group = Container.ListOfDependencies()
            group.append(self._registered[actual_key])
            group.append(registration)
            self._registered[group_key] = group
            del self._registered[actual_key]
        else:
            self._registered[actual_key] = registration

    def build(self) -> None:
        """
        Build all registered dependencies in topological order.

        Dependencies are always built before the things that depend on them.
        Circular dependencies are detected and reported with a descriptive path.
        """
        build_order = _topological_sort(self.__analyser.build_graph())
        for key in build_order:
            self.__ensure_built(key)
        self.__is_built = True

    def __ensure_built(
        self,
        registration_key: ContainerKey,
    ) -> tuple[ContainerKey | None, ContainerKey | None] | None:
        """
        Ensure *registration_key* is built and cached in ``__built``.

        Returns one of:
        - ``None`` — single registration whose condition was not met (no throw).
        - ``(item_key, None)`` — single registration built successfully.
        - ``(item_key_or_None, list_key)`` — group built.
        """
        if registration_key not in self._registered:
            raise PartialContainerError(
                f"The object with key {registration_key} is not registered"
            )

        multiple = isinstance(
            self._registered[registration_key], Container.ListOfDependencies
        )

        if multiple:
            item_key = registration_key.__args__[0]
            list_key = list[item_key]
            if item_key in self.__built or list_key in self.__built:
                return (
                    item_key if item_key in self.__built else None,
                    list_key if list_key in self.__built else None,
                )
        else:
            if registration_key in self.__built:
                return registration_key, None

        registrations: list[Registration] = (
            self._registered[registration_key].registrations
            if multiple
            else [self._registered[registration_key]]
        )

        built_pairs: list[tuple[Registration, Any]] = []
        for reg in registrations:
            if (
                reg.condition is not None
                and reg.type not in (RegistrationType.TRANSIENT, RegistrationType.TRANSIENT_FACTORY)
                and not self.__execute_with_injections(
                    reg.condition, reg.condition_args, reg.condition_kwargs
                )
            ):
                continue
            built_pairs.append((reg, self.__build_registration(reg)))

        if not built_pairs:
            if multiple:
                if any(r.throw_if_condition_not_satisfied for r in registrations):
                    raise PartialContainerError(
                        f"No objects with key {registration_key} were built because built "
                        f"conditions have not been met for any of the registrations."
                    )
                item_key = registration_key.__args__[0]
                list_key = list[item_key]
                self.__built[list_key] = GroupBuilt(registrations[0], [])
                return None, list_key
            else:
                if registrations[0].throw_if_condition_not_satisfied:
                    raise PartialContainerError(
                        f"No object with key {registration_key} was built because the "
                        f"built condition has not been met."
                    )
                return None

        def _wrap(reg: Registration, raw: Any) -> SingletonBuilt | TransientBuilt:
            return (
                TransientBuilt(reg, raw)
                if isinstance(raw, TransientContainer)
                else SingletonBuilt(reg, raw)
            )

        typed_items = [_wrap(reg, raw) for reg, raw in built_pairs]

        if multiple:
            item_key = registration_key.__args__[0]
            list_key = list[item_key]
            built_item_key: ContainerKey | None = None
            if len(typed_items) == 1:
                built_item_key = item_key
                self.__built[item_key] = typed_items[0]
            self.__built[list_key] = GroupBuilt(registrations[0], typed_items)
            return built_item_key, list_key
        else:
            self.__built[registration_key] = typed_items[0]
            return registration_key, None

    def __lookup_param_entry(
        self,
        reg_key: ContainerKey,
        param_is_list: bool,
    ) -> BuiltEntry | None:
        """
        Bridge from ``_FunctionWirer`` into the Container's build state.

        Ensures *reg_key* is built, resolves the correct dict key based on
        whether the parameter expects a scalar or a list, and returns the
        ``BuiltEntry`` — or ``None`` when condition-blocked or ambiguous.
        """
        built_result = self.__ensure_built(reg_key)
        if built_result is None:
            return None
        item_key, list_key = built_result
        resolved_key = list_key if (param_is_list and list_key is not None) else item_key
        if resolved_key is None or resolved_key not in self.__built:
            return None
        return self.__built[resolved_key]

    def __build_registration(self, reg: Registration) -> Any:
        """
        Build a single ``Registration`` into its runtime value or ``TransientContainer``.

        Dispatches on ``(registration_type, object_category)`` — all arms are
        explicit and exhaustiveness is visible at a glance.
        """
        category = _registration_category(reg.obj, reg.inject_items)
        match (reg.type, category):
            case (RegistrationType.SINGLETON, "from_container"):
                self.__ensure_built(reg.obj.source_key)
                return reg.obj(self.__resolve_value_by_key)

            case (RegistrationType.TRANSIENT, "from_container"):
                return TransientContainer(self.__execute_transient_from_container, reg)

            case (RegistrationType.SINGLETON, "function"):
                return self.__wirer.wire(reg.obj, reg.inject_returns)

            case (RegistrationType.TRANSIENT, "function"):
                return TransientContainer(self.__execute_transient_function, reg)

            case (RegistrationType.SINGLETON, "list"):
                return [
                    self.__build_registration(replace(reg, obj=item))
                    for item in reg.obj
                ]

            case (RegistrationType.TRANSIENT, "list"):
                return TransientContainer(self.__execute_transient_list_items, reg)

            case (RegistrationType.SINGLETON, "instance"):
                return reg.obj

            case (RegistrationType.TRANSIENT, "instance"):
                return TransientContainer(self.__execute_transient_instance, reg)

            case (RegistrationType.SINGLETON_FACTORY, _):
                return self.__execute_singleton_factory(reg)

            case (RegistrationType.TRANSIENT_FACTORY, _):
                return TransientContainer(self.__execute_transient_factory, reg)

            case _:
                raise PartialContainerError(
                    f"Unsupported registration type and configuration: {reg.type!r}"
                )

    def __execute_transient_from_container(self, reg: Registration) -> Any:
        """Resolve a ``FromContainer`` descriptor afresh on each transient call."""
        self.__ensure_built(reg.obj.source_key)
        return reg.obj(self.__resolve_value_by_key)

    def __execute_transient_function(self, reg: Registration) -> Any:
        """
        Produce a freshly cloned and wired callable for a transient function registration.

        The function is cloned via ``_copy_object`` so each resolution receives an
        independent copy with its own ``__dict__``, then wired with the current
        container state.
        """
        return self.__wirer.wire(_copy_object(reg.obj), reg.inject_returns)

    def __execute_transient_instance(self, reg: Registration) -> Any:
        """Produce a deep copy of the registered instance on each transient resolution."""
        return _copy_object(reg.obj)

    def __execute_transient_list_items(self, reg: Registration) -> Any:
        """
        Re-copy and re-build each item in the registered list on every transient resolution.

        Each element is cloned independently so mutations to one resolution cannot
        affect another.
        """
        return [
            self.__build_registration(replace(reg, obj=_copy_object(item)))
            for item in reg.obj
        ]

    def __execute_singleton_factory(self, reg: Registration) -> Any:
        """
        Call the registered factory once and return its result.

        ``FromContainer`` items in *factory_args* / *factory_kwargs* are resolved
        before the call.  If the result is itself a callable, it is wired through
        the container.
        """
        result = self.__execute_with_injections(
            reg.obj, reg.factory_args, reg.factory_kwargs
        )
        return self.__apply_factory_result(result, reg.inject_returns)

    def __execute_transient_factory(self, reg: Registration) -> Any:
        """
        Call the registered factory and return its result (called on every resolution).

        Identical to ``__execute_singleton_factory`` in structure; the difference
        is that the calling path triggers on every ``resolve`` rather than once at
        ``build()`` time.
        """
        result = self.__execute_with_injections(
            reg.obj, reg.factory_args, reg.factory_kwargs
        )
        return self.__apply_factory_result(result, reg.inject_returns)

    def __apply_factory_result(self, obj: Any, inject_returns: bool) -> Any:
        """Post-process a factory return value: wire it if it is a function."""
        if isfunction(obj):
            return self.__wirer.wire(obj, inject_returns)
        if isinstance(obj, FromContainer):
            raise PartialContainerError("Cannot build FromContainer object")
        return obj

    def __execute_with_injections(
        self,
        factory: Callable,
        args: list[ContainerObject] | None = None,
        kwargs: dict[str, ContainerObject] | None = None,
    ) -> Any:
        """Call *factory* with resolved args/kwargs (unwrapping ``FromContainer`` items)."""
        resolved_args   = self.__build_from_container_args(args)    if args   is not None else []
        resolved_kwargs = self.__build_from_container_kwargs(kwargs) if kwargs is not None else {}
        return factory(*resolved_args, **resolved_kwargs)

    def __unwrap_injectable(self, item: ContainerObject) -> Any:
        """
        Resolve *item* to its concrete value.

        Plain objects are returned as-is.  ``FromContainer`` descriptors are
        resolved via the container; if the resolved value is a list (i.e. the
        source key is a group), a ``PartialContainerError`` is raised because
        factory args must be scalar.
        """
        if not isinstance(item, FromContainer):
            return item
        self.__ensure_built(item.source_key)
        value = item(self.__resolve_value_by_key)
        if isinstance(value, list):
            raise PartialContainerError(
                f"Cannot resolve dependency from the list registered under key "
                f"{item.source_key} because more than one object is available under this key"
            )
        return value

    def __build_from_container_args(self, args: list[ContainerObject]) -> list[Any]:
        """Unwrap every item in *args*, resolving ``FromContainer`` descriptors."""
        return [self.__unwrap_injectable(item) for item in args]

    def __build_from_container_kwargs(
        self, kwargs: dict[str, ContainerObject]
    ) -> dict[str, Any]:
        """Unwrap every value in *kwargs*, resolving ``FromContainer`` descriptors."""
        return {k: self.__unwrap_injectable(v) for k, v in kwargs.items()}

    def __resolve_value_by_key(self, key: ContainerKey) -> Any:
        """Look up *key* in ``__built`` and delegate to ``__resolve_value``."""
        return self.__resolve_value(self.__built[key])

    def __resolve_value(self, entry: BuiltEntry) -> Any:
        """
        Materialise a ``BuiltEntry`` into its concrete value.

        - ``SingletonBuilt`` — returns the cached value directly.
        - ``TransientBuilt`` — evaluates the stored ``condition`` (if any) and
          calls the ``TransientContainer`` factory to produce a fresh value.
        - ``GroupBuilt`` — delegates to ``__resolve_list``.
        """
        match entry:
            case SingletonBuilt(value=v):
                return v

            case TransientBuilt(factory=tc, registration=reg):
                if reg.condition is not None and not self.__execute_with_injections(
                    reg.condition, reg.condition_args, reg.condition_kwargs
                ):
                    raise PartialContainerError(
                        f"No object with key {reg.key} was built because the built "
                        f"condition has not been met."
                    )
                return tc()

            case GroupBuilt(items=items, first_registration=first_reg):
                return self.__resolve_list(items, first_reg)

    def __resolve_list(
        self,
        items: list[SingletonBuilt | TransientBuilt],
        first_reg: Registration,
    ) -> list[Any]:
        """
        Resolve a group of built entries into a plain list.

        Transient items have their ``condition`` evaluated lazily at this point.
        Items whose condition is not met are silently omitted; if *all* items are
        omitted and at least one had ``throw_if_condition_not_satisfied=True``,
        a ``PartialContainerError`` is raised.
        """
        allowed: list[Any] = []
        any_throw = False

        for item in items:
            match item:
                case TransientBuilt(factory=tc, registration=reg):
                    if reg.condition is not None and not self.__execute_with_injections(
                        reg.condition, reg.condition_args, reg.condition_kwargs
                    ):
                        if reg.throw_if_condition_not_satisfied:
                            any_throw = True
                        continue
                    allowed.append(tc())
                case SingletonBuilt(value=v):
                    allowed.append(v)

        if not allowed and any_throw:
            raise PartialContainerError(
                f"No objects with key {first_reg.key} were built because built "
                f"conditions have not been met for any of the registrations at the moment "
                f"of resolution."
            )
        return allowed

    def resolve(self, key: ContainerKey) -> Any:
        """
        Return the built object registered under *key*.

        *key* can be any value used with ``register_*``: a type, a string, a
        ``TypeAlias``, or the function object itself.  To retrieve a group of
        multiple registrations, pass ``list[Key]``.

        Raises ``PartialContainerError`` when:
        - ``build()`` has not been called yet.
        - *key* was never registered.
        - *key* was registered but not built (e.g. condition not satisfied at
          build time for a singleton).
        """
        if not self.__is_built:
            raise PartialContainerError("Container not built")

        if (
            key not in self._registered
            and hasattr(key, "__args__")
            and Container.ListOfDependencies[key.__args__[0]] not in self._registered
        ):
            raise PartialContainerError(f"Object with key {key} not registered")

        if key not in self.__built and list[key] not in self.__built:
            raise PartialContainerError(f"Object with key {key} not built")

        return self.__resolve_value(self.__built[key])
