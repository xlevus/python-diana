import pytest
from mock import Mock



def test_inject_value(injector):
    dependency = object()
    value = Mock()

    injector.provide(dependency, value=value)

    @injector(fish=dependency)
    def inner(fish):
        assert fish == value

    inner()


def test_inject_factory(injector):
    dependency = object()
    factory = Mock()

    injector.provide(dependency, factory=factory)

    @injector(fish=dependency)
    def inner(fish):
        factory.assert_called_once_with()
        assert fish == factory()

    inner()


def test_inject_aliases(injector):
    dependency = object()
    value = Mock()

    injector.provide(dependency, value=value, aliases=('fish',))

    @injector(fish='fish')
    def inner(fish):
        assert fish == value

    inner()


def test_no_provider(injector):
    dependency = object()
    value = Mock()

    @injector(fish=dependency)
    def inner(fish):
        assert fish == value

    with pytest.raises(RuntimeError) as excinfo:
        inner()


def test_no_provider_soft(injector):
    dependency = object()

    @injector.soft(fish=dependency)
    def inner(fish):
        assert fish is None

    inner()


def test_context(injector):
    dependency = object()
    factory = Mock()
    override_value = Mock()

    injector.provide(dependency, factory)

    @injector(fish=dependency)
    def inner(fish):
        assert fish == override_value
        assert not factory.called

    with injector.override(dependency, value=override_value):
        inner()


def test_duplicate_provider(injector):
    dependency = object()
    factory = Mock()
    value = Mock()

    injector.provide(dependency, factory=factory)

    with pytest.raises(RuntimeError) as excinfo:
        injector.provide(dependency, value=value)


def test_duplicate_aliases(injector):
    dependency_a = object()
    dependency_b = object()

    factory = Mock()

    injector.provide(dependency_a, factory=factory, aliases=('dependency',))
    with pytest.raises(RuntimeError) as excinfo:
        injector.provide(dependency_b, factory=factory, aliases=('dependency',))
