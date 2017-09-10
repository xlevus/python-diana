import pytest
import typing as t

from diana.injector import Module, Injector, NoProvider, NoDependencies


MyType = t.NewType('MyType', int)
OtherType = t.NewType('OtherType', str)
FrobType = t.NewType('FrobType', int)


class MyModule(Module):
    def provide_mytype(self) -> MyType:
        return MyType(0)

    def provide_othertype(self) -> OtherType:
        return OtherType("other")


class OtherModule(Module):
    def provide_frobtype(self) -> FrobType:
        return FrobType(1)


class TestModule(object):
    def test_get_providers(self):
        m = MyModule()
        assert dict(m.providers) == {
            MyType: m.provide_mytype,
            OtherType: m.provide_othertype
        }


class TestInjector(object):
    @pytest.fixture
    def mymodule(self):
        return MyModule()

    @pytest.fixture
    def othermodule(self):
        return OtherModule()

    @pytest.fixture
    def modules(self, mymodule, othermodule):
        return [mymodule, othermodule]

    @pytest.fixture
    def injector(self, modules):
        return Injector(modules)

    def test_load_modules(self, modules):
        i = Injector()
        i.load(*modules)
        assert i.context.modules == modules

    def test_providers(self, mymodule, othermodule):
        i = Injector()
        i.load(mymodule, othermodule)

        assert i.providers == {
            MyType: mymodule.provide_mytype,
            OtherType: mymodule.provide_othertype,
            FrobType: othermodule.provide_frobtype,
        }

    @pytest.mark.parametrize('feature,expected', [
        (MyType, MyType(0)),
        (OtherType, OtherType('other')),
        (FrobType, FrobType(1)),
        pytest.param(int, 1, marks=pytest.mark.xfail(raises=NoProvider))])
    def test_get(self, injector, feature, expected):
        assert injector.get(feature) == expected

    def test_decorate(self, injector):

        @injector
        def decorated(*, my: MyType, other: OtherType, frob: FrobType):
            return my, other, frob

        assert decorated() == (MyType(0), OtherType('other'), FrobType(1))

    def test_decorate_with_default(self, injector):
        @injector
        def decorated(*, frob: FrobType, foo: int = 100):
            return frob, foo

        assert decorated() == (FrobType(1), 100)

    def test_decorate_no_provider(self, injector):
        @injector
        def decorated(*, foo: int):
            return foo

        with pytest.raises(NoProvider):
            decorated()

    def test_decorate_overridden(self, injector):
        frob = FrobType(10)

        @injector
        def decorated(*, foo: FrobType):
            return foo

        assert decorated(foo=frob) == frob

    def test_decorate_no_kwargs(self, injector):
        with pytest.raises(NoDependencies):
            @injector
            def decorated(foo: FrobType):
                return foo

    def test_override(self, injector):
        @injector
        def frob(*, foo: FrobType):
            return foo

        class NewFrobber(Module):
            def provide_frob(self) -> FrobType:
                return FrobType(200)

        with injector.override(NewFrobber()):
            assert frob() == FrobType(200)

        assert frob() == FrobType(1)
