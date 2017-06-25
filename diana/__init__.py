from .injector import Injector, NoProvider, DuplicateProvider  # noqa
from .scopes import Const, Func  # noqa
from .key import Key  # noqa


__version__ = '0.0.4'

injector = Injector()
