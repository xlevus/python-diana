import logging
import typing as t
from functools import wraps
from contextlib import contextmanager
from inspect import Signature, Parameter, getmembers

logger = logging.getLogger(__name__)


T = t.TypeVar('T')


class NoProvider(RuntimeError):
    pass


class NoDependencies(RuntimeError):
    pass


class Module(object):
    @property
    def providers(self) -> t.Generator[t.Tuple[t.Type, t.Any], None, None]:
        for name, func in getmembers(self):
            if not name.startswith('provide_'):
                continue

            signature = Signature.from_function(func)
            yield (
                signature.return_annotation,
                func)


class Injector(object):
    modules: t.List[Module]
    _providers: t.Dict[t.Any, t.Callable]

    def __init__(self, modules: t.Sequence[Module] = ()) -> None:
        self.modules = []
        self._providers = {}

        self.load(*modules)

    def load(self, *modules: Module) -> None:
        self.modules.extend(modules)
        self._providers = {}

    @property
    def providers(self):
        if not self._providers:
            for module in self.modules:
                for feature, provider in module.providers:
                    self._providers[feature] = provider
        return self._providers

    def get(self, feature: t.Type):
        try:
            return self.providers[feature]()
        except KeyError:
            raise NoProvider('No provider found for {!r}'.format(feature))

    def __call__(self, func: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
        signature = Signature.from_function(func)
        deps = {key: param
                for key, param in signature.parameters.items()
                if param.kind == param.KEYWORD_ONLY}

        if not deps:
            raise NoDependencies(
                'Function {!r} has no keyword-only arguments'.format(func))

        @wraps(func)
        def _wrapper(*args, **kwargs):
            for key, param in deps.items():

                if key in kwargs:
                    # Kwarg already provided
                    continue

                if param.annotation == Parameter.empty:
                    logger.debug("No annotation for {!r}".format(param))

                try:
                    value = self.get(param.annotation)
                except NoProvider:
                    if param.default != Parameter.empty:
                        value = param.default
                    else:
                        raise

                kwargs[key] = value

            return func(*args, **kwargs)

        return _wrapper
