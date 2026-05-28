import re

import pytest

from partial_injector.error_handling import PartialContainerError
from partial_injector.partial_container import Container


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

    container.register_transient_factory(lambda: NumberContainer(), key=NumberContainer)
    container.build()

    # Act / Assert
    number_container = container.resolve(NumberContainer)
    assert number_container.value == 0

    number_container.increment()

    number_container = container.resolve(NumberContainer)
    assert number_container.value == 0


def test_transient_factory_produces_new_instance_each_time_it_used_as_parameter():
    # Arrange
    container = Container()

    container.register_transient_factory(lambda: NumberContainer(), key=NumberContainer)
    container.register_singleton(__outer_function)
    container.build()

    # Act
    container.resolve(__outer_function)()
    final_value = container.resolve(__outer_function)()

    # Assert
    assert final_value == 1


def test_transient_factory_works_the_same_when_resolved_directly_and_used_as_parameter_together():
    # Arrange
    # Factory creates a fresh NumberContainer each time it is called.
    # Resolving directly and resolving as an injected parameter must both
    # produce independent instances — neither path should mutate the other.
    container = Container()

    container.register_transient_factory(lambda: NumberContainer(), key=NumberContainer)
    container.register_singleton(__outer_function)
    container.build()

    # Act
    resolved_direct = container.resolve(NumberContainer)
    direct_value_before = resolved_direct.value  # 0 — fresh instance
    resolved_direct.increment()  # only this instance reaches value=1

    # __outer_function injects NumberContainer; with transient it must receive
    # a *fresh* instance on every call, independent of resolved_direct.
    result_via_param = container.resolve(__outer_function)()

    # Assert
    assert direct_value_before == 0  # captured before any increment
    assert resolved_direct.value == 1  # only one increment on the direct instance
    assert result_via_param == 1  # fresh instance for the param, also incremented once


def test_single_transient_factory_registration_with_failed_dependency_throws():
    # Arrange
    container = Container()
    container.register_transient_factory(
        lambda n: n, factory_args=[1], key=int, condition=lambda: False
    )
    container.build()

    # Act / Assert
    with pytest.raises(
        PartialContainerError,
        match=re.escape(
            "No object with key <class 'int'> was built because the built condition has not been met."
        ),
    ):
        container.resolve(int)
