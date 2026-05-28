"""
Shared data-types for partial_injector.

Keeping these in a separate module avoids circular imports and makes the
types reusable without importing the full Container machinery.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeAliasType, TypeVar

type ContainerKey = str | type | TypeAliasType | Callable
type ContainerObject = Any  # May be a FromContainer instance.


class RegistrationType(Enum):
    SINGLETON = "SINGLETON"
    TRANSIENT = "TRANSIENT"
    SINGLETON_FACTORY = "SINGLETON_FACTORY"
    TRANSIENT_FACTORY = "TRANSIENT_FACTORY"


T = TypeVar("T")
TDependencyKey = TypeVar("TDependencyKey", bound="ContainerKey")


@dataclass
class Registration:
    """Holds every parameter supplied at registration time."""

    type: RegistrationType
    key: ContainerKey
    obj: ContainerObject
    factory_args: list[Any] | None = None
    factory_kwargs: dict[str, Any] | None = None
    inject_returns: bool = False
    inject_items: bool = False
    condition: Callable[..., bool] | None = None
    condition_args: list[ContainerObject] | None = None
    condition_kwargs: dict[str, Any] | None = None
    throw_if_condition_not_satisfied: bool = False


@dataclass
class FromContainer[TDependencyKey: "ContainerKey"]:
    """
    Descriptor for pulling a resolved value from the container.

    Use as a registration value or as a ``factory_args`` / ``factory_kwargs`` element.
    ``selector`` is applied to the resolved value when provided.

    Example::

        container.register_singleton(
            FromContainer(Configuration, lambda cfg: cfg.section),
            key=ConfigurationSection,
        )
    """

    source_key: TDependencyKey
    selector: Callable[[Any], Any] | None = None

    def __call__(self, resolver: Callable[[ContainerKey], Any]) -> Any:
        """
        Resolve ``source_key`` via *resolver*, then apply ``selector`` if present.

        *resolver* is a container-supplied callable with signature
        ``resolver(key: ContainerKey) -> Any``.
        """
        value = resolver(self.source_key)
        return self.selector(value) if self.selector is not None else value
