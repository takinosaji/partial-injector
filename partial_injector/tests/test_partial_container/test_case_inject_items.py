from typing import Callable

from partial_injector.partial_container import Container

type ConstantReturner = Callable[[], int]
type NumberReturner = Callable[[], int]
type NumberAdder = Callable[[list[NumberReturner]], int]
type NumberAdderFactory = Callable[[], NumberAdder]

def __return_constant() -> int:
    return 10
return_constant: ConstantReturner = __return_constant

def __return_one(get_constant: ConstantReturner) -> int:
    return get_constant() + 1
return_one: NumberReturner = __return_one

def __number_adder_factory() -> NumberAdder:
    def number_adder(number_returners: list[NumberReturner]) -> int:
        return sum([number_returner() for number_returner in number_returners])
    return number_adder
number_adder_factory: NumberAdderFactory = __number_adder_factory

def test_container_can_inject_single_container_in_returns():
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton([return_one], key=list[NumberReturner], inject_items=True)
    container.register_singleton(number_adder_factory, key=NumberAdderFactory, inject_returns=True)
    container.build()

    factory = container.resolve(NumberAdderFactory)
    number_adder = factory()

    assert number_adder() == 11

def test_container_can_inject_multiple_containers_in_returns():
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton([return_one, return_one], key=list[NumberReturner], inject_items=True)
    container.register_singleton(number_adder_factory, key=NumberAdderFactory, inject_returns=True)
    container.build()

    factory = container.resolve(NumberAdderFactory)
    number_adder = factory()

    assert number_adder() == 22

def test_container_can_inject_multiple_containers():
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton([return_one, return_one], key=list[NumberReturner], inject_items=True)
    container.build()

    number_returners = container.resolve(list[NumberReturner])

    assert len(number_returners) == 2
    assert sum([n() for n in number_returners]) == 22

def test_container_can_inject_single_container():
    container = Container()
    container.register_singleton(return_constant, key=ConstantReturner)
    container.register_singleton([return_one], key=list[NumberReturner], inject_items=True)
    container.build()

    number_returners = container.resolve(list[NumberReturner])

    assert len(number_returners) == 1
    assert number_returners[0]() == 11