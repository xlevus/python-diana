import pytest

import diana



@pytest.fixture
def injector():
    return diana.Injector()
