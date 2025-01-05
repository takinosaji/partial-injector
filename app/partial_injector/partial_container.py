import inspect
from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import Callable, Optional, Any, TypeVar, Generic
from typing_extensions import TypeAliasType

from .error_handling import DoNotCatchThisException

type ContainerKey = str | type | TypeAliasType | Callable
type ContainerObject = Any | FromContainer

class Container: # TODO: Add validation and proper error handling
    """
    This is a dependency injection tool that was designed to work with functions for those, who employs techniques of FP.
    It has got such name because it uses and is primarily based on partial function capabilities of Python.
    """

    def __init__(self):
        self.__registered = dict[ContainerKey, Container.Registration]()
        self.__built = dict[ContainerKey, Any]()
        self.__is_built = False

    def register_instance(self, obj: ContainerObject, inject_returns: bool = False, key: Optional[ContainerKey] = None):
        if self.__is_built:
            raise Exception("Container already built")

        actual_key = key if key is not None else obj

        if actual_key in self.__registered:
            raise Exception(f"The object with key {actual_key} already registered")

        self.__registered[actual_key] = Container.Registration(Container.RegistrationType.INSTANCE, obj, inject_returns=inject_returns)

    def register_factory(self,
                         factory: Callable,
                         args: Optional[list[ContainerObject]]=None,
                         kwargs: Optional[dict[str, ContainerObject]]=None,
                         inject_returns: bool = False,
                         key: Optional[ContainerKey] = None):
        if self.__is_built:
            raise Exception("Container already built")

        actual_key = key if key is not None else factory

        if actual_key in self.__registered:
            raise Exception(f"The object with key {actual_key} already registered")

        self.__registered[actual_key] = Container.Registration(Container.RegistrationType.FACTORY,
                                                               factory, args=args, kwargs=kwargs, inject_returns=inject_returns)

    def build(self) -> None:
        for key, registration in self.__registered.items():
            self.__build_dependency(key)
        self.__is_built = True

    def resolve(self, key: ContainerKey):
        if not self.__is_built:
            raise Exception("Container not built")

        if not key in self.__registered:
            raise Exception(f"Object with key {key} not registered")

        if not key in self.__built:
            raise Exception(f"Object with key {key} not built")

        return self.__built[key]

    def __build_dependency(self, key) -> None: # TODO: Add circular depndency tracking
        if key not in self.__registered:
            raise Exception(f"The object with key {key} is not registered")

        if key in self.__built:
            return self.__built[key]

        registration = self.__registered[key]

        match key:
            case _ if registration.type == Container.RegistrationType.INSTANCE and isinstance(registration.obj, FromContainer):
                self.__build_dependency(registration.obj.source_key)
                self.__built[key] = registration.obj(self.__built)
            case _ if registration.type == Container.RegistrationType.INSTANCE and not isinstance(registration.obj, FromContainer) and callable(registration.obj):
                partial_func = self.__build_partial(registration.obj, registration.inject_returns)
                self.__built[key] = partial_func
            case _ if registration.type == Container.RegistrationType.INSTANCE and not isinstance(registration.obj, FromContainer) and not callable(registration.obj):
                self.__built[key] = registration
            case _ if registration.type == Container.RegistrationType.FACTORY:
                obj = self.__execute_factory(registration.obj, registration.args, registration.kwargs)
                match obj:
                    case _ if callable(obj):
                        partial_func = self.__build_partial(registration.obj, registration.inject_returns)
                        self.__built[key] = partial_func
                    case _ if isinstance(obj, FromContainer):
                        raise Exception("Cannot build FromContainer object")
                    case _:
                        self.__built[key] = obj

    def __execute_factory(self, factory: Callable,
                          args: Optional[list[ContainerObject]]=None,
                          kwargs: Optional[dict[str, ContainerObject]]=None):
        match factory:
            case _ if args is not None and kwargs is not None:
                return factory(*args, **kwargs)
            case _ if args is not None and kwargs is None:
                return factory(*self.__build_from_container_args(args))
            case _ if args is None and kwargs is not None:
                return factory(**kwargs)
            case _:
                return factory()

    def __build_from_container_args(self, obj: list[ContainerObject]):
        unwrapped = []
        for item in obj:
            match item:
                case _ if isinstance(item, FromContainer):
                    self.__build_dependency(item.source_key)
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
                    raise DoNotCatchThisException(f"Cannot build partial function without registered parameter {last_not_registered_param}")
                self.__build_dependency(dep_key)
                partial_args.append(self.__built[dep_key])
            else:
                last_not_registered_param = param_name

        if len(partial_args) == 0:
            return self.__get_with_returns_injected(func) if inject_returns else func

        partial_func = partial(func, *partial_args)
        return self.__get_with_returns_injected(partial_func) if inject_returns else partial_func

    def __compose_and_build_partial(self, func: Callable, inject_returns: bool) -> Callable:
        sig = inspect.signature(func)

        if len(sig.parameters) == 0:
            return self.__get_with_returns_injected(func) if inject_returns else func

        partial_args = []

        last_not_registered_param = None
        for param_name, param in sig.parameters.items():
            dep_key = param_name if param_name in self.__built else param.annotation if param.annotation in self.__built else None

            if not dep_key is None:
                if last_not_registered_param is not None:
                    raise DoNotCatchThisException(f"Cannot build partial function without registered parameter {last_not_registered_param}")
                self.__build_dependency(dep_key)
                partial_args.append(self.__built[dep_key])
            else:
                last_not_registered_param = param_name

        if len(partial_args) == 0:
            return self.__get_with_returns_injected(func) if inject_returns else func

        partial_func = partial(func, *partial_args)
        return self.__get_with_returns_injected(partial_func) if inject_returns else partial_func

    def __get_with_returns_injected(self, func):
        def func_with_injected_returns(*args, **kwargs):
            result = func(*args, **kwargs)
            if callable(result):
                return self.__compose_and_build_partial(result, True)
            return result
        return func_with_injected_returns

    class RegistrationType(Enum):
        INSTANCE = 1
        FACTORY = 2

    @dataclass
    class Registration:
        type: 'Container.RegistrationType'
        obj: Any
        args: Optional[list[Any]] = None
        kwargs: Optional[dict[str, Any]] = None
        inject_returns: bool = False

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