import re
from typing import Callable

import pytest

from partial_injector.error_handling import PartialContainerException
from partial_injector.partial_container import Container

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
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner)
    container.register_instance(return_two, key=NumberReturner)
    container.register_instance(return_three, key=NumberReturner)
    container.build()

    number_returners = container.resolve(list[NumberReturner])

    assert len(number_returners) == 3
    assert multiple_number_adder(number_returners) == 26

def test_container_throws_when_all_dependency_conditions_false():
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner, condition=lambda: False)
    container.register_instance(return_two, key=NumberReturner, condition=lambda: False)
    container.register_instance(return_three, key=NumberReturner, condition=lambda: False)

    with pytest.raises(PartialContainerException,
                       match=re.escape("No objects with key partial_injector.partial_container.Container.RegistrationContainer[NumberReturner] were built because built conditions have not been met for any of the registrations.")):
        container.build()

def test_container_doesnt_throw_when_all_dependency_conditions_false_and_ignored():
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner, condition=lambda: False, condition_ignore_not_satisfied=True)
    container.register_instance(return_two, key=NumberReturner, condition=lambda: False, condition_ignore_not_satisfied=True)
    container.register_instance(return_three, key=NumberReturner, condition=lambda: False, condition_ignore_not_satisfied=True)

    container.build()

def test_container_can_resolve_some_with_same_key_correctly():
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner)
    container.register_instance(return_two, key=NumberReturner, condition=lambda: False)
    container.register_instance(return_three, key=NumberReturner)
    container.build()

    number_returners = container.resolve(list[NumberReturner])

    assert len(number_returners) == 2
    assert multiple_number_adder(number_returners) == 24

def test_container_can_resolve_the_single_dependency_with_same_key_as_list_correctly():
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner, condition=lambda: False)
    container.register_instance(return_two, key=NumberReturner, condition=lambda: False)
    container.register_instance(return_three, key=NumberReturner)
    container.build()

    number_returners = container.resolve(list[NumberReturner])

    assert len(number_returners) == 1
    assert multiple_number_adder(number_returners) == 13

def test_container_can_resolve_the_single_dependency_with_same_key_as_single_item_correctly():
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner, condition=lambda: False)
    container.register_instance(return_two, key=NumberReturner, condition=lambda: False)
    container.register_instance(return_three, key=NumberReturner)
    container.build()

    number_returner = container.resolve(NumberReturner)

    assert number_returner() == 13

def test_container_can_inject_many_dependencies_with_same_key_correctly():
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner)
    container.register_instance(return_two, key=NumberReturner)
    container.register_instance(return_three, key=NumberReturner)
    container.register_instance(multiple_number_adder, key=NumberAdder)
    container.build()

    result = container.resolve(NumberAdder)

    assert result() == 26


def test_container_can_inject_many_dependencies_in_returns():
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner)
    container.register_instance(return_two, key=NumberReturner)
    container.register_instance(return_three, key=NumberReturner)
    container.register_instance(multiple_number_adder_returner, key=NumberAdderReturner, inject_returns=True)
    container.build()

    adder_returner = container.resolve(NumberAdderReturner)
    adder = adder_returner()

    assert adder() == 26

def test_container_can_inject_single_dependency_of_many_in_returns():
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner)
    container.register_instance(return_two, key=NumberReturner, condition=lambda: False)
    container.register_instance(return_three, key=NumberReturner, condition=lambda: False)
    container.register_instance(single_number_adder_returner, key=NumberAdderReturner, inject_returns=True)
    container.build()

    adder_returner = container.resolve(NumberAdderReturner)
    adder = adder_returner()

    assert adder() == 11

def test_container_can_inject_multiple_dependencies_of_many_in_returns():
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner)
    container.register_instance(return_two, key=NumberReturner, condition=lambda: False)
    container.register_instance(return_three, key=NumberReturner, condition=lambda: False)
    container.register_instance(multiple_number_adder_returner, key=NumberAdderReturner, inject_returns=True)
    container.build()

    adder_returner = container.resolve(NumberAdderReturner)
    adder = adder_returner()

    assert adder() == 11