NO_VALUE = object()


class Scope(object):
    """Default scope.

    If dependency is provided via a factory, the factory is
    called on each invocation.

    :param factory: A factory method.
    :param value: A constant value."""
    def __init__(self, feature, factory=None, value=None):
        self.factory = factory
        self.value = value

    def get(self, dependent):
        if self.factory:
            return self.factory()
        return self.value


class Const(Scope):
    """Lazy constant scope.

    Factory will be invocated on initial dependency requirement.
    Subsequent requirements will return the same value."""
    def __init__(self, feature, factory=None, value=NO_VALUE):
        self.factory = factory
        self.value = value

    def get(self, dependent):
        if self.value is NO_VALUE:
            self.value = self.factory()
        return self.value


class Func(Scope):
    """Scope that instantiates one instance per dependent function."""
    def __init__(self, feature, factory):
        self.dependents = {}
        self.factory = factory

    def get(self, dependent):
        if dependent not in self.dependents:
            value = self.factory()
            self.dependents[dependent] = value
        return self.dependents[dependent]
