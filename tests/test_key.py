
from diana import Key


class OtherKey(Key):
    pass


def test_key_equality():
    k1 = Key(1)
    k2 = Key(1)

    assert k1 == k2

    k3 = Key(3)
    assert k1 != k2

    k4 = OtherKey(1)
    assert k1 != k4

    k5 = OtherKey(1)
    assert k4 == k5


def test_key_hash():
    s = {
        Key(1),
        Key(1),
        Key(2),
        OtherKey(1),
        OtherKey(1),
        OtherKey(2),
    }

    assert len(s) == 4
