import typing as t
import contextlib
from functools import partial

import pytest
import diana

SYNC = "sync"
ASYNC = "async"
RETURN = "return"
CONTEXT = "context"
GENERATOR = "generator"
INSPECT = "inspect"
EXPLICIT = "explicit"
DECORATOR = "decorator"
REGISTER = "register"
REGISTER_INSPECT = "register_inspect"


async def no_op():
    return


@pytest.fixture
def dep_type():
    return t.NewType("Dependency", str)


@pytest.fixture
def dep_value(dep_type):
    return dep_type("-")


@pytest.fixture(params=[SYNC, ASYNC])
def execution_model(request):
    return request.param


@pytest.fixture(params=[RETURN, CONTEXT], ids=lambda x: f"Provider:{x}")
def _provider_func(request):
    return request.param


@pytest.fixture
def provider_func(_provider_func, execution_model, dep_type, dep_value):
    key = (execution_model, _provider_func)

    if key == (SYNC, RETURN):

        def provider(self, length=1) -> dep_type:
            return dep_value * length

    elif key == (SYNC, CONTEXT):

        @contextlib.contextmanager
        def provider(self, length=1) -> dep_type:
            yield dep_value * length

    elif key == (ASYNC, RETURN):

        async def provider(self, length=1) -> dep_type:
            await no_op()
            return dep_value * length

    elif key == (ASYNC, CONTEXT):

        @contextlib.asynccontextmanager
        async def provider(self, length=1) -> dep_type:
            await no_op()
            yield dep_value * length

    else:
        raise RuntimeError()

    return provider


@pytest.fixture(
    params=[INSPECT, DECORATOR, REGISTER, REGISTER_INSPECT],
    ids=lambda x: f"Wrapper:{x}",
)
def _provider_wrapper(request):
    return request.param


@pytest.fixture
def module(_provider_wrapper, provider_func, _provider_func, dep_type):
    if _provider_func == RETURN:
        provider = diana.provider
        provides = diana.provides(dep_type)
        context = False
    elif _provider_func == CONTEXT:
        provider = diana.contextprovider
        provides = diana.provides(dep_type, context=True)
        context = True
    else:
        raise RuntimeError(_provider_func)

    if _provider_wrapper in (INSPECT, DECORATOR):
        if _provider_wrapper == INSPECT:
            wrapped_func = provider(provider_func)

        elif _provider_wrapper == DECORATOR:
            wrapped_func = provides(provider_func)

        module = type("TestModule", (diana.Module,), {"test_provider": wrapped_func})

        return module()

    elif _provider_wrapper in (REGISTER, REGISTER_INSPECT):

        class module(diana.Module):
            pass

        if _provider_wrapper == REGISTER:
            module.register(provider_func, dep_type, context=context)

        elif _provider_wrapper == REGISTER_INSPECT:
            module.register(provider_func, context=context)

        return module()

    else:
        raise RuntimeError(_provider_wrapper)


@pytest.fixture
def injector(module):
    injector = diana.Injector()
    injector.load(module)
    return injector


@pytest.fixture(params=[RETURN, GENERATOR], ids=lambda x: f"Target:{x}")
def _target_func(request):
    return request.param


@pytest.fixture
def target_func(_target_func, execution_model, dep_type):
    key = (execution_model, _target_func)

    if key == (SYNC, RETURN):

        def target(*, value: dep_type):
            return value

    elif key == (SYNC, GENERATOR):

        def target(*, value: dep_type):
            yield value

    elif key == (ASYNC, RETURN):

        async def target(*, value: dep_type):
            await no_op()
            return value

    elif key == (ASYNC, GENERATOR):

        async def target(*, value: dep_type):
            await no_op()
            yield value

    else:
        raise RuntimeError(key)

    return target


@pytest.fixture(params=[INSPECT, EXPLICIT], ids=lambda x: f"Inject:{x}")
def inject_wrapper(request, injector, dep_type):
    if request.param == INSPECT:
        return injector

    elif request.param == EXPLICIT:
        return injector.inject(value=dep_type)

    else:
        raise RuntimeError()


@pytest.fixture
def target(target_func, inject_wrapper):
    return inject_wrapper(target_func)


@pytest.mark.parametrize("execution_model", [SYNC], indirect=True)
def test_sync(target, dep_value, _target_func):
    if _target_func == RETURN:
        assert target() == dep_value

    elif _target_func == GENERATOR:
        assert next(target()) == dep_value

    else:
        raise RuntimeError()


@pytest.mark.asyncio
@pytest.mark.parametrize("execution_model", [ASYNC], indirect=True)
async def test_async(target, dep_value, _target_func):
    if _target_func == RETURN:
        assert (await target()) == dep_value

    elif _target_func == GENERATOR:
        async for x in target():
            assert x == dep_value

    else:
        raise RuntimeError()

