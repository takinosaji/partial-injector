from dataclasses import dataclass
from typing import Callable

from partial_injector.partial_container import Container, FromContainer

type ConstantReturner = Callable[[], int]
type NumberReturner = Callable[[], int]
type NumberAdder = Callable[[list[NumberReturner]], int]
type NumberAdderFactory = Callable[[], NumberAdder]

@dataclass
class ConfigurationSection:
    property: str

@dataclass
class Configuration:
    section: ConfigurationSection

def test_container_can_resolve_subsection():
    configuration = Configuration(
        section=ConfigurationSection(
            property='value'
        )
    )
    container = Container()
    container.register_instance(configuration, key=Configuration)
    container.register_instance(FromContainer(Configuration, lambda conf: conf.section), key=ConfigurationSection)
    container.build()

    configuration_section = container.resolve(ConfigurationSection)
    assert configuration_section.property == 'value'