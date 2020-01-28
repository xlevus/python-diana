import inspect
import asyncio
import typing as t

from .util import isasync


Feature = t.TypeVar("Feature")
SyncFeatureProvider = t.Callable[..., Feature]
AsyncFeatureProvider = t.Callable[..., t.Awaitable[Feature]]
FeatureProvider = t.Union[SyncFeatureProvider, AsyncFeatureProvider]

SyncProviderMap = t.Dict[Feature, SyncFeatureProvider]
AsyncProviderMap = t.Dict[Feature, AsyncFeatureProvider]

FuncType = t.Callable[..., t.Any]
F = t.TypeVar("F", bound=FuncType)

if t.TYPE_CHECKING:
    from .injector import Injector  # noqa


def mark_provides(
    func: FeatureProvider, feature: Feature, context: bool = False
) -> None:
    func.__provides__ = feature
    func.__contextprovider__ = context
    func.__asyncproider__ = isasync(func)


def provider(func: FeatureProvider, context: bool = False) -> FeatureProvider:
    signature = inspect.signature(func)
    mark_provides(func, signature.return_annotation, context)
    return func


def contextprovider(func: FeatureProvider) -> FeatureProvider:
    signature = inspect.signature(func)
    mark_provides(func, signature.return_annotation, True)
    return func


def provides(feature: Feature, context=False):
    def _decorator(func: FeatureProvider) -> FeatureProvider:
        mark_provides(func, feature, context)
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
            if hasattr(attr, "__provides__"):
                if attr.__asyncproider__:
                    async_providers[attr.__provides__] = attr
                else:
                    providers[attr.__provides__] = attr

        attrs["providers"] = providers
        attrs["async_providers"] = async_providers

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
    def register(
        cls,
        func: FeatureProvider,
        feature: t.Optional[Feature] = None,
        context: bool = False,
    ) -> None:
        """Register `func` to be a provider for `feature`.

        If `feature` is `None`, the feature's return annotation will be
        inspected."""

        if feature:
            mark_provides(func, feature, context)
        else:
            provider(func, context)

        if isasync(func):
            cls.async_providers[func.__provides__] = func
        else:
            cls.providers[func.__provides__] = func

    def load(self, injector: "Injector"):
        pass

    def unload(self, injector: "Injector"):
        pass
