"""
_entries — sealed BuiltEntry hierarchy and TransientContainer.

These data types represent the three possible states of a built registration:

- ``SingletonBuilt``  — a fully materialised value, returned as-is on every resolve.
- ``TransientBuilt``  — a deferred entry; ``TransientContainer`` is called fresh
                        on each resolution to produce a new value.
- ``GroupBuilt``      — multiple registrations under the same key, resolved as a list.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from partial_injector._models import Registration

type BuiltEntry = "SingletonBuilt | TransientBuilt | GroupBuilt"


class TransientContainer:
    """
    Deferred callable that produces a fresh value on every invocation.

    ``factory`` is a bound method of ``Container`` accepting a ``Registration``
    and returning the resolved value.
    """

    __slots__ = ("_factory", "registration")

    def __init__(
        self,
        factory: Callable[[Registration], Any],
        registration: Registration,
    ) -> None:
        self._factory = factory
        self.registration = registration

    def __call__(self) -> Any:
        return self._factory(self.registration)


@dataclass
class SingletonBuilt:
    """A fully materialised singleton value."""

    registration: Registration
    value: Any


@dataclass
class TransientBuilt:
    """Deferred transient entry — a new value is produced on each resolution."""

    registration: Registration
    factory: TransientContainer


@dataclass
class GroupBuilt:
    """
    A group of entries registered under the same key.

    ``items`` holds one ``SingletonBuilt`` or ``TransientBuilt`` per registration
    that survived its condition check.  An empty list means every condition failed.
    """

    first_registration: Registration
    items: list[SingletonBuilt | TransientBuilt]
