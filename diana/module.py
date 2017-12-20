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


def mark_provides(func: FeatureProvider, feature: Feature) -> None:
    func.__provides__ = feature


def provider(func: FeatureProvider) -> FeatureProvider:
    signature = inspect.signature(func)
    mark_provides(func, signature.return_annotation)
    return func


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
        provider(func)
        if asyncio.iscoroutinefunction(func):
            cls.async_providers[func.__provides__] = func
        else:
            cls.providers[func.__provides__] = func
        return func