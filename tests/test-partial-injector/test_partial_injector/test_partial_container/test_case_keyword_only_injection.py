"""Tests that keyword-only parameters (after ``*``) are injected by the container
while ordinary positional parameters—even when they share the same type
annotation—remain open for the caller to supply.

This certifies the recommended pattern::

    def step(
        caller_arg: InputType,   # ← caller supplies
        *,
        dep_service: Service,    # ← container injects
    ) -> OutputType:
        ...
"""

from partial_injector.partial_container import Container


class _Service:
    def __init__(self, label: str) -> None:
        self.label = label


def test_keyword_only_dep_injected_by_type():
    # Arrange
    dep = _Service("injected")

    def step(*, svc: _Service) -> _Service:
        return svc

    container = Container()
    container.register_singleton(dep, key=_Service)
    container.register_singleton(step)
    container.build()

    # Act
    fn = container.resolve(step)
    result = fn()

    # Assert
    assert result is dep


def test_positional_left_open_keyword_only_injected():
    # Arrange — positional has no matching registration; keyword-only dep does
    dep = _Service("injected")

    def step(raw: str, *, svc: _Service) -> tuple[str, _Service]:
        return raw, svc

    container = Container()
    container.register_singleton(dep, key=_Service)
    container.register_singleton(step)
    container.build()

    # Act
    fn = container.resolve(step)
    result = fn("caller-value")

    # Assert
    assert result[0] == "caller-value"  # positional intact — supplied by caller
    assert result[1] is dep  # keyword-only — injected by container


def test_positional_and_keyword_same_type_positional_left_open():
    # Arrange — both params share the same type; dep is registered under the
    # keyword-only param's *name* (string key), so only that param is injected.
    dep = _Service("injected")

    def step(
        caller_svc: _Service,
        *,
        dep_svc: _Service,
    ) -> tuple[_Service, _Service]:
        return caller_svc, dep_svc

    container = Container()
    # Key is the string "dep_svc" — matched by name.
    # "caller_svc" has no registered name and _Service type is not a key,
    # so it remains open for the caller even though it shares the same type.
    container.register_singleton(dep, key="dep_svc")
    container.register_singleton(step)
    container.build()

    # Act
    fn = container.resolve(step)
    caller_input = _Service("caller")
    result = fn(caller_input)

    # Assert
    assert result[0] is caller_input  # positional intact — supplied by caller
    assert result[1] is dep  # keyword-only — injected by container


def test_positional_only_never_injected():
    # Arrange — a POSITIONAL_ONLY param (before ``/``) is never injected even
    # when its type annotation matches a registered key.
    dep = _Service("injected")

    def step(svc: _Service, /, *, kw_svc: _Service) -> tuple[_Service, _Service]:
        return svc, kw_svc

    container = Container()
    container.register_singleton(dep, key=_Service)
    container.register_singleton(step)
    container.build()

    # Act
    fn = container.resolve(step)
    caller_input = _Service("caller")
    result = fn(caller_input)

    # Assert
    assert result[0] is caller_input  # positional-only intact — never injected
    assert result[1] is dep  # keyword-only — injected by container
