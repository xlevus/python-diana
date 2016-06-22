
class Scope(object):
    """Default scope.

    If dependency is provided via a factory, the factory is
    called on each invocation.

    :param factory: A factory method.
    :param value: A constant value."""
    def __init__(self, factory=None, value=None):
        self.factory = factory
        self.value = value

    def get(self):
        if self.factory:
            return self.factory()
        return self.value


class Const(Scope):
    """Lazy constant scope.

    Factory will be invocated on initial dependency requirement.
    Subsequent requirements will return the same value."""
    def get(self):
        if not self.value:
            self.value = self.factory()
        return self.value
