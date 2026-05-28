import re

import pytest

from partial_injector.error_handling import PartialContainerError
from partial_injector.partial_container import Container, FromContainer


class NumberContainer:
    def __init__(self):
        self.value = 0

    def increment(self) -> int:
        self.value += 1
        return self.value


def test_transient_registration_returns_new_instance_each_time():
    # Arrange
    container = Container()

    container.register_transient(NumberContainer(), key=NumberContainer)
    container.build()

    # Act
    first = container.resolve(NumberContainer)
    second = container.resolve(NumberContainer)

    # Assert
    assert isinstance(first, NumberContainer)
    assert isinstance(second, NumberContainer)
    assert first is not second


def test_transient_registration_instances_do_not_share_state():
    # Arrange
    container = Container()

    container.register_transient(NumberContainer(), key=NumberContainer)
    container.build()

    # Act
    first = container.resolve(NumberContainer)
    first.increment()

    second = container.resolve(NumberContainer)

    # Assert
    assert first.value == 1
    assert second.value == 0


def _return_shared_number_container(shared: NumberContainer) -> NumberContainer:
    return shared


def test_transient_function_references_are_different():
    # Arrange
    container = Container()
    shared_number_container = NumberContainer()

    def number_container_returner() -> NumberContainer:
        return shared_number_container

    container.register_transient(number_container_returner)
    container.build()

    # Act
    first_number_container_returner = container.resolve(number_container_returner)
    second_number_container_returner = container.resolve(number_container_returner)

    # Assert
    assert first_number_container_returner is not second_number_container_returner
    assert first_number_container_returner() is second_number_container_returner()


def test_transient_with_from_container_resolution():
    # Arrange
    container = Container()
    container.register_singleton(42, key=int)
    container.register_transient(
        FromContainer(int, lambda value: f"str: {value + 1}"), key=str
    )
    container.build()

    # Act
    result1 = container.resolve(str)

    # Assert
    assert result1 == "str: 43"


def test_transient_instance_injected_into_singleton_gets_fresh_copy_each_call():
    # Arrange
    # A transient *instance* (registered via register_transient, not a factory) is
    # injected into a singleton function.  Each call to the singleton must receive
    # an independent deepcopy of the original — not the same frozen object that was
    # baked in at build() time (the "captive dependency" anti-pattern).
    container = Container()

    def receive_dep(dep: NumberContainer) -> NumberContainer:
        return dep

    container.register_transient(NumberContainer(), key=NumberContainer)
    container.register_singleton(receive_dep)
    container.build()

    # Act
    first = container.resolve(receive_dep)()
    second = container.resolve(receive_dep)()

    # Assert
    assert first is not second  # distinct copies, not the same object
    first.increment()
    assert second.value == 0  # mutations on one copy do not affect the other


def test_transient_function_injected_into_singleton_gets_fresh_copy_each_call():
    # Arrange
    # A transient *function* (registered via register_transient) is injected into a
    # singleton function.  Each call to the singleton must receive a fresh function
    # object (a new FunctionType clone), not the same instance frozen at build() time.
    container = Container()
    shared = NumberContainer()

    def counter() -> int:
        return shared.increment()

    def receive_counter(counter):
        return counter  # return the injected function so we can inspect it

    # Register with a string key so the parameter name "counter" is matched directly.
    container.register_transient(counter, key="counter")
    container.register_singleton(receive_counter)
    container.build()

    # Act — each call to the singleton injects a fresh clone of counter
    first_counter = container.resolve(receive_counter)()
    second_counter = container.resolve(receive_counter)()

    # Assert
    assert (
        first_counter is not second_counter
    )  # distinct function objects (fresh clones)
    assert callable(first_counter)
    assert callable(second_counter)
    assert first_counter() == 1  # both clones share the closure → same shared counter
    assert second_counter() == 2


def test_transient_throws_when_single_dependency_conditions_false_and_throw_not_set():
    # Arrange
    container = Container()
    container.register_singleton(42, key=int)
    container.register_transient(
        FromContainer(int, lambda value: f"str: {value + 1}"),
        key=str,
        condition=lambda: False,
    )
    container.build()

    # Act / Assert
    with pytest.raises(
        PartialContainerError,
        match=re.escape(
            "No object with key <class 'str'> was built because the built condition has not been met."
        ),
    ):
        container.resolve(str)


def test_transient_throws_when_single_dependency_conditions_false_and_throw_set():
    # Arrange
    container = Container()
    container.register_transient(42, key=int)
    container.register_transient(
        FromContainer(int, lambda value: f"str: {value + 1}"),
        key=str,
        condition=lambda: False,
        throw_if_condition_not_satisfied=True,
    )
    container.build()

    # Act / Assert
    with pytest.raises(
        PartialContainerError,
        match=re.escape(
            "No object with key <class 'str'> was built because the built condition has not been met."
        ),
    ):
        container.resolve(str)
