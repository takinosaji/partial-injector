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


def test_single_not_built_dependency_doesnt_throw():
    # Arrange
    container = Container()
    container.register_singleton(42, key=int)
    container.register_singleton(
        FromContainer(int, lambda value: f"str: {value + 1}"),
        key=str,
        condition=lambda: False,
        throw_if_condition_not_satisfied=False,
    )

    # Act / Assert
    container.build()


def test_single_not_built_throws():
    # Arrange
    container = Container()
    container.register_singleton(42, key=int)
    container.register_singleton(
        FromContainer(int, lambda value: f"str: {value + 1}"),
        key=str,
        condition=lambda: False,
        throw_if_condition_not_satisfied=True,
    )

    # Act / Assert
    with pytest.raises(
        PartialContainerError,
        match=re.escape(
            "No object with key <class 'str'> was built because the built condition has not been met."
        ),
    ):
        container.build()
