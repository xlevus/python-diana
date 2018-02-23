import inspect
import functools
import asyncio
import typing as t

from .module import Module


FuncType = t.Callable[..., t.Any]
Decorator = t.Callable[[FuncType], FuncType]


class NoProvider(RuntimeError):
    pass


class Injector(object):
    # modules: t.List[Module]
    # providers: SyncProviderMap
    # async_providers: AsyncProviderMap

    def __init__(self,
                 _sync_dep_klass: t.Type['Dependency'] = None,
                 _async_dep_klass: t.Type['Dependency'] = None):
        self.modules = []
        self.providers = {}
        self.async_providers = {}

        self._sync_dep = _sync_dep_klass or Dependencies
        self._async_dep = _async_dep_klass or AsyncDependencies

    def load(self, *modules: Module):
        """Load the given modules in the provided order.

        Any providers in the modules will take precedence over
        any already loaded providers.
        """
        for module in modules:
            module.load(self)
            self._load_module(module)

    def unload(self, *modules: Module) -> None:
        """Unload the given modules.

        If the module is not loaded, nothing will happen.

        Any providers that have been superceded by providers in the
        unloaded module will be reinstated.
        """
        keep = self.modules[:]
        self.modules = []

        self.providers = {}
        self.async_providers = {}

        for m in keep:
            if m in modules:
                m.unload(self)
                continue
            self._load_module(m)

    def _load_module(self, module: Module) -> None:
        self.modules.append(module)
        for feature, provider in module.providers.items():
            self.providers[feature] = (module, provider)

        for feature, provider in module.async_providers.items():
            self.async_providers[feature] = (module, provider)

    def wrap_dependent(self, func: FuncType) -> FuncType:
        """Wrap a function to have it's dependencies injected.

        The returning function will have a `__dependencies__` attribute
        used to manage dependencies and parameters for the wrapped function.

        Note: This does not specify which dependencies to inject.
        """
        if hasattr(func, '__dependencies__'):
            return func

        if asyncio.iscoroutinefunction(func):
            klass = self._async_dep
        else:
            klass = self._sync_dep

        injected = klass(self, func)

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            return injected.call_injected(*args, **kwargs)

        wrapped.__dependencies__ = injected

        return wrapped

    def __call__(self, func: FuncType) -> FuncType:
        """Wrap a function and attempt to discover it's dependencies by
        inspecting the annotations on kwarg-only arguments.

        >>>
        >>> @injector
        >>> def my_func(*, a_frob: Frob):
        >>>     assert isinstance(a_frob, Frob)
        >>>
        """
        func = self.wrap_dependent(func)
        func.__dependencies__.inspect_dependencies()
        return func

    def inject(self, **mapping) -> Decorator:
        """Wrap a function and specify which dependencies to inject on which
        kwargs.

        >>>
        >>> @injector.inject(a_frob: Frob)
        >>> def my_func(a_frob):
        >>>     assert isinstance(a_frob, Frob)
        >>>
        """
        def wrapper(func: FuncType) -> FuncType:
            func = self.wrap_dependent(func)
            for kwarg, feature in mapping.items():
                func.__dependencies__.add_dependency(kwarg, feature)
            return func
        return wrapper

    def param(self, kwarg, __feature=None, **params) -> Decorator:
        """Specify parameters to pass to the dependencies provider.

        >>>
        >>> @injector
        >>> @injector.param('a_frob', frobulation='high')
        >>> def my_func(a_frob: Frob):
        >>>     assert a_frob.frobulation == 'high'
        >>>

        You can also specify the dependency type as an optional second
        argument.

        >>>
        >>> @injector.param('a_frob', Frob, frobulation='high')
        >>> def my_func(a_frob):
        >>>     assert a_frob.frobulation == 'high'
        >>>
        """
        def wrapper(func: FuncType) -> FuncType:
            func = self.wrap_dependent(func)
            if __feature:
                func.__dependencies__.add_dependency(kwarg, __feature)
            func.__dependencies__.add_params(kwarg, params)
            return func
        return wrapper

    def get(self, feature, params=None):
        """Get the resolved dependency for `feature`."""
        params = params or {}

        provider_map = self.providers
        if feature not in provider_map:
            raise NoProvider('No provider for {!r}'.format(feature))
        module, provider = provider_map[feature]
        return provider(module, **params)

    def get_async(self, feature, params):
        """Get the resolved async dependency for `feature`."""
        provider_map = self.async_providers
        if feature not in provider_map:
            raise NoProvider('No provider for {!r}'.format(feature))
        module, provider = provider_map[feature]
        return provider(module, **params)


class Dependencies(object):
    """Container class to manage dependencies for an injected function.
    """

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
            if kwarg in called_kwargs:
                # Dependency already provided explicitly
                continue
            params = self.dependency_params.get(kwarg, {})
            output[kwarg] = self.injector.get(feature, params)

        return output

    def call_injected(self, *args, **kwargs) -> t.Any:
        kwargs.update(self.resolve_dependencies(kwargs))
        return self.func(*args, **kwargs)


class AsyncDependencies(Dependencies):
    """Container class to manage dependencies for an injected async function.
    """

    async def resolve_dependencies(self, called_kwargs):
        output = {}
        futures = {}

        for kwarg, feature in self.dependencies.items():
            if kwarg in called_kwargs:
                continue

            params = self.dependency_params.get(kwarg, {})
            try:
                futures[kwarg] = self.injector.get_async(feature, params)
            except NoProvider:
                output[kwarg] = self.injector.get(feature, params)

        for k, v in futures.items():
            output[k] = await v

        return output

    async def call_injected(self, *args, **kwargs) -> t.Any:
        kwargs.update(await self.resolve_dependencies(kwargs))
        return (await self.func(*args, **kwargs))
