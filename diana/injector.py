import inspect
import functools
import asyncio
import typing as t

from .module import Module


FuncType = t.Callable[..., t.Any]
F = t.TypeVar('F', bound=FuncType)


class NoProvider(RuntimeError):
    pass


class Injector(object):
    # modules: t.List[Module]
    # providers: SyncProviderMap
    # async_providers: AsyncProviderMap

    def __init__(self):
        self.modules = []
        self.providers = {}
        self.async_providers = {}

    def load_module(self, module: Module) -> None:
        self.modules.append(module)
        for feature, provider in module.providers.items():
            self.providers[feature] = (module, provider)

        for feature, provider in module.async_providers.items():
            self.async_providers[feature] = (module, provider)

    def wrap_dependent(self, func: FuncType) -> 'Dependent':
        if not isinstance(func, Injected):
            if asyncio.iscoroutinefunction(func):
                func = AsyncInjected(self, func)
            else:
                func = Injected(self, func)
        return func

    def __call__(self, func: F) -> F:
        func = self.wrap_dependent(func)
        func.inspect_dependencies()
        return t.cast(F, func)

    def inject(self, **mapping) -> t.Callable[[F], F]:
        def wrapper(func: F) -> F:
            func = self.wrap_dependent(func)
            for kwarg, feature in mapping.items():
                func.add_dependency(kwarg, feature)
            return t.cast(F, func)
        return wrapper

    def param(self, kwarg, **params) -> t.Callable[[F], F]:
        def wrapper(func: F) -> F:
            func = self.wrap_dependent(func)
            func.add_params(kwarg, params)
            return t.cast(F, func)
        return wrapper

    def get(self, feature, params):
        provider_map = self.providers
        if feature not in provider_map:
            raise NoProvider('No provider for {!r}'.format(feature))
        module, provider = provider_map[feature]
        return provider(module, **params)

    def get_async(self, feature, params):
        provider_map = self.async_providers
        if feature not in provider_map:
            raise NoProvider('No provider for {!r}'.format(feature))
        module, provider = provider_map[feature]
        return provider(module, **params)


class Injected(object):
    def __init__(self, injector: Injector, func: FuncType) -> None:
        functools.update_wrapper(self, func)
        self.injector = injector
        self.func = func

        self.dependency_params = {}
        self.dependencies = {}

    def __repr__(self):
        params = ", ".join([
            "{}={!r}".format(k, v)
            for k, v in self.dependency_params
        ])
        return "<injected {self.func.__name__} ({params})>".format(
            self=self, params=params)

    def add_dependency(self, kwarg: str, feature) -> None:
        if kwarg in self.dependencies:
            raise RuntimeError('Dependency for kwarg {!r} exists'.format(
                kwarg))
        self.dependencies[kwarg] = feature

    def add_params(self, kwarg, params):
        self.dependency_params.setdefault(kwarg, {})\
                              .update(params)

    def inspect_dependencies(self):
        signature = inspect.signature(self.func)

        for kwarg, parameter in signature.parameters.items():
            if parameter.kind != inspect.Parameter.KEYWORD_ONLY\
               or parameter.annotation == inspect.Parameter.empty:
                continue

            self.dependencies[kwarg] = parameter.annotation

    def resolve_dependencies(self, called_kwargs):
        output = {}

        for kwarg, feature in self.dependencies.items():
            params = self.dependency_params.get(kwarg, {})
            output[kwarg] = self.injector.get(feature, params)

        return output

    def __call__(self, *args, **kwargs) -> t.Any:
        kwargs.update(self.resolve_dependencies(kwargs))
        return self.func(*args, **kwargs)


class AsyncInjected(Injected):
    async def resolve_dependencies(self, called_kwargs):
        output = {}
        futures = {}

        for kwarg, feature in self.dependencies.items():
            params = self.dependency_params.get(kwarg, {})
            try:
                futures[kwarg] = self.injector.get_async(feature, params)
            except NoProvider:
                output[kwarg] = self.injector.get(feature, params)

        for k, v in futures.items():
            output[k] = await v

        return output

    async def __call__(self, *args, **kwargs) -> t.Any:
        kwargs.update(await self.resolve_dependencies(kwargs))
        return (await self.func(*args, **kwargs))
