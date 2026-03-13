"""Tests for delta encoding."""
import pytest
from delta_encode import encode_delta, decode_delta, encode_delta_str, decode_delta_str


def test_empty():
    assert encode_delta([]) == []
    assert decode_delta([]) == []


def test_single_value():
    assert encode_delta([42]) == [42]
    assert decode_delta([42]) == [42]


def test_increasing_sequence():
    values = [10, 12, 15, 15, 20]
    deltas = encode_delta(values)
    assert deltas == [10, 2, 3, 0, 5]
    assert decode_delta(deltas) == values


def test_decreasing_sequence():
    values = [100, 90, 80, 70]
    deltas = encode_delta(values)
    assert deltas == [100, -10, -10, -10]
    assert decode_delta(deltas) == values


def test_roundtrip():
    for values in [[1, 2, 3], [5, 5, 5, 5], [100, 1, 200, 2]]:
        assert decode_delta(encode_delta(values)) == values


def test_str_roundtrip():
    for s in ["abcde", "hello", "aaaaaa"]:
        assert decode_delta_str(encode_delta_str(s)) == s


def test_slowly_varying_compresses():
    """Adjacent values differ by ±1 — deltas are small."""
    values = list(range(100))
    deltas = encode_delta(values)
    # After first value, all deltas are 1
    assert all(d == 1 for d in deltas[1:])


if __name__ == "__main__":
    import sys
    exit_code = pytest.main([__file__, "-rA"])
    sys.exit(exit_code)
