import logging
import inspect
import typing as t
import functools
from contextlib import contextmanager
from collections import deque

logger = logging.getLogger(__name__)


T = t.TypeVar('T')

Wrappable = t.Callable[..., T]
Provider = t.Callable[..., t.Any]
ProviderMap = t.Dict[t.Any, Provider]
DependencyMap = t.Dict[str, inspect.Parameter]


class NoProvider(RuntimeError):
    pass


class NoDependencies(RuntimeError):
    pass


class Module(object):
    @property
    def providers(self) -> t.Generator[t.Tuple[t.Type, Provider], None, None]:
        for name, func in inspect.getmembers(self):
            if not name.startswith('provide_'):
                continue

            signature = inspect.signature(func)
            yield (
                signature.return_annotation,
                func)


class ModuleContext(object):
    modules: t.List[Module]
    _providers: ProviderMap

    def __init__(self, modules: t.Sequence[Module]) -> None:
        self.modules = []
        self._providers = {}

        self.load(*modules)

    def load(self, *modules: Module) -> None:
        self.modules.extend(modules)

    def clone(self) -> 'ModuleContext':
        return ModuleContext(self.modules)

    @property
    def providers(self) -> ProviderMap:
        if not self._providers:
            for module in self.modules:
                for feature, provider in module.providers:
                    if feature in self._providers:
                        logger.warn(
                            'Feature {!r} was provided by {!r} '
                            'now being provided by {!r}'.format(
                                feature,
                                self._providers[feature],
                                provider))

                    self._providers[feature] = provider
        return self._providers


class Injector(object):
    context_stack: t.Deque[ModuleContext]

    def __init__(self, modules: t.Sequence[Module] = ()) -> None:
        self.context_stack = deque([ModuleContext(modules)])

    @property
    def context(self) -> ModuleContext:
        return self.context_stack[-1]

    @property
    def providers(self) -> ProviderMap:
        return self.context.providers

    def load(self, *modules) -> None:
        self.context_stack[0].load(*modules)

    def get(self, dependency: t.Type):
        try:
            provider = self.providers[dependency]
            return self.provide_call(
                provider,
                self.get_dependencies(provider, False),
                (),
                {})

        except KeyError:
            raise NoProvider('No provider found for {!r}'.format(dependency))

    def get_dependencies(self,
                         func: Wrappable,
                         strict: bool = True) -> DependencyMap:
        signature = inspect.signature(func)
        deps = {key: param
                for key, param in signature.parameters.items()
                if param.kind == inspect.Parameter.KEYWORD_ONLY}

        if not deps and strict:
            raise NoDependencies(
                'Function {!r} has no keyword-only arguments.'.format(func))

        return deps

    def provide_call(self,
                     func: Wrappable,
                     dependencies: t.Optional[DependencyMap],
                     args: t.Tuple,
                     kwargs: t.Dict[str, t.Any]) -> T:
        if dependencies is None:
            dependencies = self.get_dependencies(func)

        for key, param in dependencies.items():
            if key in kwargs:
                # Kwarg already provided
                continue

            if param.annotation == inspect.Parameter.empty:
                logger.debug("No annotation for {!r}".format(param))

            try:
                value = self.get(param.annotation)
            except NoProvider:
                if param.default != inspect.Parameter.empty:
                    value = param.default
                else:
                    raise

            kwargs[key] = value

        return func(*args, **kwargs)

    def wrap_func(self,
                  func: Wrappable,
                  explicit: t.Dict[str, t.Any]) -> Wrappable:
        deps = self.get_dependencies(func)

        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            return self.provide_call(func, deps, args, kwargs)

        return _wrapper

    def __call__(self, func: Wrappable = None, **kwargs: t.Any):
        if func is None:
            return functools.partial(self.__call__, **kwargs)
        return self.wrap_func(func, kwargs)

    @contextmanager
    def override(self, *modules: Module):
        new_ctx = self.context.clone()
        new_ctx.load(*modules)
        self.context_stack.append(new_ctx)
        yield new_ctx
        assert self.context_stack.pop() == new_ctx
