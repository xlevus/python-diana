import pytest

from diana.injector import Injector, Injected
from diana.module import Module, provider

LENGTH = 3

INT_VALUE = 1
STR_VALUE = 'x'


class ModuleSync(Module):
    @provider
    def provide_int(self) -> int:
        return INT_VALUE

    @provider
    def provide_string(self, length: int) -> str:
        return STR_VALUE * length


class AltModuleSync(Module):
    @provider
    def provide_bool(self) -> bool:
        return False


@pytest.fixture(params=[
    (ModuleSync,)
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
        def requires_int(*, an_int: int):
            return an_int

    elif request.param == 'inject':
        @injector.inject(an_int=int)
        def requires_int(an_int):
            return an_int

    return requires_int


@pytest.fixture(params=['__call__', 'inject', 'param'])
def parametrized_injected_function(request, injector):
    if request.param == '__call__':
        @injector
        @injector.param('a_str', length=LENGTH)
        def requires_str(*, a_str: str):
            return a_str

    elif request.param == 'inject':
        @injector.inject(a_str=str)
        @injector.param('a_str', length=LENGTH)
        def requires_str(a_str):
            return a_str

    elif request.param == 'param':
        @injector.param('a_str', str, length=LENGTH)
        def requires_str(a_str):
            return a_str

    return requires_str


def test_basic(basic_injected_function):
    assert isinstance(basic_injected_function, Injected)

    assert basic_injected_function() == INT_VALUE


def test_inject_param(parametrized_injected_function):
    assert isinstance(parametrized_injected_function, Injected)

    assert parametrized_injected_function() == STR_VALUE * LENGTH


def test_module_dependencies(injector):

    class DependentModule(Module):
        @provider
        @injector.inject(a_int=int)
        def provide_float(self, a_int) -> float:
            return float(a_int)

    @injector.inject(a_float=float)
    def requires_float(a_float):
        return a_float

    injector.load_module(DependentModule())

    assert requires_float() == float(INT_VALUE)


@pytest.mark.parametrize('modules', [
    (AltModuleSync,),
], indirect=True)
def test_missing_dependency(injector, basic_injected_function):
    with pytest.raises(RuntimeError):
        basic_injected_function()


def test_module_unloading(injector):
    class ToUnload(Module):
        @provider
        def provide_bool(self) -> bool:
            return False

    assert bool not in injector.providers
    assert str in injector.providers
    assert int in injector.providers

    mod = ToUnload()
    injector.load_module(mod)
    assert bool in injector.providers
    assert str in injector.providers
    assert int in injector.providers

    injector.unload_module(mod)
    assert bool not in injector.providers
    assert str in injector.providers
    assert int in injector.providers


def test_instancemethod(injector):
    class MyThing(object):
        @injector
        def requires_int(self, *, an_int: int) -> int:
            return self, an_int

    thing = MyThing()

    assert thing.requires_int() == (thing, INT_VALUE)


def test_classmethod(injector):
    class MyThing(object):
        @classmethod
        @injector
        def requires_int(cls, *, an_int: int) -> int:
            return cls, an_int

    thing = MyThing()
    assert thing.requires_int() == (MyThing, INT_VALUE)


def test_staticmethod(injector):
    class MyThing(object):
        @staticmethod
        @injector
        def requires_int(*, an_int: int) -> int:
            return an_int

    thing = MyThing()
    assert thing.requires_int() == INT_VALUE
