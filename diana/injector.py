from functools import wraps
from contextlib import contextmanager
from collections import defaultdict, deque


class Scope(object):
    def __init__(self, factory=None, value=None):
        self.factory = factory
        self.value = value

    def get(self):
        if self.factory:
            return self.factory()
        return self.value


NONE = Scope(value=None)


class Injector(object):
    def __init__(self):
        self.providers = {}
        self.overrides = defaultdict(deque)  # This should be thread-local
        self.aliases = {}

    def provide(self, feature, factory=None, value=None, aliases=(),
                scope=Scope):

        if feature in self.providers or feature in self.aliases:
            raise RuntimeError("Feature '{}' already provided".format(feature))

        for alias in aliases:
            if (alias in self.providers) or (alias in self.aliases):
                raise RuntimeError("Alias '{}' laready provided".format(alias))

        _scope = scope(factory=factory, value=value)

        self.providers[feature] = _scope
        for alias in aliases:
            self.aliases[alias] = feature

    @contextmanager
    def override(self, feature, factory=None, value=None, scope=Scope):
        _scope = scope(factory=factory, value=value)

        self.overrides[feature].append(_scope)
        yield
        self.overrides[feature].pop()

        if not self.overrides[feature]:
            del self.overrides[feature]

    def _get_scope(self, feature, soft=False, aliases=True):
        if feature in self.overrides:
            _scope = self.overrides[feature][-1]
        elif feature in self.providers:
            _scope = self.providers[feature]
        elif aliases and feature in self.aliases:
            actual = self.aliases[feature]
            _scope = self._get_scope(actual, soft, False)

        else:
            if soft:
                _scope = NONE
            else:
                raise RuntimeError()

        return _scope

    def get(self, feature, soft=False, aliases=True):
        return self._get_scope(feature, soft, aliases).get()

    def _decorator(self, kwargs, soft):
        def _dec(func):
            @wraps(func)
            def _inner(*func_args, **func_kwargs):
                for kwarg in kwargs:
                    dependency = kwargs[kwarg]
                    value = self.get(dependency, soft)
                    func_kwargs.setdefault(kwarg, value)
                return func(*func_args, **func_kwargs)
            return _inner
        return _dec

    def __call__(self, **kwargs):
        return self._decorator(kwargs, False)

    def soft(self, **kwargs):
        return self._decorator(kwargs, True)
