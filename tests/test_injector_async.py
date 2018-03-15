import pytest

from diana.injector import Injector
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


@ModuleAsync.provider
async def provide_string(self, length: int) -> str:
    return STR_VALUE * length


class AltModuleAsync(Module):
    @provider
    def provide_bool(self) -> bool:
        return False


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
    injector.load(*modules)
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
def defaulted_injected_function(request, injector):
    if request.param == '__call__':
        @injector
        async def requires_bool(*, a_bool: bool = False):
            return a_bool

    elif request.param == 'inject':
        @injector.inject(a_bool=bool)
        async def requires_bool(a_bool=False):
            return a_bool

    return requires_bool


@pytest.fixture(params=['__call__', 'inject', 'param'])
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

    elif request.param == 'param':
        @injector.param('a_str', str, length=LENGTH)
        async def requires_str(a_str):
            return a_str

    return requires_str


async def test_basic(basic_injected_function):
    assert (await basic_injected_function()) == INT_VALUE


async def test_inject_param(parametrized_injected_function):
    assert (await parametrized_injected_function()) == STR_VALUE * LENGTH


async def test_basic_manual(basic_injected_function):
    assert (await basic_injected_function(an_int=99)) == 99


async def test_provided_defaults(defaulted_injected_function):
    assert (await defaulted_injected_function()) == False
    assert (await defaulted_injected_function(a_bool=True)) == True


@pytest.mark.parametrize('modules', [(AltModuleAsync,)], indirect=True)
async def test_missing_dependency(injector, basic_injected_function):
    with pytest.raises(RuntimeError):
        await basic_injected_function()


@pytest.mark.parametrize('modules', [(AltModuleAsync,)], indirect=True)
async def test_missing_dependency_provided(injector, basic_injected_function):
    assert (await basic_injected_function(an_int=99)) == 99


async def test_instancemethod(injector):
    class MyThing(object):
        @injector
        async def requires_int(self, *, an_int: int) -> int:
            return self, an_int

    thing = MyThing()

    assert (await thing.requires_int()) == (thing, INT_VALUE)


async def test_classmethod(injector):
    class MyThing(object):
        @classmethod
        @injector
        async def requires_int(cls, *, an_int: int) -> int:
            return cls, an_int

    thing = MyThing()
    assert (await thing.requires_int()) == (MyThing, INT_VALUE)


async def test_staticmethod(injector):
    class MyThing(object):
        @staticmethod
        @injector
        async def requires_int(*, an_int: int) -> int:
            return an_int

    thing = MyThing()
    assert (await thing.requires_int()) == INT_VALUE
