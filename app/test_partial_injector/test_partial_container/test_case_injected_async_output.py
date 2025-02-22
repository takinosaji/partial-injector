import asyncio

import pytest

from partial_injector.partial_container import Container

def __sync_dependency_that_returns_async():
    return __async_dependency

def __innermost_dependency_of_async():
    return "EXPECTED RESULT"

async def __async_dependency(innermost_dependency_of_async: __innermost_dependency_of_async):
    await asyncio.sleep(0)
    return innermost_dependency_of_async()

@pytest.mark.asyncio
async def test_container_can_inject_dependencies_to_async_correctly():
    container = Container()
    container.register_instance(__sync_dependency_that_returns_async, inject_returns=True)
    container.register_instance(__async_dependency)
    container.register_instance(__innermost_dependency_of_async)
    container.build()

    outermost_dependency = container.resolve(__sync_dependency_that_returns_async)
    async_dependency = outermost_dependency()
    result = await async_dependency()

    assert result == "EXPECTED RESULT"
