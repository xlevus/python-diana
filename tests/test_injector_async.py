import pytest

from diana.injector import Injector, Injected
from diana.module import Module, provider

LENGTH = 3

INT_VALUE = 1
STR_VALUE = 'x'

pytestmark = pytest.mark.asyncio


class ModuleSync(Module):
    @provider
    def provide_int(self) -> int:
        return INT_VALUE

    @provider
    def provide_string(self, length: int) -> str:
        return STR_VALUE * length


class ModuleAsync(Module):
    @provider
    async def provide_int(self) -> int:
        return INT_VALUE

    @provider
    async def provide_string(self, length: int) -> str:
        return STR_VALUE * length


@pytest.fixture(params=[
    (ModuleSync,),
    (ModuleAsync,),
    (ModuleSync, ModuleAsync),
])
def modules(request):
    return [
        module_cls()
        for module_cls in request.param]


@pytest.fixture
def injector(modules):
    injector = Injector()

    for module in modules:
        injector.load_module(module)

    return injector


@pytest.fixture(params=['__call__', 'inject'])
def basic_injected_function(request, injector):
    if request.param == '__call__':
        @injector
        async def requires_int(*, an_int: int):
            return an_int

    elif request.param == 'inject':
        @injector.inject(an_int=int)
        async def requires_int(an_int):
            return an_int

    return requires_int


@pytest.fixture(params=['__call__', 'inject'])
def parametrized_injected_function(request, injector):
    if request.param == '__call__':
        @injector
        @injector.param('a_str', length=LENGTH)
        async def requires_str(*, a_str: str):
            return a_str

    elif request.param == 'inject':
        @injector.inject(a_str=str)
        @injector.param('a_str', length=LENGTH)
        async def requires_str(a_str):
            return a_str

    return requires_str


async def test_basic(basic_injected_function):
    assert isinstance(basic_injected_function, Injected)

    assert (await basic_injected_function()) == INT_VALUE


async def test_inject_param(parametrized_injected_function):
    assert isinstance(parametrized_injected_function, Injected)

    assert (await parametrized_injected_function()) == STR_VALUE * LENGTH
