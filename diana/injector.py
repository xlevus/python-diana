from functools import wraps
from contextlib import contextmanager
from collections import defaultdict, deque

from .scopes import Scope

NONE = Scope(value=None)


class Injector(object):
    """Provides lazy-evaluation dependency injection.

    >>> injector = Injector()
    """
    def __init__(self):
        self.providers = {}
        self.overrides = defaultdict(deque)  # This should be thread-local
        self.aliases = {}

    def provide(self, feature, factory=None, value=None, aliases=(),
                scope=Scope):
        """Registers ``factory`` or ``value`` to be injected against ``feature``

        :param feature: A hashable object to indicate the required dependency.
        :param factory: (Optional) A callable object that provides the
            dependency.
            Factories will take precedence over values.
        :param value: (Optional) The value of the dependency itself.
        :param scope: (Optional) ``Scope`` subclass to define the lifecycle of the
            dependency. If ``factory`` or ``value`` are None, this can also be a
            ``Scope`` instance. Default: :py:class:``diana.scopes.Scope``.
        :param aliases: A tuple of hashable aliases that this dependency can
            also be requested via.
        """

        if feature in self.providers or feature in self.aliases:
            raise RuntimeError("Feature '{}' already provided".format(feature))

        for alias in aliases:
            if (alias in self.providers) or (alias in self.aliases):
                raise RuntimeError("Alias '{}' laready provided".format(alias))

        if factory:
            scope = scope(factory=factory)
        elif value:
            scope = Scope(value=value)

        self.providers[feature] = scope
        for alias in aliases:
            self.aliases[alias] = feature

    @contextmanager
    def override(self, feature, factory=None, value=None, scope=Scope):
        """Context manager to override ``feature`` with ``factory``, ``value`` or
        ``scope``.

        You are not able to provide aditional aliases with ``override``, but
        all previously define aliases will also provide the temporary values.

        .. caution:: This is not thread safe.

        >>> with injector.override('Feature', value='other value'):
        ...     foo()
        ...
        'other_value'

        """
        _scope = scope(factory=factory, value=value)

        self.overrides[feature].append(_scope)
        yield
        self.overrides[feature].pop()

        if not self.overrides[feature]:
            del self.overrides[feature]

    def factory(self, feature, scope=Scope, aliases=()):
        """Convenience factory decorator for ``Injector.provide``.

        :param feature: The feature to provide.
        :param scope: The scope to provide the feature in.
        """
        def _decorator(func):
            self.provide(feature, factory=func, scope=scope, aliases=aliases)
            return func
        return _decorator

    def get(self, feature, soft=False, aliases=True):
        """Get the value of ``feature``.

        :param bool soft: If True, when no provider for ``feature`` can be
            found, None will be returned. (Default: ``False``).
        :param bool aliases: If True, aliases will be searched if no
            provider can be found.
        """
        return self._get_scope(feature, soft, aliases).get()

    def __call__(self, **kwargs):
        """Alias of :py:method:``depends``."""
        return self.depends(**kwargs)

    def depends(self, **kwargs):
        """Wraps a function to inject dependencies keyword arguments.

        If the keyword argument is already provided when the wrapped function
        is called, the argument will not be overwritten.
        """
        return self._decorator(kwargs, False)

    def soft(self, **kwargs):
        """Wraps a function to softly inject dependencies as keyword arguments.
        If a dependency provider can not be found, the value passed into the
        keyword argument will be ``None``.

        Like :py:func:`depends`, already passed in keyword arguments will not
        be overwritten.
        """
        return self._decorator(kwargs, True)

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
                raise RuntimeError("No ")

        return _scope

    def _decorator(self, kwargs, soft):
        def _dec(func):
            @wraps(func)
            def _inner(*func_args, **func_kwargs):
                for kwarg in kwargs:
                    if kwarg not in func_kwargs:
                        dependency = kwargs[kwarg]
                        value = self.get(dependency, soft)
                        func_kwargs[kwarg] = value
                return func(*func_args, **func_kwargs)
            return _inner
        return _dec
