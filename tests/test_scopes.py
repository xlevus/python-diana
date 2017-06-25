from mock import Mock
from diana import scopes


def test_const(injector):
    call_check = Mock(return_value=None)

    @injector.factory('Feature', scope=scopes.Const)
    def factory():
        return call_check()

    assert injector.get('Feature') == None
    assert injector.get('Feature') == None

    call_check.assert_called_once_with()


def test_func(injector):
    call_check = Mock(return_value=None)

    @injector.factory('Feature', scope=scopes.Func)
    def factory():
        return call_check()

    @injector(feat='Feature')
    def func_a(feat):
        assert feat == None

    @injector(feat='Feature')
    def func_b(feat):
        assert feat == None

    func_a()
    func_a()
    func_b()
    func_b()

    assert call_check.call_count == 2
