import inspect
from dataclasses import dataclass, replace
from enum import Enum
from functools import partial
from inspect import isfunction
from typing import Callable, Optional, Any, TypeVar, Generic, TypeAliasType

from .error_handling import PartialContainerException

type ContainerKey = str | type | TypeAliasType | Callable
type ContainerObject = Any | FromContainer

class Container: # TODO: Add validation and proper error handling
    """
    This is a dependency injection tool that was designed to work with functions for those, who employs techniques of FP.
    It has got such name because it uses and is primarily based on partial function capabilities of Python.
    """
    type BuiltDictValue = list[Any] | Any
    type RegistrationsDictValue = Container.Registration | Container.RegistrationContainer[Container.Registration]

    def __init__(self):
        self.__registered = dict[ContainerKey, Container.RegistrationsDictValue]()
        self.__built = dict[ContainerKey, Container.BuiltDictValue]()
        self.__is_built = False

    def register_instance(self,
                          instance: ContainerObject,
                          inject_returns: bool = False,
                          inject_items: bool = False,
                          key: Optional[ContainerKey] = None,
                          condition: Optional[Callable[[...], bool] | Callable[[], bool]] = None,
                          condition_args: Optional[list[ContainerObject]]=None,
                          condition_kwargs: Optional[dict[str, ContainerObject]]=None,
                          condition_ignore_not_satisfied: bool = False):
        return self.__register(Container.RegistrationType.INSTANCE,
                               instance,
                               inject_returns,
                               inject_items,
                               key, condition,
                               condition_args,
                               condition_kwargs,
                               condition_ignore_not_satisfied)

    def register_factory(self,
                         factory: Callable,
                         args: Optional[list[ContainerObject]]=None,
                         kwargs: Optional[dict[str, ContainerObject]]=None,
                         inject_returns: bool = False,
                         key: Optional[ContainerKey] = None,
                         condition: Optional[Callable[[...], bool] | Callable[[], bool]] = None,
                         condition_args: Optional[list[ContainerObject]]=None,
                         condition_kwargs: Optional[dict[str, ContainerObject]]=None,
                         condition_ignore_not_satisfied: bool = False):
        return self.__register(Container.RegistrationType.FACTORY,
                               factory,
                               inject_returns,
                               False,
                               key,
                               condition,
                               condition_args,
                               condition_kwargs,
                               condition_ignore_not_satisfied,
                               args,
                               kwargs)

    def __register(self,
                   registration_type: 'Container.RegistrationType',
                   registration_object: Callable,
                   inject_returns: bool = False,
                   inject_items: bool = False,
                   key: Optional[ContainerKey] = None,
                   condition: Optional[Callable[[...], bool] | Callable[[], bool]] = None,
                   condition_args: Optional[list[ContainerObject]]=None,
                   condition_kwargs: Optional[dict[str, ContainerObject]]=None,
                   condition_ignore_not_satisfied: bool = False,
                   factory_args: Optional[list[ContainerObject]]=None,
                   factory_kwargs: Optional[dict[str, ContainerObject]]=None):
        if self.__is_built:
            raise PartialContainerException("Container already built")

        actual_key = key if key is not None else registration_object

        registration = Container.Registration(registration_type,
                                              registration_object,
                                              factory_args=factory_args,
                                              factory_kwargs=factory_kwargs,
                                              inject_returns=inject_returns,
                                              inject_items=inject_items,
                                              condition=condition,
                                              condition_args=condition_args,
                                              condition_kwargs=condition_kwargs,
                                              condition_ignore_not_satisfied=condition_ignore_not_satisfied)

        if Container.RegistrationContainer[actual_key] in self.__registered and isinstance(self.__registered[Container.RegistrationContainer[actual_key]], Container.RegistrationContainer):
            self.__registered[Container.RegistrationContainer[actual_key]].append(registration)
        elif actual_key in self.__registered:
            container = Container.RegistrationContainer()
            container.registrations.append(self.__registered[actual_key])
            container.registrations.append(registration)
            self.__registered[Container.RegistrationContainer[actual_key]] = container
            del self.__registered[actual_key]
        else:
            self.__registered[actual_key] = registration
        return None

    def build(self) -> None:
        for key, registration in self.__registered.items():
            self.__build_dependency(key)
        self.__is_built = True

    def __build_dependency(self, registration_key: ContainerKey) -> None | tuple[ContainerKey | None, list[ContainerKey] | None]: # TODO: Add circular dependency tracking
        if registration_key not in self.__registered:
            raise PartialContainerException(f"The object with key {registration_key} is not registered")

        multiple_registrations = isinstance(self.__registered[registration_key], Container.RegistrationContainer)

        if multiple_registrations:
            already_built_item_key = registration_key.__args__[0] if registration_key.__args__[0] in self.__built else None
            already_built_list_key = list[already_built_item_key] if list[already_built_item_key] in self.__built else None

            if already_built_item_key or already_built_list_key:
                return already_built_item_key, already_built_list_key
        else:
            if registration_key in self.__built:
                return registration_key, None

        built_dependencies = []
        multiple_registrations = isinstance(self.__registered[registration_key], Container.RegistrationContainer)

        registrations = self.__registered[registration_key].registrations if multiple_registrations else [self.__registered[registration_key]]
        for registration in registrations:
            if registration.condition is not None:
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
                self.__built[built_item_key] = built_dependencies[0]

            built_list_key = list[registration_key.__args__[0]]
            self.__built[built_list_key] = built_dependencies

            return built_item_key, built_list_key
        else:
            self.__built[registration_key] = built_dependencies[0]
            return registration_key, None

    def __build_registration(self, registration: 'Container.Registration') -> list[BuiltDictValue]:
        match registration:
            case _ if registration.type == Container.RegistrationType.INSTANCE and isinstance(registration.obj,
                                                                                              FromContainer):
                self.__build_dependency(registration.obj.source_key)
                return [registration.obj(self.__built)]
            case _ if registration.type == Container.RegistrationType.INSTANCE \
                      and not isinstance(registration.obj, FromContainer) \
                      and isfunction(registration.obj):
                partial_func = self.__build_partial(registration.obj, registration.inject_returns)
                return [partial_func]
            case _ if registration.type == Container.RegistrationType.INSTANCE \
                      and isinstance(registration.obj, list) \
                      and registration.inject_items:
                injected_list = []
                for item in registration.obj:
                     injected_list.append(self.__build_registration(replace(registration, obj=item)))
                return injected_list
            case _ if registration.type == Container.RegistrationType.INSTANCE \
                      and not isinstance(registration.obj, FromContainer) \
                      and not isfunction(registration.obj):
                return [registration.obj]
            case _ if registration.type == Container.RegistrationType.FACTORY:
                obj = self.__execute_with_injections(registration.obj, registration.factory_args,
                                                     registration.factory_kwargs)
                match obj:
                    case _ if isfunction(obj):
                        partial_func = self.__build_partial(registration.obj, registration.inject_returns)
                        return [partial_func]
                    case _ if isinstance(obj, FromContainer):
                        raise PartialContainerException("Cannot build FromContainer object")
                    case _:
                        return [obj]
            case _:
                raise PartialContainerException("Unknown registration type")

    def __execute_with_injections(self, factory: Callable,
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

                    if isinstance(self.__built[item.source_key], list):
                        raise PartialContainerException(f"Cannot resolve dependency from the list of registered under key {item.source_key} because more than one object is available under this key")
                    unwrapped.append(self.__built[item.source_key])
                case _:
                    unwrapped.append(item)
        return unwrapped

    def __build_from_container_kwargs(self, obj: dict[str, ContainerObject]):
        unwrapped = {}
        for key, item in obj.items():
            match item:
                case _ if isinstance(item, FromContainer):
                    self.__build_dependency(item.source_key)

                    if isinstance(self.__built[item.source_key], list):
                        raise PartialContainerException(f"Cannot resolve dependency from the list of registered under key {item.source_key} because more than one object is available under this key")
                    unwrapped[key] = self.__built[item.source_key]
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
            reg_container_type = Container.RegistrationContainer[param.annotation.__args__[0]] if param.annotation and param_is_list \
                else Container.RegistrationContainer[param.annotation] if param.annotation \
                else None

            reg_dep_key = param_name if param_name in self.__registered \
                else param.annotation if param.annotation in self.__registered \
                else reg_container_type if reg_container_type in self.__registered \
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
                        partial_args.append(self.__built[built_dep_keys[1]])
                    else:
                        partial_args.append(self.__built[built_dep_keys[0]])
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

        if not key in self.__registered and hasattr(key, '__args__') \
                and Container.RegistrationContainer[key.__args__[0]] not in self.__registered:
            raise PartialContainerException(f"Object with key {key} not registered")

        if not key in self.__built and list[key] not in self.__built:
            raise PartialContainerException(f"Object with key {key} not built")

        return self.__built[key]

    class RegistrationType(Enum):
        INSTANCE = "INSTANCE"
        FACTORY = "FACTORY"

    @dataclass
    class Registration:
        type: 'Container.RegistrationType'
        obj: Any
        factory_args: Optional[list[Any]] = None
        factory_kwargs: Optional[dict[str, Any]] = None
        inject_returns: bool = False
        inject_items: bool = False
        condition: Optional[Callable[[...], bool]] = None,
        condition_args: Optional[list[ContainerObject]] = None
        condition_kwargs: Optional[dict[str, Any]] = None
        condition_ignore_not_satisfied: bool = False

    T = TypeVar('T')
    class RegistrationContainer(Generic[T]):
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
                return built[self.source_key]
            case _:
                return self.selector(built[self.source_key])
