import asyncio
import typing as t

import pytest

from diana import Injector, Module


Dep1 = t.NewType('Dep1', int)
Dep2 = t.NewType('Dep2', int)


@pytest.fixture
def injector():
    return Injector()


@pytest.fixture(params=[Dep1, Dep2])
def dependency_klass(request):
    return request.param


@pytest.fixture
def dependency_value(dependency_klass):
    return dependency_klass(1)


@pytest.fixture(params=['sync', 'async'])
def dependency_type(request):
    return request.param


@pytest.fixture
def dependency_fn(dependency_type, dependency_klass):
    if dependency_type == 'sync':
        def sync_dependency_fn(*, value: dependency_klass):
            return value
        return sync_dependency_fn

    elif dependency_type == 'async':
        async def async_dependency_fn(*, value: dependency_klass):
            return value
        return async_dependency_fn
    else:
        raise RuntimeError('Unknown dependency type')


@pytest.fixture(params=['decorator', 'typing'])
def injection_method(request):
    return request.param


@pytest.fixture
def dependent(injection_method, dependency_fn, injector, dependency_klass):
    if injection_method == 'typing':
        # @injector
        # def to_wrap(*, value: Dependency):
        #     ...
        return injector(dependency_fn)
    elif injection_method == 'decorator':
        # @injector(value=Dependency)
        # def to_wrap(*, value):
        #     ....
        return injector(value=dependency_klass)(dependency_fn)
    else:
        raise RuntimeError('Unknown injection method')


@pytest.fixture(params=['sync', 'async'])
def provider_type(request):
    return request.param


@pytest.fixture
def provider(provider_type, dependency_klass, dependency_value):
    if provider_type == 'sync':
        class SyncProvider(Module):
            def provide_dep(self) -> dependency_klass:
                return dependency_value
        return SyncProvider
    elif provider_type == 'async':
        class AsyncProvider(Module):
            async def provide_dep(self) -> dependency_klass:
                return dependency_value
        return AsyncProvider
    else:
        raise RuntimeError('Unknown provider type')


@pytest.mark.parametrize(('dependency_type', 'provider_type'), [
    ('sync', 'sync'),
    ('async', 'async'),
    ('async', 'sync'),
    pytest.param('sync', 'async', marks=pytest.mark.xfail(
        reason='Cant provide sync dep with async provider.'))
], indirect=True)
def test_inject(
        injector, provider, dependent, dependency_value,
        dependency_type,
        event_loop):
    injector.load(provider())

    if dependency_type == 'async':
        assert asyncio.iscoroutinefunction(dependent)
        result = event_loop.run_until_complete(dependent())
    else:
        result = dependent()

    assert result == dependency_value
