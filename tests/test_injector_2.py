import contextlib
from unittest import mock

import pytest

from diana import Module, Injector, provider, contextprovider, provides


@pytest.fixture(params=[(int, 1)])
def dependency(request):
    return request.param


@pytest.fixture
def dependency_type(dependency):
    return dependency[0]


@pytest.fixture
def dependency_value(dependency):
    return dependency[1]


@pytest.fixture(
    params=[
        "inspect",
        "decorator",
        "context_inspect",
        "context_decorator",
        "register_inspect",
        "register",
    ]
)
def module_cls(request, dependency_type, dependency_value):
    if request.param == "inspect":

        class MyModule(Module):
            @provider
            def provide(self) -> dependency_type:
                return dependency_value

            @provider
            async def provide_async(self) -> dependency_type:
                return dependency_value

    elif request.param == "decorator":

        class MyModule(Module):
            @provides(dependency_type)
            def provide(self):
                return dependency_value

            @provides(dependency_type)
            async def provide_async(self):
                return dependency_value

    elif request.param == "context_inspect":

        class MyModule(Module):
            @contextprovider
            @contextlib.contextmanager
            def provide(self) -> dependency_type:
                yield dependency_value

            @contextprovider
            @contextlib.asynccontextmanager
            async def provide_async(self) -> dependency_type:
                yield dependency_value

    elif request.param == "context_decorator":

        class MyModule(Module):
            @provides(dependency_type, context=True)
            @contextlib.contextmanager
            def provide(self):
                yield dependency_value

            @provides(dependency_type, context=True)
            @contextlib.asynccontextmanager
            async def provide_async(self):
                yield dependency_value

    elif request.param == "register_inspect":

        class MyModule(Module):
            pass

        def provide(injector) -> dependency_type:
            return dependency_value

        MyModule.register(provide)

        async def provide_async(injector) -> dependency_type:
            return dependency_value

        MyModule.register(provide_async)

    elif request.param == "register":

        class MyModule(Module):
            pass

        def provide(injector):
            return dependency_value

        MyModule.register(provide, dependency_type)

        async def provide_async(injector):
            return dependency_value

        MyModule.register(provide_async, dependency_type)

    else:
        raise RuntimeError("Cannot do " + request.param)

    return MyModule


@pytest.fixture
def module(module_cls):
    return module_cls()


@pytest.fixture
def injector(module):
    injector = Injector()
    injector.load(module)
    return injector


@pytest.fixture(params=["inspect"])
def inject_target(request, injector, dependency_type, dependency_value):
    if request.param == "inspect":

        @injector
        def target(*, value: dependency_type) -> dependency_type:
            return value

    else:
        raise RuntimeError("Cannot do " + request.param)

    return target


@pytest.fixture(params=["inspect"])
def inject_target_async(request, injector, dependency_type, dependency_value):
    if request.param == "inspect":

        @injector
        async def target(*, value: dependency_type) -> dependency_type:
            return value

    else:
        raise RuntimeError("Cannot do " + request.param)

    return target


def test_inject(dependency_value, inject_target):
    assert inject_target() == dependency_value


def test_use_provided_value(inject_target):
    value = mock.sentinel.EXPECTED_VALUE
    assert inject_target(value=value) == value


@pytest.mark.asyncio
async def test_inject_async(dependency_value, inject_target_async):
    assert (await inject_target_async()) == dependency_value