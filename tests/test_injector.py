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
            def provide_inspect(self, multiplier=1) -> dependency_type:
                return dependency_value * multiplier

            @provider
            async def provide_inspect_async(self, multiplier=1) -> dependency_type:
                return dependency_value * multiplier

    elif request.param == "decorator":

        class MyModule(Module):
            @provides(dependency_type)
            def provide_decorator(self, multiplier=1):
                return dependency_value * multiplier

            @provides(dependency_type)
            async def provide_decorator_async(self, multiplier=1):
                return dependency_value * multiplier

    elif request.param == "context_inspect":

        class MyModule(Module):
            @contextprovider
            @contextlib.contextmanager
            def provide_context_inspect(self, multiplier=1) -> dependency_type:
                yield dependency_value * multiplier

            @contextprovider
            @contextlib.asynccontextmanager
            async def provide_context_inspect_async(
                self, multiplier=1
            ) -> dependency_type:
                yield dependency_value * multiplier

    elif request.param == "context_decorator":

        class MyModule(Module):
            @provides(dependency_type, context=True)
            @contextlib.contextmanager
            def provide_context_decorator(self, multiplier=1):
                yield dependency_value * multiplier

            @provides(dependency_type, context=True)
            @contextlib.asynccontextmanager
            async def provide_context_decorator_async(self, multiplier=1):
                yield dependency_value * multiplier

    elif request.param == "register_inspect":

        class MyModule(Module):
            pass

        def provide_register_inspect(injector, multiplier=1) -> dependency_type:
            return dependency_value * multiplier

        MyModule.register(provide_register_inspect)

        async def provide_register_inspect_async(
            injector, multiplier=1
        ) -> dependency_type:
            return dependency_value * multiplier

        MyModule.register(provide_register_inspect_async)

    elif request.param == "register":

        class MyModule(Module):
            pass

        def provide_register(injector, multiplier=1):
            return dependency_value * multiplier

        MyModule.register(provide_register, dependency_type)

        async def provide_register_async(injector, multiplier=1):
            return dependency_value * multiplier

        MyModule.register(provide_register_async, dependency_type)

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


@pytest.fixture(params=["inspect", "explicit"])
def target_style(request):
    return request.param


@pytest.fixture(params=["", "param"])
def target_param(request):
    return request.param


@pytest.fixture
def inject_target(
    target_style, target_param, injector, dependency_type, dependency_value
):
    key = (target_style, target_param)

    if key == ("inspect", ""):

        @injector
        def target(*, value: dependency_type) -> dependency_type:
            return value

    elif key == ("explicit", ""):

        @injector.inject(value=dependency_type)
        def target(*, value) -> dependency_type:
            return value

    elif key == ("inspect", "param"):

        @injector
        @injector.param("value", multiplier=5)
        def target(*, value: dependency_type) -> dependency_type:
            return value

    elif key == ("explicit", "param"):

        @injector.inject(value=dependency_type)
        @injector.param("value", multiplier=5)
        def target(*, value: dependency_type):
            return value

    else:
        raise RuntimeError("Cannot do " + key)

    return target


@pytest.fixture
def inject_target_async(
    target_style, target_param, injector, dependency_type, dependency_value
):
    key = (target_style, target_param)

    if key == ("inspect", ""):

        @injector
        async def target(*, value: dependency_type) -> dependency_type:
            return value

    elif key == ("explicit", ""):

        @injector.inject(value=dependency_type)
        async def target(*, value) -> dependency_type:
            return value

    elif key == ("inspect", "param"):

        @injector
        @injector.param("value", multiplier=5)
        async def target(*, value: dependency_type) -> dependency_type:
            return value

    elif key == ("explicit", "param"):

        @injector.inject(value=dependency_type)
        @injector.param("value", multiplier=5)
        async def target(*, value: dependency_type):
            return value

    else:
        raise RuntimeError("Cannot do " + key)

    return target


def test_inject(dependency_value, inject_target, target_param):
    if target_param:
        expected_value = dependency_value * 5
    else:
        expected_value = dependency_value

    assert inject_target() == expected_value


def test_use_provided_value(inject_target):
    value = mock.sentinel.EXPECTED_VALUE
    assert inject_target(value=value) == value


@pytest.mark.asyncio
async def test_inject_async(dependency_value, inject_target_async, target_param):
    if target_param:
        expected_value = dependency_value * 5
    else:
        expected_value = dependency_value

    assert (await inject_target_async()) == expected_value
