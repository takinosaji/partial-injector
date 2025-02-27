from typing import Callable

import pytest

from partial_injector.error_handling import TerminationException
from partial_injector.partial_container import Container

type NumberReturner = Callable[[], int]
type NumberAdder = Callable[[], int]
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

def __number_adder(number_returners: NumberReturner) -> int:
    accumulator = 0
    for number_returner in number_returners:
        accumulator += number_returner()
    return accumulator
number_adder: NumberAdder = __number_adder

def test_container_can_resolve_all_with_same_key_correctly():
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner)
    container.register_instance(return_two, key=NumberReturner)
    container.register_instance(return_three, key=NumberReturner)
    container.build()

    number_returners = container.resolve(list[NumberReturner])

    assert len(number_returners) == 3
    assert number_adder(number_returners) == 26

def test_container_can_resolve_some_with_same_key_correctly():
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner)
    container.register_instance(return_two, key=NumberReturner, condition=lambda: False)
    container.register_instance(return_three, key=NumberReturner)
    container.build()

    number_returners = container.resolve(list[NumberReturner])

    assert len(number_returners) == 2
    assert number_adder(number_returners) == 24

def test_container_can_resolve_the_only_with_same_key_correctly():
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner, condition=lambda: False)
    container.register_instance(return_two, key=NumberReturner, condition=lambda: False)
    container.register_instance(return_three, key=NumberReturner)
    container.build()

    number_returners = container.resolve(list[NumberReturner])

    assert len(number_returners) == 1
    assert number_adder(number_returners) == 24

# def test_container_throws_when_all_dependency_condifions_false():
#     container = Container()
#     container.register_instance(return_constant, key=ConstantReturner)
#     container.register_instance(return_one, key=NumberReturner, condition=lambda: False)
#     container.register_instance(return_two, key=NumberReturner, condition=lambda: False)
#     container.register_instance(return_three, key=NumberReturner, condition=lambda: False)
#
#     #with pytest.raises(TerminationException):
#     container.build()
#
#     #number_returners = container.resolve(list[NumberReturner])


def test_container_can_inject_many_deps_with_same_key_correctly():
    container = Container()
    container.register_instance(return_constant, key=ConstantReturner)
    container.register_instance(return_one, key=NumberReturner)
    container.register_instance(return_two, key=NumberReturner)
    container.register_instance(return_three, key=NumberReturner)
    container.register_instance(number_adder, key=NumberAdder)
    container.build()

    result = container.resolve(list[NumberAdder])

    assert result() == 26
