from diana.module import Module, provider, provides


def test_register():
    class MyModule(Module):
        pass

    def p_int(module) -> int:
        return 1

    def p_str(module):
        return "string"

    MyModule.register(p_int)
    MyModule.register(p_str, str)


def test_provider():
    class MyModule(Module):
        @provider
        def p_int(self) -> int:
            return 1

        @provides(str)
        def p_str(self):
            return "string"

        @provider
        async def async_p_int(self) -> int:
            return 2

        @provides(str)
        async def async_p_str(self):
            return "string"

    assert MyModule.providers == {
        int: MyModule.p_int,
        str: MyModule.p_str,
    }

    assert MyModule.async_providers == {
        int: MyModule.async_p_int,
        str: MyModule.async_p_str,
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

    assert MyModule.providers == {str: AModule.p_str, int: MyModule.p_int}

    assert MyModule.async_providers == {int: MyModule.p_async_int}


def test_decorator():
    class MyModule(Module):
        pass

    @MyModule.provider
    def p_int(module) -> int:
        return 1

    @MyModule.provides(str)
    def p_str(module):
        return "string"

    @MyModule.provider
    async def async_p_int(module) -> int:
        return 2

    @MyModule.provider
    async def async_p_str(module) -> str:
        return "string"

    assert MyModule.providers == {
        int: p_int,
        str: p_str,
    }

    assert MyModule.async_providers == {
        int: async_p_int,
        str: async_p_str,
    }
