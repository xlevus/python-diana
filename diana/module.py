import inspect
import asyncio
import typing as t


Feature = t.TypeVar('Feature')
SyncFeatureProvider = t.Callable[..., Feature]
AsyncFeatureProvider = t.Callable[..., t.Awaitable[Feature]]
FeatureProvider = t.Union[SyncFeatureProvider, AsyncFeatureProvider]

SyncProviderMap = t.Dict[Feature, SyncFeatureProvider]
AsyncProviderMap = t.Dict[Feature, AsyncFeatureProvider]

FuncType = t.Callable[..., t.Any]
F = t.TypeVar('F', bound=FuncType)

if t.TYPE_CHECKING:
    from .injector import Injector  # noqa


def mark_provides(func: FeatureProvider, feature: Feature) -> None:
    func.__provides__ = feature


def provider(func: FeatureProvider) -> FeatureProvider:
    signature = inspect.signature(func)
    mark_provides(func, signature.return_annotation)
    return func


def provides(feature: Feature):
    def _decorator(func: FeatureProvider) -> FeatureProvider:
        mark_provides(func, feature)
        return func
    return _decorator


class ModuleMeta(type):
    def __new__(mcls, name, bases, attrs):
        providers = {}
        async_providers = {}

        for base in bases:
            if isinstance(base, mcls):
                providers.update(base.providers)
                async_providers.update(async_providers)

        for attr in attrs.values():
            if hasattr(attr, '__provides__'):
                if asyncio.iscoroutinefunction(attr):
                    async_providers[attr.__provides__] = attr
                else:
                    providers[attr.__provides__] = attr

        attrs['providers'] = providers
        attrs['async_providers'] = async_providers

        return super().__new__(mcls, name, bases, attrs)


class Module(metaclass=ModuleMeta):
    # providers: SyncProviderMap
    # async_providers: AsyncProviderMap

    @classmethod
    def provider(cls, func: FeatureProvider) -> FeatureProvider:
        cls.register(func)
        return func

    @classmethod
    def provides(cls, feature: Feature):
        def _decorator(func: FeatureProvider) -> FeatureProvider:
            cls.register(func, feature)
            return func
        return _decorator

    @classmethod
    def register(cls,
                 func: FeatureProvider,
                 feature: t.Optional[Feature]=None) -> None:
        """Register `func` to be a provider for `feature`.

        If `feature` is `None`, the feature's return annotation will be
        inspected."""

        if feature:
            mark_provides(func, feature)
        else:
            provider(func)

        if asyncio.iscoroutinefunction(func):
            cls.async_providers[func.__provides__] = func
        else:
            cls.providers[func.__provides__] = func

    def load(self, injector: 'Injector'):
        pass

    def unload(self, injector: 'Injector'):
        pass
