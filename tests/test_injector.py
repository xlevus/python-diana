import pytest

from diana.injector import Injector
from diana.module import Module, provider

LENGTH = 3

INT_VALUE = 1
STR_VALUE = 'x'


def assert_wrapped(wrapped_func):
    assert hasattr(wrapped_func, '__dependencies__')
    source_func = wrapped_func.__wrapped__

    assert wrapped_func.__doc__ == source_func.__doc__
    assert wrapped_func.__name__ == source_func.__name__

    # Some libraries inspect __code__ directly.
    assert hasattr(wrapped_func, '__code__')

    if hasattr(source_func, '__module__'):
        assert wrapped_func.__module__ == source_func.__module__

    if hasattr(source_func, '__annotations__'):
        assert wrapped_func.__annotations__ == source_func.__annotations__


class ModuleSync(Module):
    @provider
    def provide_int(self) -> int:
        return INT_VALUE


@ModuleSync.provider
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
    injector.load(*modules)

    return injector


@pytest.fixture(params=['__call__', 'inject'])
def basic_injected_function(request, injector):
    if request.param == '__call__':
        @injector
        def requires_int(*, an_int: int):
            """I require an int"""
            return an_int

    elif request.param == 'inject':
        @injector.inject(an_int=int)
        def requires_int(an_int):
            """I require an int"""
            return an_int

    return requires_int


@pytest.fixture(params=['__call__', 'inject'])
def defaulted_injected_function(request, injector):
    if request.param == '__call__':
        @injector
        def requires_bool(*, a_bool: bool = False):
            """I accept a bool"""
            return a_bool

    elif request.param == 'inject':
        @injector.inject(a_bool=bool)
        def requires_bool(a_bool = False):
            """I accept a bool"""
            return a_bool

    return requires_bool



@pytest.fixture(params=['__call__', 'inject', 'param'])
def parametrized_injected_function(request, injector):
    if request.param == '__call__':
        @injector
        @injector.param('a_str', length=LENGTH)
        def requires_str(*, a_str: str):
            """I require a str"""
            return a_str

    elif request.param == 'inject':
        @injector.inject(a_str=str)
        @injector.param('a_str', length=LENGTH)
        def requires_str(a_str):
            """I require a str"""
            return a_str

    elif request.param == 'param':
        @injector.param('a_str', str, length=LENGTH)
        def requires_str(a_str):
            """I require a str"""
            return a_str

    return requires_str


def test_basic(basic_injected_function):
    assert_wrapped(basic_injected_function)

    assert basic_injected_function() == INT_VALUE


def test_basic_manual(basic_injected_function):
    assert basic_injected_function(an_int=99) == 99


def test_inject_param(parametrized_injected_function):
    assert_wrapped(parametrized_injected_function)

    assert parametrized_injected_function() == STR_VALUE * LENGTH


def test_provided_defaults(defaulted_injected_function):
    assert defaulted_injected_function() == False
    assert defaulted_injected_function(a_bool=True) == True


def test_module_dependencies(injector):

    class DependentModule(Module):
        @provider
        @injector.inject(a_int=int)
        def provide_float(self, a_int) -> float:
            return float(a_int)

    @injector.inject(a_float=float)
    def requires_float(a_float):
        return a_float

    injector.load(DependentModule())

    assert requires_float() == float(INT_VALUE)


@pytest.mark.parametrize('modules', [
    (AltModuleSync,),
], indirect=True)
def test_missing_dependency(injector, basic_injected_function):
    with pytest.raises(RuntimeError):
        basic_injected_function()


@pytest.mark.parametrize('modules', [
    (AltModuleSync,),
], indirect=True)
def test_missing_dependency_provided(injector, basic_injected_function):
    assert basic_injected_function(an_int=99) == 99



def test_module_unloading(injector):
    loaded = 0
    unloaded = 0

    class ToUnload(Module):
        @provider
        def provide_bool(self) -> bool:
            return False

        def load(self, injector):
            nonlocal loaded
            assert self not in injector.modules
            loaded += 1

        def unload(self, injector):
            nonlocal unloaded
            assert self not in injector.modules
            unloaded += 1

    assert bool not in injector.providers
    assert str in injector.providers
    assert int in injector.providers

    mod = ToUnload()
    injector.load(mod)
    assert loaded == 1
    assert bool in injector.providers
    assert str in injector.providers
    assert int in injector.providers

    injector.unload(mod)
    assert loaded == 1
    assert unloaded == 1
    assert bool not in injector.providers
    assert str in injector.providers
    assert int in injector.providers


def test_instancemethod(injector):
    class MyThing(object):
        @injector
        def requires_int(self, *, an_int: int) -> int:
            return self, an_int

    thing = MyThing()

    assert_wrapped(thing.requires_int)
    assert thing.requires_int() == (thing, INT_VALUE)


def test_classmethod(injector):
    class MyThing(object):
        @classmethod
        @injector
        def requires_int(cls, *, an_int: int) -> int:
            return cls, an_int

    thing = MyThing()

    assert_wrapped(thing.requires_int)
    assert thing.requires_int() == (MyThing, INT_VALUE)


def test_staticmethod(injector):
    class MyThing(object):
        @staticmethod
        @injector
        def requires_int(*, an_int: int) -> int:
            return an_int

    thing = MyThing()

    assert_wrapped(thing.requires_int)
    assert thing.requires_int() == INT_VALUE
