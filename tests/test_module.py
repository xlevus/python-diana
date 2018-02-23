from diana.module import Module, provider


def test_provider():
    class MyModule(Module):
        @provider
        def p_int(self) -> int:
            return 1

        @provider
        async def async_p_int(self) -> int:
            return 2

    assert MyModule.providers == {
        int: MyModule.p_int
    }

    assert MyModule.async_providers == {
        int: MyModule.async_p_int
    }


def test_inheritance():
    class AModule(Module):
        @provider
        def p_int(self) -> int:
            return 1

        @provider
        async def async_p_int(self) -> int:
            return 1

        @provider
        def p_str(self) -> str:
            return "1"

    class MyModule(AModule):
        @provider
        def p_int(self) -> int:
            return 2

        @provider
        async def p_async_int(self) -> int:
            return 2

    assert MyModule.providers == {
        str: AModule.p_str,
        int: MyModule.p_int
    }

    assert MyModule.async_providers == {
        int: MyModule.p_async_int
    }


def test_decorator():
    class MyModule(Module):
        pass

    @MyModule.provider
    def p_int(module) -> int:
        return 1

    @MyModule.provider
    async def async_p_int(module) -> int:
        return 2

    assert MyModule.providers == {
        int: p_int
    }

    assert MyModule.async_providers == {
        int: async_p_int
    }
