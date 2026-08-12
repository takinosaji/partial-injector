"""Tests for optional dependency support.

An ``X | None`` (or ``Optional[X]`` / ``Union[X, None]``) parameter annotation
is treated as an *optional* dependency:

- when ``X`` is registered, it is resolved and injected as usual;
- when ``X`` is not registered — or its registration condition is not met —
  the parameter is left open, so a ``= None`` default makes it ``None``.

The container change is purely in resolution: the optional annotation is
unwrapped to its inner type ``X`` before the name/type/group lookups, so
``X | None`` resolves to whatever ``X`` would have resolved to.
"""

from typing import Optional, Union

from partial_injector.partial_container import Container


class _Service:
    def __init__(self, label: str = "svc") -> None:
        self.label = label


class _Unregistered:
    pass


def test_optional_dep_injected_when_registered_by_type():
    # Arrange — annotation is ``_Service | None``; dep registered by type.
    dep = _Service("injected")

    def step(*, svc: _Service | None = None) -> _Service | None:
        return svc

    container = Container()
    container.register_singleton(dep, key=_Service)
    container.register_singleton(step)
    container.build()

    # Act
    result = container.resolve(step)()

    # Assert — resolves through the union to the registered instance.
    assert result is dep


def test_optional_dep_is_none_when_type_not_registered():
    # Arrange — nothing registered for ``_Unregistered``.
    def step(*, svc: _Unregistered | None = None) -> _Unregistered | None:
        return svc

    container = Container()
    container.register_singleton(step)
    container.build()

    # Act
    result = container.resolve(step)()

    # Assert — left open, so the ``= None`` default applies.
    assert result is None


def test_optional_dep_is_none_when_condition_not_met():
    # Arrange — dep registered by type but its build condition is False.
    dep = _Service("conditional")

    def step(*, svc: _Service | None = None) -> _Service | None:
        return svc

    container = Container()
    container.register_singleton(dep, key=_Service, condition=lambda: False)
    container.register_singleton(step)
    container.build()

    # Act
    result = container.resolve(step)()

    # Assert — condition-blocked registration resolves to None.
    assert result is None


def test_optional_dep_supports_typing_optional_form():
    # Arrange — ``Optional[_Service]`` must behave like ``_Service | None``.
    dep = _Service("optional-form")

    def step(*, svc: Optional[_Service] = None) -> Optional[_Service]:  # noqa: UP045
        return svc

    container = Container()
    container.register_singleton(dep, key=_Service)
    container.register_singleton(step)
    container.build()

    # Act
    result = container.resolve(step)()

    # Assert
    assert result is dep


def test_optional_dep_supports_typing_union_form():
    # Arrange — ``Union[_Service, None]`` must behave like ``_Service | None``.
    dep = _Service("union-form")

    def step(*, svc: Union[_Service, None] = None) -> Union[_Service, None]:  # noqa: UP007
        return svc

    container = Container()
    container.register_singleton(dep, key=_Service)
    container.register_singleton(step)
    container.build()

    # Act
    result = container.resolve(step)()

    # Assert
    assert result is dep


def test_optional_list_dependency_resolves_group():
    # Arrange — ``list[_Service] | None`` resolves to the grouped registrations.
    a = _Service("a")
    b = _Service("b")

    def step(*, svcs: list[_Service] | None = None) -> list[_Service] | None:
        return svcs

    container = Container()
    container.register_singleton(a, key=_Service)
    container.register_singleton(b, key=_Service)
    container.register_singleton(step)
    container.build()

    # Act
    result = container.resolve(step)()

    # Assert — the optional list annotation still resolves the group.
    assert result is not None
    assert set(result) == {a, b}


def test_optional_dep_still_resolves_by_name():
    # Arrange — name-based match takes priority and is unaffected by the union.
    dep = _Service("by-name")

    def step(*, svc: _Service | None = None) -> _Service | None:
        return svc

    container = Container()
    container.register_singleton(dep, key="svc")  # string key = param name
    container.register_singleton(step)
    container.build()

    # Act
    result = container.resolve(step)()

    # Assert
    assert result is dep
