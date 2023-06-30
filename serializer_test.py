import serializer
import pytest


def test_varint():
    with pytest.raises(serializer.SerializeError):
        serializer._varint_encode(-1)

    cases = [
        (0, 1),
        (100, 1),
        (1000, 2),
        (20000, 3),
        (10000000, 4),
    ]

    for n, size in cases:
        b = serializer._varint_encode(n)
        assert len(b) == size
        n1, s1 = serializer._varint_decode(b)
        assert n1 == n
        assert s1 == size

def test_serealize():
    cases = [
        None,
        b'', b'a', b'ab', b'abc', b'abcd',
        '', 'a',  'ab',  'abc',  'abcd',
        True, False,
        0, 100, 1000, 20000, 10000000, 2 ** 32,
        -0, -100, -1000, -20000, -10000000, -2 ** 32,
        0.0, 100.0,  10000.0,  200000.0,  100000000.0, 2 ** 32 * 1.0,
        -0.0, -100.0,  -10000.0,  -200000.0,  -100000000.0, -2 ** 32 * 1.0,
        (), (None, b'a', 'ab', True, 10000, -2**32, 1.0, -2.0, ('b', 1), [1, ('c', None), {}], {'a': 1, 'b': 2, 3: 4}),
        [], [None, b'a', 'ab', True, 10000, -2**32, 1.0, -2.0, ('b', 1), [1, ('c', None), {}], {'a': 1, 'b': 2, 3: 4}],
        {}, {'a': None, 'b': b'a', 'c': 'ab', 'd': True, 'e': 10000, 'f': -2**32, 'g': 1.0, 'h': -2.0, 'i': ('b', 1), 'j': [1, ('c', None), {}], 'k': {'a': 1, 'b': 2, 3: 4}},
    ]

    for n in cases:
        print('=====>', n)
        b = serializer.serialize(n)
        n1, s1 = serializer.deserialize(b)
        assert n1 == n
