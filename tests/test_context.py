import typing as t
import contextlib

import pytest

import diana


State = t.NewType("State", dict)


@pytest.fixture
def module():
    class ContextModule(diana.Module):
        def __init__(self):
            self.state: State = {"count": 0}

        @diana.contextprovider
        @contextlib.contextmanager
        def provide(self) -> State:
            self.state["count"] += 1
            yield self.state
            self.state["count"] -= 1

        @diana.contextprovider
        @contextlib.asynccontextmanager
        async def provide_async(self) -> State:
            self.state["count"] += 1
            yield self.state
            self.state["count"] -= 1

    return ContextModule()


@pytest.fixture
def injector(module):
    injector = diana.Injector()
    injector.load(module)
    return injector


def test_within_context(injector):
    @injector
    def uses_state(*, state: State):
        assert state["count"] != 0

    uses_state()


@pytest.mark.asyncio
async def test_within_context_async(injector):
    @injector
    async def uses_state(*, state: State):
        assert state["count"] != 0

    await uses_state()

