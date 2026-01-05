import copy
import inspect
from dataclasses import dataclass, replace
from enum import Enum
from functools import partial
from inspect import isfunction
from typing import Callable, Optional, Any, TypeVar, Generic, TypeAliasType

from .error_handling import PartialContainerException

type ContainerKey = str | type | TypeAliasType | Callable
type ContainerObject = Any | FromContainer


class RegistrationType(Enum):
    SINGLETON = "SINGLLETON"
    TRANSIENT = "TRANSIENT"
    SINGLETON_FACTORY = "SINGLETON_FACTORY"
    TRANSIENT_FACTORY = "TRANSIENT_FACTORY"


class Container: # TODO: Add validation and proper error handling
    """
    This is a dependency injection tool that was designed to work with functions for those, who employs techniques of FP.
    It has got such name because it uses and is primarily based on partial function capabilities of Python.
    """
    type RegistrationsDictValue = Container.Registration | Container.ListOfDependencies[Container.Registration]

    class BuiltDictValue:
        def __init__(self,
                     first_registration: 'Container.Registration',
                     value: Any,
                     execute_with_injections: Callable[[Callable, Optional[list[ContainerObject]], Optional[dict[str, ContainerObject]]], Any]):
            self._value = value
            self._first_registration = first_registration
            self._execute_with_injections = execute_with_injections

        def __raise_no_objects_built_error(self, key: ContainerKey) -> None:
            raise PartialContainerException(
                f"No objects with key {key} were built because built conditions have not been met for any of the registrations at the moment of resolution.")

        @property
        def value(self) -> Any:
            match self._value:
                case _ if isinstance(self._value, Container.TransientContainer):
                    if (self._value.registration.condition is not None and
                        not self._execute_with_injections(self._first_registration.condition,
                                                          self._first_registration.condition_args,
                                                          self._first_registration.condition_kwargs)):
                        self.__raise_no_objects_built_error(self._first_registration.key)
                    return self._value()
                case _ if isinstance(self._value, list):
                    allowed_dependencies = []
                    for item in self._value:
                        if isinstance(item, Container.TransientContainer):
                            if (item.registration.condition is not None and
                                not self._execute_with_injections(item.registration.condition,
                                                                  item.registration.condition_args,
                                                                  item.registration.condition_kwargs)):
                                continue
                            allowed_dependencies.append(item())
                        else:
                            allowed_dependencies.append(item)

                    if len(allowed_dependencies) == 0:
                        self.__raise_no_objects_built_error(self._first_registration.key)

                    return allowed_dependencies
                case _:
                    return self._value

        @value.setter
        def value(self, value: Any) -> None:
            self._value = value

    class TransientContainer:
        def __init__(self,
                     transient_callable: Callable,
                     registration: 'Container.Registration'):
            self._transient_callable = transient_callable
            self.registration = registration

        def __call__(self):
            factory_result = self._transient_callable(self.registration)
            return factory_result

    def __init__(self):
        self._registered = dict[ContainerKey, Container.RegistrationsDictValue]()
        self._built = dict[ContainerKey, Container.BuiltDictValue]()
        self.__is_built = False

    def register_singleton(self,
                           instance: ContainerObject,
                           key: Optional[ContainerKey] = None,
                           inject_returns: bool = False,
                           inject_items: bool = False,
                           condition: Optional[Callable[[...], bool] | Callable[[], bool]] = None,
                           condition_args: Optional[list[ContainerObject]]=None,
                           condition_kwargs: Optional[dict[str, ContainerObject]]=None,
                           condition_ignore_not_satisfied: bool = False):
        return self.__register(RegistrationType.SINGLETON,
                               instance,
                               key,
                               None,
                               None,
                               inject_returns,
                               inject_items,
                               condition,
                               condition_args,
                               condition_kwargs,
                               condition_ignore_not_satisfied)

    def register_transient(self,
                           instance: ContainerObject,
                           key: Optional[ContainerKey] = None,
                           inject_returns: bool = False,
                           inject_items: bool = False,
                           condition: Optional[Callable[[...], bool] | Callable[[], bool]] = None,
                           condition_args: Optional[list[ContainerObject]]=None,
                           condition_kwargs: Optional[dict[str, ContainerObject]]=None,
                           condition_ignore_not_satisfied: bool = False):
        return self.__register(RegistrationType.TRANSIENT,
                               instance,
                               key,
                               None,
                               None,
                               inject_returns,
                               inject_items,
                               condition,
                               condition_args,
                               condition_kwargs,
                               condition_ignore_not_satisfied)


    def register_singleton_factory(self,
                                   factory: Callable,
                                   key: Optional[ContainerKey] = None,
                                   factory_args: Optional[list[ContainerObject]]=None,
                                   factory_kwargs: Optional[dict[str, ContainerObject]]=None,
                                   inject_returns: bool = False,
                                   condition: Optional[Callable[[...], bool] | Callable[[], bool]] = None,
                                   condition_args: Optional[list[ContainerObject]]=None,
                                   condition_kwargs: Optional[dict[str, ContainerObject]]=None,
                                   condition_ignore_not_satisfied: bool = False):
        return self.__register(RegistrationType.SINGLETON_FACTORY,
                               factory,
                               key,
                               factory_args,
                               factory_kwargs,
                               inject_returns,
                               False,
                               condition,
                               condition_args,
                               condition_kwargs,
                               condition_ignore_not_satisfied)

    def register_transient_factory(self,
                                   factory: Callable,
                                   key: Optional[ContainerKey] = None,
                                   factory_args: Optional[list[ContainerObject]]=None,
                                   factory_kwargs: Optional[dict[str, ContainerObject]]=None,
                                   inject_returns: bool = False,
                                   condition: Optional[Callable[[...], bool] | Callable[[], bool]] = None,
                                   condition_args: Optional[list[ContainerObject]]=None,
                                   condition_kwargs: Optional[dict[str, ContainerObject]]=None,
                                   condition_ignore_not_satisfied: bool = False):
        return self.__register(RegistrationType.TRANSIENT_FACTORY,
                               factory,
                               key,
                               factory_args,
                               factory_kwargs,
                               inject_returns,
                               False,
                               condition,
                               condition_args,
                               condition_kwargs,
                               condition_ignore_not_satisfied)

    def __register(self,
                   registration_type: 'RegistrationType',
                   registration_object: Callable,
                   key: Optional[ContainerKey] = None,
                   factory_args: Optional[list[ContainerObject]]=None,
                   factory_kwargs: Optional[dict[str, ContainerObject]]=None,
                   inject_returns: bool = False,
                   inject_items: bool = False,
                   condition: Optional[Callable[[...], bool] | Callable[[], bool]] = None,
                   condition_args: Optional[list[ContainerObject]]=None,
                   condition_kwargs: Optional[dict[str, ContainerObject]]=None,
                   condition_ignore_not_satisfied: bool = False):
        if self.__is_built:
            raise PartialContainerException("Container already built")

        actual_key = key if key is not None else registration_object

        registration = Container.Registration(registration_type,
                                              actual_key,
                                              registration_object,
                                              factory_args=factory_args,
                                              factory_kwargs=factory_kwargs,
                                              inject_returns=inject_returns,
                                              inject_items=inject_items,
                                              condition=condition,
                                              condition_args=condition_args,
                                              condition_kwargs=condition_kwargs,
                                              condition_ignore_not_satisfied=condition_ignore_not_satisfied)
        if Container.ListOfDependencies[actual_key] in self._registered and isinstance(self._registered[Container.ListOfDependencies[actual_key]], Container.ListOfDependencies):
            self._registered[Container.ListOfDependencies[actual_key]].append(registration)
        elif actual_key in self._registered:
            container = Container.ListOfDependencies()
            container.registrations.append(self._registered[actual_key])
            container.registrations.append(registration)
            self._registered[Container.ListOfDependencies[actual_key]] = container
            del self._registered[actual_key]
        else:
            self._registered[actual_key] = registration
        return None

    def build(self) -> None:
        for key, registration in self._registered.items():
            self.__build_dependency(key)
        self.__is_built = True

    def __create_build_dict_value(self,
                                  registration: 'Container.Registration',
                                  value: Any):
        return Container.BuiltDictValue(registration, value, self.__execute_with_injections)

    def __build_dependency(self, registration_key: ContainerKey) -> None | tuple[ContainerKey | None, list[ContainerKey] | None]: # TODO: Add circular dependency tracking
        if registration_key not in self._registered:
            raise PartialContainerException(f"The object with key {registration_key} is not registered")

        built_dependencies = []
        multiple_registrations = isinstance(self._registered[registration_key], Container.ListOfDependencies)

        if multiple_registrations:
            already_built_item_key = registration_key.__args__[0] if registration_key.__args__[0] in self._built else None
            already_built_list_key = list[already_built_item_key] if list[already_built_item_key] in self._built else None

            if already_built_item_key or already_built_list_key:
                return already_built_item_key, already_built_list_key
        else:
            if registration_key in self._built:
                return registration_key, None

        registrations = self._registered[registration_key].registrations if multiple_registrations else [self._registered[registration_key]]
        for registration in registrations:
            if registration.condition is not None and registration.type is not RegistrationType.TRANSIENT_FACTORY:
                if not self.__execute_with_injections(registration.condition, registration.condition_args, registration.condition_kwargs):
                    continue
            built_dependencies.extend(self.__build_registration(registration))

        if len(built_dependencies) == 0 and any(not r.condition_ignore_not_satisfied for r in registrations):
            raise PartialContainerException(f"No objects with key {registration_key} were built because built conditions have not been met for any of the registrations.")
        elif len(built_dependencies) == 0:
            return None

        if multiple_registrations:
            built_item_key = None
            if len(built_dependencies) == 1:
                built_item_key = registration_key.__args__[0]
                self._built[built_item_key] = self.__create_build_dict_value(registration, built_dependencies[0])

            built_list_key = list[registration_key.__args__[0]]
            self._built[built_list_key] = self.__create_build_dict_value(registration, built_dependencies)

            return built_item_key, built_list_key
        else:
            self._built[registration_key] = self.__create_build_dict_value(registration, built_dependencies[0])
            return registration_key, None

    def __build_registration(self, registration: 'Container.Registration') -> list[Container.BuiltDictValue]:
        match registration:
            case _ if registration.type == RegistrationType.SINGLETON and isinstance(registration.obj,
                                                                                               FromContainer):
                self.__build_dependency(registration.obj.source_key)
                return [registration.obj(self._built)]
            case _ if registration.type == RegistrationType.SINGLETON \
                      and not isinstance(registration.obj, FromContainer) \
                      and isfunction(registration.obj):
                partial_func = self.__build_partial(registration.obj, registration.inject_returns)
                return [partial_func]
            case _ if registration.type == RegistrationType.TRANSIENT \
                      and not isinstance(registration.obj, FromContainer) \
                      and isfunction(registration.obj):
                transient_container = Container.TransientContainer(self.__execute_transient_factory, registration)
                return [transient_container]
            case _ if registration.type == RegistrationType.SINGLETON \
                      and isinstance(registration.obj, list) \
                      and registration.inject_items:
                injected_list = []
                for item in registration.obj:
                     injected_list.append(self.__build_registration(replace(registration, obj=item)))
                return injected_list
            case _ if registration.type == RegistrationType.SINGLETON \
                      and not isinstance(registration.obj, FromContainer) \
                      and not isfunction(registration.obj):
                return [registration.obj]
            case _ if (registration.type == RegistrationType.TRANSIENT
                       and not isinstance(registration.obj, FromContainer)
                       and not isfunction(registration.obj)):
                transient_container = Container.TransientContainer(self.__execute_transient_factory, registration)
                return [transient_container]
            case _ if registration.type == RegistrationType.SINGLETON_FACTORY:
                return [self.__execute_singleton_factory(registration)]
            case _ if registration.type == RegistrationType.TRANSIENT_FACTORY:
                transient_container = Container.TransientContainer(self.__execute_transient_factory, registration)
                return [transient_container]
            case _:
                raise PartialContainerException("Unsupported registration type and configuration")

    def __execute_singleton_factory(self, registration: 'Container.Registration') -> Any:
        obj = self.__execute_with_injections(registration.obj,
                                             registration.factory_args,
                                             registration.factory_kwargs)
        match obj:
            case _ if isfunction(obj):
                partial_func = self.__build_partial(obj, registration.inject_returns)
                return partial_func
            case _ if isinstance(obj, FromContainer):
                raise PartialContainerException("Cannot build FromContainer object")
            case _:
                return obj

    def __execute_transient_factory(self, registration: 'Container.Registration') -> Any:
        match registration.obj:
            case _ if isfunction(registration.obj):
                obj = self.__execute_with_injections(registration.obj,
                                                     registration.factory_args,
                                                     registration.factory_kwargs)
                match obj:
                    case _ if isfunction(obj):
                        partial_func = self.__build_partial(copy.copy(obj), registration.inject_returns)
                        return partial_func
                    case _ if isinstance(obj, FromContainer):
                        raise PartialContainerException("Cannot build FromContainer object")
                    case _:
                        return copy.deepcopy(obj)
            case _:
                return copy.deepcopy(registration.obj)

    def __execute_with_injections(self,
                                  factory: Callable,
                                  args: Optional[list[ContainerObject]]=None,
                                  kwargs: Optional[dict[str, ContainerObject]]=None) -> Any:
        match factory:
            case _ if args is not None and kwargs is not None:
                return factory(*self.__build_from_container_args(args), **self.__build_from_container_kwargs(kwargs))
            case _ if args is not None and kwargs is None:
                return factory(*self.__build_from_container_args(args))
            case _ if args is None and kwargs is not None:
                return factory(**self.__build_from_container_kwargs(kwargs))
            case _:
                return factory()

    def __build_from_container_args(self, obj: list[ContainerObject]):
        unwrapped = []
        for item in obj:
            match item:
                case _ if isinstance(item, FromContainer):
                    self.__build_dependency(item.source_key)

                    if isinstance(self._built[item.source_key].value, list):
                        raise PartialContainerException(f"Cannot resolve dependency from the list of registered under key {item.source_key} because more than one object is available under this key")
                    unwrapped.append(self._built[item.source_key].value)
                case _:
                    unwrapped.append(item)
        return unwrapped

    def __build_from_container_kwargs(self, obj: dict[str, ContainerObject]):
        unwrapped = {}
        for key, item in obj.items():
            match item:
                case _ if isinstance(item, FromContainer):
                    self.__build_dependency(item.source_key)

                    if isinstance(self._built[item.source_key].value, list):
                        raise PartialContainerException(f"Cannot resolve dependency from the list of registered under key {item.source_key} because more than one object is available under this key")
                    unwrapped[key] = self._built[item.source_key].value
                case _:
                    unwrapped[key] = item
        return unwrapped

    def __build_partial(self, func: Callable, inject_returns: bool) -> Callable:
        sig = inspect.signature(func)

        if len(sig.parameters) == 0:
            return self.__get_with_returns_injected(func) if inject_returns else func

        partial_args = []

        last_not_registered_name = None
        last_not_registered_annotation = None
        for param_name, param in sig.parameters.items():
            param_is_list = hasattr(param.annotation, '__origin__') and param.annotation.__origin__ is list
            reg_container_type = Container.ListOfDependencies[param.annotation.__args__[0]] if param.annotation and param_is_list \
                else Container.ListOfDependencies[param.annotation] if param.annotation \
                else None

            reg_dep_key = param_name if param_name in self._registered \
                else param.annotation if param.annotation in self._registered \
                else reg_container_type if reg_container_type in self._registered \
                else None

            registered_multiple_times = reg_container_type == reg_dep_key

            if not reg_dep_key is None:
                if last_not_registered_name is not None:
                    raise PartialContainerException(f"Cannot build partial function without registered parameter {last_not_registered_name}:{last_not_registered_annotation}")

                built_dep_keys = self.__build_dependency(reg_dep_key)

                if built_dep_keys is None:
                    last_not_registered_name = param_name
                    last_not_registered_annotation = param.annotation
                else:
                    if param_is_list and registered_multiple_times:
                        partial_args.append(self._built[built_dep_keys[1]].value)
                    else:
                        partial_args.append(self._built[built_dep_keys[0]].value)
            else:
                last_not_registered_name = param_name
                last_not_registered_annotation = param.annotation

        if len(partial_args) == 0:
            return self.__get_with_returns_injected(func) if inject_returns else func

        partial_func = partial(func, *partial_args)
        return self.__get_with_returns_injected(partial_func) if inject_returns else partial_func

    def __get_with_returns_injected(self, func):
        if inspect.iscoroutinefunction(func):
            async def async_func_with_injected_returns(*args, **kwargs):
                result = await func(*args, **kwargs)
                if isfunction(result):
                    return self.__build_partial(result, True)
                return result
            return async_func_with_injected_returns

        def func_with_injected_returns(*args, **kwargs):
            result = func(*args, **kwargs)
            if isfunction(result):
                return self.__build_partial(result, True)
            return result
        return func_with_injected_returns

    def resolve(self, key: ContainerKey):
        if not self.__is_built:
            raise PartialContainerException("Container not built")

        if not key in self._registered and hasattr(key, '__args__') \
                and Container.ListOfDependencies[key.__args__[0]] not in self._registered:
            raise PartialContainerException(f"Object with key {key} not registered")

        if not key in self._built and list[key] not in self._built:
            raise PartialContainerException(f"Object with key {key} not built")

        return self._built[key].value

    @dataclass
    class Registration:
        type: 'RegistrationType'
        key: ContainerKey
        obj: ContainerObject
        factory_args: Optional[list[Any]] = None
        factory_kwargs: Optional[dict[str, Any]] = None
        inject_returns: bool = False
        inject_items: bool = False
        condition: Optional[Callable[[...], bool]] = None,
        condition_args: Optional[list[ContainerObject]] = None
        condition_kwargs: Optional[dict[str, Any]] = None
        condition_ignore_not_satisfied: bool = False

    T = TypeVar('T')
    class ListOfDependencies(Generic[T]):
        def __init__(self, *args):
            if len(args) == 0:
                self.registrations = []
                return
            self.registrations = args[0] if len(args) == 1 and isinstance(args[0], list) else args

        def extend(self, registrations):
            self.registrations.extend(registrations)

        def append(self, registration):
            self.registrations.append(registration)

TDependencyKey = TypeVar('TDependencyKey', bound=ContainerKey)
@dataclass
class FromContainer(Generic[TDependencyKey]):
    source_key: TDependencyKey
    selector: Optional[Callable[[TDependencyKey], Any]] = None

    def __call__(self, built: dict[TDependencyKey, Any]) -> Any:
        match self.selector:
            case None:
                return built[self.source_key].value
            case _:
                return self.selector(built[self.source_key].value)
