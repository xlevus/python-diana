import logging
import inspect
import typing as t
import functools
from contextlib import contextmanager
from collections import deque

logger = logging.getLogger(__name__)


T = t.TypeVar('T')

Wrappable = t.Callable[..., t.Any]
Provider = t.Callable[..., t.Any]
ProviderMap = t.Dict[t.Any, Provider]


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
            return self.providers[dependency]()
        except KeyError:
            raise NoProvider('No provider found for {!r}'.format(dependency))

    def wrap_func(self,
                  func: Wrappable,
                  explicit_bindings: t.Dict[str, t.Any]) -> Wrappable:
        signature = inspect.signature(func)
        deps = {key: param
                for key, param in signature.parameters.items()
                if param.kind == inspect.Parameter.KEYWORD_ONLY}

        if not deps:
            raise NoDependencies(
                'Function {!r} has no keyword-only arguments'.format(func))

        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            for key, param in deps.items():

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
