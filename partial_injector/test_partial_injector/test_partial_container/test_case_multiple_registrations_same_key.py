import re
from typing import Callable

import pytest

from partial_injector.error_handling import PartialContainerException
from partial_injector.partial_container import Container

type NumberPassthrough = Callable[[int], int]
type NumberReturner = Callable[[], int]
type NumberAdder = Callable[[], int]
type NumberAdderReturner = Callable[[], NumberAdder]
type ConstantReturner = Callable[[], int]

def __return_constant() -> int:
    return 10
return_constant: ConstantReturner = __return_constant


def __return_one(get_constant: ConstantReturner) -> int:
    return get_constant() + 1
return_one: NumberReturner = __return_one


def __return_two() -> int:
    return 2
return_two: NumberReturner = __return_two


def __return_three(get_constant: ConstantReturner) -> int:
    return get_constant() + 3
return_three: NumberReturner = __return_three


def __single_number_adder(number_returner: NumberReturner) -> int:
    return number_returner()
single_number_adder: NumberAdder = __single_number_adder


def __single_number_adder_returner() -> NumberAdder:
    return single_number_adder
single_number_adder_returner: NumberAdderReturner = __single_number_adder_returner


def __multiple_number_adder(number_returners: list[NumberReturner]) -> int:
    accumulator = 0
    for number_returner in number_returners:
        accumulator += number_returner()
    return accumulator
multiple_number_adder: NumberAdder = __multiple_number_adder


def __multiple_number_adder_returner() -> NumberAdder:
    return multiple_number_adder
multiple_number_adder_returner: NumberAdderReturner = __multiple_number_adder_returner


def test_container_can_resolve_all_with_same_key_correctly():
    # Arrange
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton(return_one, key=NumberReturner)
    container.register_singleton(return_two, key=NumberReturner)
    container.register_singleton(return_three, key=NumberReturner)
    container.build()

    # Act
    number_returners = container.resolve(list[NumberReturner])

    # Assert
    assert len(number_returners) == 3
    assert multiple_number_adder(number_returners) == 26


def test_container_throws_when_all_dependency_conditions_false():
    # Arrange
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton(return_one, key=NumberReturner, condition=lambda: False)
    container.register_singleton(return_two, key=NumberReturner, condition=lambda: False)
    container.register_singleton(return_three, key=NumberReturner, condition=lambda: False)

    # Act / Assert
    with pytest.raises(PartialContainerException,
                       match=re.escape("No objects with key partial_injector.partial_container.Container.ListOfDependencies[NumberReturner] were built because built conditions have not been met for any of the registrations.")):
        container.build()


def test_container_doesnt_throw_when_all_dependency_conditions_false_and_ignored():
    # Arrange
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton(return_one, key=NumberReturner, condition=lambda: False, condition_ignore_not_satisfied=True)
    container.register_singleton(return_two, key=NumberReturner, condition=lambda: False, condition_ignore_not_satisfied=True)
    container.register_singleton(return_three, key=NumberReturner, condition=lambda: False, condition_ignore_not_satisfied=True)

    # Act
    container.build()

    # Assert
    # no exception means success
    assert True


def test_container_can_resolve_some_with_same_key_correctly():
    # Arrange
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton(return_one, key=NumberReturner)
    container.register_singleton(return_two, key=NumberReturner, condition=lambda: False)
    container.register_singleton(return_three, key=NumberReturner)
    container.build()

    # Act
    number_returners = container.resolve(list[NumberReturner])

    # Assert
    assert len(number_returners) == 2
    assert multiple_number_adder(number_returners) == 24


def test_container_can_resolve_the_single_dependency_with_same_key_as_list_correctly():
    # Arrange
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton(return_one, key=NumberReturner, condition=lambda: False)
    container.register_singleton(return_two, key=NumberReturner, condition=lambda: False)
    container.register_singleton(return_three, key=NumberReturner)
    container.build()

    # Act
    number_returners = container.resolve(list[NumberReturner])

    # Assert
    assert len(number_returners) == 1
    assert multiple_number_adder(number_returners) == 13


def test_container_can_resolve_the_single_dependency_with_same_key_as_single_item_correctly():
    # Arrange
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton(return_one, key=NumberReturner, condition=lambda: False)
    container.register_singleton(return_two, key=NumberReturner, condition=lambda: False)
    container.register_singleton(return_three, key=NumberReturner)
    container.build()

    # Act
    number_returner = container.resolve(NumberReturner)

    # Assert
    assert number_returner() == 13


def test_container_can_inject_many_dependencies_with_same_key_correctly():
    # Arrange
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton(return_one, key=NumberReturner)
    container.register_singleton(return_two, key=NumberReturner)
    container.register_singleton(return_three, key=NumberReturner)
    container.register_singleton(multiple_number_adder, key=NumberAdder)
    container.build()

    # Act
    result = container.resolve(NumberAdder)

    # Assert
    assert result() == 26


def test_container_can_inject_many_dependencies_in_returns():
    # Arrange
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton(return_one, key=NumberReturner)
    container.register_singleton(return_two, key=NumberReturner)
    container.register_singleton(return_three, key=NumberReturner)
    container.register_singleton(multiple_number_adder_returner, key=NumberAdderReturner, inject_returns=True)
    container.build()

    # Act
    adder_returner = container.resolve(NumberAdderReturner)
    adder = adder_returner()

    # Assert
    assert adder() == 26


def test_container_can_inject_single_dependency_of_many_in_returns():
    # Arrange
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton(return_one, key=NumberReturner)
    container.register_singleton(return_two, key=NumberReturner, condition=lambda: False)
    container.register_singleton(return_three, key=NumberReturner, condition=lambda: False)
    container.register_singleton(single_number_adder_returner, key=NumberAdderReturner, inject_returns=True)
    container.build()

    # Act
    adder_returner = container.resolve(NumberAdderReturner)
    adder = adder_returner()

    # Assert
    assert adder() == 11


def test_container_can_inject_multiple_dependencies_of_many_in_returns():
    # Arrange
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton(return_one, key=NumberReturner)
    container.register_singleton(return_two, key=NumberReturner, condition=lambda: False)
    container.register_singleton(return_three, key=NumberReturner, condition=lambda: False)
    container.register_singleton(multiple_number_adder_returner, key=NumberAdderReturner, inject_returns=True)
    container.build()

    # Act
    adder_returner = container.resolve(NumberAdderReturner)
    adder = adder_returner()

    # Assert
    assert adder() == 11


def test_container_can_resolve_all_with_same_key_correctly_using_transient_factories():
    # Arrange
    container = Container()
    container.register_transient_factory(lambda n: n, factory_args=[1], key=int)
    container.register_transient_factory(lambda n: n, factory_args=[2], key=int, condition=lambda: False)
    container.register_transient_factory(lambda n: n, factory_args=[3], key=int)
    container.build()

    # Act
    ints = container.resolve(list[int])

    # Assert
    assert len(ints) == 2
    assert sum(ints) == 4


def test_multiple_transient_factory_registration_with_failed_dependency_throw():
    # Arrange
    container = Container()
    container.register_transient_factory(lambda n: n, factory_args=[1], key=int, condition=lambda: False)
    container.register_transient_factory(lambda n: n, factory_args=[2], key=int, condition=lambda: False)
    container.register_transient_factory(lambda n: n, factory_args=[3], key=int, condition=lambda: False)
    container.build()

    # Act / Assert
    with pytest.raises(
        PartialContainerException,
        match=re.escape(
            "No objects with key <class 'int'> were built because built conditions have not been met for any of the registrations at the moment of resolution."
        ),
    ):
        container.resolve(list[int])


def test_container_can_resolve_all_with_same_key_correctly_using_singleton_factories():
    # Arrange
    container = Container()
    container.register_singleton_factory(lambda n: n, factory_args=[1], key=int)
    container.register_singleton_factory(lambda n: n, factory_args=[2], key=int, condition=lambda: False)
    container.register_singleton_factory(lambda n: n, factory_args=[3], key=int)
    container.build()

    # Act
    ints = container.resolve(list[int])

    # Assert
    assert len(ints) == 2
    assert sum(ints) == 4


def test_multiple_singleton_factory_registration_with_failed_dependency_throw():
    # Arrange
    container = Container()
    container.register_singleton_factory(lambda n: n, factory_args=[1], key=int, condition=lambda: False)
    container.register_singleton_factory(lambda n: n, factory_args=[2], key=int, condition=lambda: False)
    container.register_singleton_factory(lambda n: n, factory_args=[3], key=int, condition=lambda: False)

    # Act / Assert
    with pytest.raises(
        PartialContainerException,
        match=re.escape(
            "No objects with key partial_injector.partial_container.Container.ListOfDependencies[int] were built because built conditions have not been met for any of the registrations."
        ),
    ):
        container.build()
