from dataclasses import dataclass
from typing import Callable

from partial_injector.partial_container import Container, FromContainer

type ConstantReturner = Callable[[], int]
type NumberReturner = Callable[[], int]
type NumberAdder = Callable[[list[NumberReturner]], int]
type NumberAdderFactory = Callable[[], NumberAdder]


@dataclass
class ConfigurationSection:
    property1: str
    property2: str


@dataclass
class Configuration:
    section: ConfigurationSection


def property_returner(value: str):
    return value


def test_container_can_resolve_subsection():
    configuration = Configuration(
        section=ConfigurationSection(
            property1='value1',
            property2='value2'
        )
    )
    container = Container()
    container.register_singleton(configuration, key=Configuration)
    container.register_singleton(FromContainer(Configuration, lambda conf: conf.section), key=ConfigurationSection)
    container.build()

    configuration_section = container.resolve(ConfigurationSection)
    assert configuration_section.property1 == 'value1'


def test_from_container_lambda_executed_when_passed_as_parameter():
    configuration = Configuration(
        section=ConfigurationSection(
            property1='value1',
            property2='value2'
        )
    )
    container = Container()
    container.register_singleton(configuration, key=Configuration)
    container.register_singleton_factory(property_returner, factory_args=[FromContainer(Configuration, lambda conf: conf.section.property1)], key="factory1")
    container.register_singleton_factory(property_returner, factory_args=[FromContainer(Configuration, lambda conf: conf.section.property2)], key="factory2")
    container.build()

    value1 = container.resolve("factory1")
    value2 = container.resolve("factory2")

    assert value1 == 'value1'
    assert value2 == 'value2'