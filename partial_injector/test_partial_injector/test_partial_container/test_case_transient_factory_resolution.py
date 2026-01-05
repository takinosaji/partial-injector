import re
import pytest

from partial_injector.partial_container import Container
from partial_injector.error_handling import PartialContainerException


class NumberContainer:
    def __init__(self):
        self.value = 0

    def increment(self) -> int:
        self.value += 1
        return self.value


def __outer_function(number_container: NumberContainer) -> int:
    return number_container.increment()


def test_transient_factory_produces_new_instance_each_time_it_requested_directly():
    # Arrange
    container = Container()
    number_container = NumberContainer()

    container.register_transient_factory(lambda: number_container, key=NumberContainer)
    container.build()

    # Act / Assert
    number_container = container.resolve(NumberContainer)
    assert number_container.value == 0

    number_container.increment()

    number_container = container.resolve(NumberContainer)
    assert number_container.value == 1


def test_transient_factory_produces_new_instance_each_time_it_used_as_parameter():
    # Arrange
    container = Container()
    number_container = NumberContainer()

    container.register_transient_factory(lambda: number_container, key=NumberContainer)
    container.register_singleton(__outer_function)
    container.build()

    # Act
    container.resolve(__outer_function)()
    container.resolve(__outer_function)()

    # Assert
    assert number_container.value == 0


def test_transient_factory_works_the_same_when_resolved_directly_and_used_as_parameter_together():
    # Arrange
    container = Container()
    number_container = NumberContainer()

    container.register_transient_factory(lambda: number_container, key=NumberContainer)
    container.register_singleton(__outer_function)
    container.build()

    # Act
    resolved_direct = container.resolve(NumberContainer)
    direct_value_before = resolved_direct.value
    resolved_direct.increment()
    container.resolve(__outer_function)()

    # Assert
    assert direct_value_before == 0
    assert number_container.value == 0


def test_sigle_transient_factory_registration_with_failed_dependency_throws():
    # Arrange
    container = Container()
    container.register_transient_factory(lambda n: n, factory_args=[1], key=int, condition=lambda: False)
    container.build()

    # Act / Assert
    with pytest.raises(
        PartialContainerException,
        match=re.escape(
            "No objects with key <class 'int'> were built because built conditions have not been met for any of the registrations at the moment of resolution."
        ),
    ):
        container.resolve(int)

