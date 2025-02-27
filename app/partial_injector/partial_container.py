import inspect
from dataclasses import dataclass
from enum import Enum
from functools import partial
from inspect import isfunction
from typing import Callable, Optional, Any, TypeVar, Generic, TypeAliasType

from .error_handling import TerminationException

type ContainerKey = str | type | TypeAliasType | Callable
type ContainerObject = Any | FromContainer

class Container: # TODO: Add validation and proper error handling
    """
    This is a dependency injection tool that was designed to work with functions for those, who employs techniques of FP.
    It has got such name because it uses and is primarily based on partial function capabilities of Python.
    """

    def __init__(self):
        self.__registered = dict[ContainerKey, Container.Registration | Container.RegistrationContainer[Container.Registration]]()
        self.__built = dict[ContainerKey, Container.BuiltContainer[Any] | Any]()
        self.__is_built = False

    def register_instance(self,
                          obj: ContainerObject,
                          inject_returns: bool = False,
                          key: Optional[ContainerKey] = None,
                          condition: Optional[Callable[[...], bool]] = None,
                          condition_args: Optional[list[ContainerObject]]=None,
                          condition_kwargs: Optional[dict[str, ContainerObject]]=None):
        if self.__is_built:
            raise TerminationException("Container already built")

        actual_key = key if key is not None else obj

        registration = Container.Registration(Container.RegistrationType.INSTANCE,
                                              obj,
                                              inject_returns=inject_returns,
                                              condition=condition,
                                              condition_args=condition_args,
                                              condition_kwargs=condition_kwargs)

        if Container.RegistrationContainer[actual_key] in self.__registered and isinstance(self.__registered[Container.RegistrationContainer[actual_key]], Container.RegistrationContainer):
            self.__registered[Container.RegistrationContainer[actual_key]].append(registration)
        elif actual_key in self.__registered:
            container = Container.RegistrationContainer()
            container.registrations.append(self.__registered[actual_key])
            container.registrations.append(registration)
            self.__registered[Container.RegistrationContainer[actual_key]] = container
            del self.__registered[actual_key]
        else:
        #
        # if actual_key in self.__registered:
        #     container = Container.RegistrationContainer()
        #     if isinstance(self.__registered[actual_key], Container.RegistrationContainer):
        #         container.registrations.extend(self.__registered[actual_key].registrations)
        #     else:
        #         container.registrations.append(self.__registered[actual_key])
        #     container.registrations.append(registration)
        #     self.__registered[actual_key] = container
        #     return None

            self.__registered[actual_key] = registration
        return None

    def register_factory(self,
                         factory: Callable,
                         args: Optional[list[ContainerObject]]=None,
                         kwargs: Optional[dict[str, ContainerObject]]=None,
                         inject_returns: bool = False,
                         key: Optional[ContainerKey] = None,
                         condition: Optional[Callable[[...], bool]] = None,
                         condition_args: Optional[list[ContainerObject]]=None,
                         condition_kwargs: Optional[dict[str, ContainerObject]]=None):
        if self.__is_built:
            raise TerminationException("Container already built")

        actual_key = key if key is not None else factory

        registration = Container.Registration(Container.RegistrationType.FACTORY,
                                              factory,
                                              args=args,
                                              kwargs=kwargs,
                                              inject_returns=inject_returns,
                                              condition=condition,
                                              condition_args=condition_args,
                                              condition_kwargs=condition_kwargs)
        if actual_key in self.__registered:
            container = Container.RegistrationContainer()
            if isinstance(self.__registered[actual_key], Container.RegistrationContainer):
                container.extend(self.__registered[actual_key].registrations)
            else:
                container.append(self.__registered[actual_key])
            container.append(registration)
            self.__registered[actual_key] = container
            return None

        self.__registered[actual_key] = registration
        return None

    def build(self) -> None:
        for key, registration in self.__registered.items():
            self.__build_dependency(key)
        self.__is_built = True

    def __build_dependency(self, key) -> None: # TODO: Add circular dependency tracking
        if key not in self.__registered:
            raise TerminationException(f"The object with key {key} is not registered")

        if key in self.__built:
            return self.__built[key]

        container = Container.BuiltContainer()

        registrations = self.__registered[key].registrations if isinstance(self.__registered[key], Container.RegistrationContainer) else [self.__registered[key]]
        for registration in registrations:
            if registration.condition is not None:
                if not self.__execute_with_injections(registration.condition, registration.condition_args, registration.condition_kwargs):
                    continue

            match registration:
                case _ if registration.type == Container.RegistrationType.INSTANCE and isinstance(registration.obj, FromContainer):
                    self.__build_dependency(registration.obj.source_key)
                    container.append(registration.obj(self.__built))
                case _ if registration.type == Container.RegistrationType.INSTANCE and not isinstance(registration.obj, FromContainer) and isfunction(registration.obj):
                    partial_func = self.__build_partial(registration.obj, registration.inject_returns)
                    container.append(partial_func)
                case _ if registration.type == Container.RegistrationType.INSTANCE and not isinstance(registration.obj, FromContainer) and not isfunction(registration.obj):
                    container.append(registration.obj)
                case _ if registration.type == Container.RegistrationType.FACTORY:
                    obj = self.__execute_with_injections(registration.obj, registration.args, registration.kwargs)
                    match obj:
                        case _ if isfunction(obj):
                            partial_func = self.__build_partial(registration.obj, registration.inject_returns)
                            container.append(partial_func)
                        case _ if isinstance(obj, FromContainer):
                            raise TerminationException("Cannot build FromContainer object")
                        case _:
                            container.append(obj)
                case _:
                    raise TerminationException("Unknown registration type")

        built_key = list[key.__args__[0]] if hasattr(key, '__origin__') and key.__origin__ == Container.RegistrationContainer else key

        if len(container.built_dependencies) == 1:
            self.__built[built_key] = container.built_dependencies[0]
        elif len(container.built_dependencies) > 1:
            self.__built[built_key] = container

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
                    if item.source_key not in self.__built:
                        raise TerminationException(f"Object with key {item.source_key} was not built and cannot be resolved because built conditions have not been met.")
                    if isinstance(self.__built[item.source_key], Container.BuiltContainer):
                        raise TerminationException(f"Cannot resolve dependency from the list of registered under key {item.source_key} because more than one object is available under this key")
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
                    if item.source_key not in self.__built:
                        raise TerminationException(f"Object with key {item.source_key} was not built and cannot be resolved because built conditions have not been met.")
                    if isinstance(self.__built[item.source_key], Container.BuiltContainer):
                        raise TerminationException(f"Cannot resolve dependency from the list of registered under key {item.source_key} because more than one object is available under this key")
                    unwrapped[key] = self.__built[item.source_key]
                case _:
                    unwrapped[key] = item
        return unwrapped

    def __build_partial(self, func: Callable, inject_returns: bool) -> Callable:
        sig = inspect.signature(func)

        if len(sig.parameters) == 0:
            return self.__get_with_returns_injected(func) if inject_returns else func

        partial_args = []

        last_not_registered_param = None
        for param_name, param in sig.parameters.items():
            dep_key = param_name if param_name in self.__registered else param.annotation if param.annotation in self.__registered else None

            if not dep_key is None:
                if last_not_registered_param is not None:
                    raise TerminationException(f"Cannot build partial function without registered parameter {last_not_registered_param}:{param.annotation}")

                self.__build_dependency(dep_key)

                if dep_key not in self.__built:
                    raise TerminationException(f"Object with key {dep_key} was not built and cannot be resolved because built conditions have not been met.")

                # if isinstance(self.__built[dep_key], Container.BuiltContainer):
                #     raise TerminationException(f"Cannot resolve dependency from the list of registered under key {dep_key} because more than one object is available under this key")

                built_dependency = self.__built[dep_key]
                if isinstance(built_dependency, Container.BuiltContainer):
                    built_dependency = built_dependency.built_dependencies

                partial_args.append(built_dependency)
            else:
                last_not_registered_param = param_name

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
            raise TerminationException("Container not built")

        if not key in self.__registered and hasattr(key, '__args__') and Container.RegistrationContainer[key.__args__[0]] not in self.__registered:
            raise TerminationException(f"Object with key {key} not registered")

        if not key in self.__built and Container.BuiltContainer[key] not in self.__built:
            raise TerminationException(f"Object with key {key} not built")

        # if isinstance(self.__built[key], Container.BuiltContainer):
        #     return self.__built[key].built_dependencies

        return self.__built[key]

    class RegistrationType(Enum):
        INSTANCE = "INSTANCE"
        FACTORY = "FACTORY"

    @dataclass
    class Registration:
        type: 'Container.RegistrationType'
        obj: Any
        args: Optional[list[Any]] = None
        kwargs: Optional[dict[str, Any]] = None
        inject_returns: bool = False
        condition: Optional[Callable[[...], bool]] = None,
        condition_args: Optional[list[ContainerObject]] = None
        condition_kwargs: Optional[dict[str, Any]] = None

    T = TypeVar('T')
    class RegistrationContainer(Generic[T]):
        def __init__(self, *args):
            if len(args) == 0:
                self.registrations = []
                return
            self.registrations = args[0] if len(args) == 1 and isinstance(args[0], list) else args

        def extend(self, *args, **kwargs):
            self.registrations.append(args, kwargs)

        def append(self, registration):
            self.registrations.append(registration)

    class BuiltContainer(Generic[T]):
        def __init__(self, *args):
            if len(args) == 0:
                self.built_dependencies = []
                return
            self.built_dependencies = args[0] if len(args) == 1 and isinstance(args[0], list) else args

        def append(self, built_dependency):
            self.built_dependencies.append(built_dependency)

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