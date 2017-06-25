

class Key(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<{}({!r})>".format(
            self.__class__.__name__,
            self.name)

    def __eq__(self, other):
        return self.lookup() == other.lookup()

    def __hash__(self):
        return hash(self.lookup())

    def lookup(self):
        return (self.__class__, self.name)
