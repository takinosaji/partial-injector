import pytest

from partial_injector.partial_container import Container


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
    assert  first_number_container_returner is not second_number_container_returner
    assert first_number_container_returner() is second_number_container_returner()