import pytest
from partial_injector.error_handling import PartialContainerException
from partial_injector.partial_container import Container, FromContainer


class NumberContainer:
    def __init__(self):
        self.value = 0

    def increment(self) -> int:
        self.value += 1
        return self.value


def test_singleton_factory_builds_once_and_resolves_same_instance():
    # Arrange
    container = Container()
    call_count = {"count": 0}

    def make_number_container() -> NumberContainer:
        call_count["count"] += 1
        return NumberContainer()

    container.register_singleton_factory(make_number_container, key=NumberContainer)
    container.build()

    # Act
    instance1 = container.resolve(NumberContainer)
    instance2 = container.resolve(NumberContainer)

    # Assert
    assert instance1 is instance2
    assert call_count["count"] == 1


def test_singleton_factory_without_explicit_key_uses_factory_as_key():
    # Arrange
    container = Container()

    def make_value() -> int:
        return 42

    container.register_singleton_factory(make_value)
    container.build()

    # Act
    result = container.resolve(make_value)

    # Assert
    assert result == 42


def test_singleton_factory_injects_dependencies_via_factory_args():
    # Arrange
    container = Container()

    container.register_singleton(41, key="base")

    def factory(dep: int) -> int:
        return dep + 1

    container.register_singleton_factory(factory, key="result", factory_args=[FromContainer("base")])
    container.build()

    # Act
    result = container.resolve("result")

    # Assert
    assert result == 42


def test_singleton_factory_injects_dependencies_via_factory_kwargs():
    # Arrange
    container = Container()

    container.register_singleton(21, key="base")

    def factory(x: int | None = None) -> int:
        return (x or 0) * 2

    container.register_singleton_factory(factory, key="result", factory_kwargs={"x": FromContainer("base")})
    container.build()

    # Act
    result = container.resolve("result")

    # Assert
    assert result == 42


def test_singleton_factory_raises_when_factory_returns_fromcontainer():
    # Arrange
    container = Container()

    def factory() -> FromContainer[str]:
        return FromContainer("missing")

    container.register_singleton_factory(factory, key="bad")

    # Act / Assert
    with pytest.raises(PartialContainerException, match="Cannot build FromContainer object"):
        container.build()


def test_singleton_factory_register_after_build_raises():
    # Arrange
    container = Container()

    container.register_singleton_factory(lambda: 1, key="value")
    container.build()

    # Act / Assert
    with pytest.raises(PartialContainerException, match="Container already built"):
        container.register_singleton_factory(lambda: 2, key="other")


def test_singleton_factory_resolve_unregistered_key_raises_not_registered():
    # Arrange
    container = Container()

    container.register_singleton_factory(lambda: 1, key="value")
    container.build()

    # Act / Assert
    with pytest.raises(PartialContainerException, match="Object with key unknown not built"):
        container.resolve("unknown")


def test_singleton_factory_resolve_not_built_key_raises_not_built():
    # Arrange
    container = Container()

    container.register_singleton_factory(lambda: 1, key="value")

    # Act / Assert
    with pytest.raises(PartialContainerException, match="Container not built"):
        container.resolve("value")
