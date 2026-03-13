"""Tests for LZ77 token format utilities."""
import struct
import pytest
from lz77_tokens import (
    emit_token, read_token, tokens_from_bytes,
    is_literal_token, describe_token,
    WINDOW_SIZE, LOOKAHEAD_SIZE,
)


def test_constants():
    assert WINDOW_SIZE == 255
    assert LOOKAHEAD_SIZE == 15


def test_emit_literal_token():
    result = bytearray()
    emit_token(result, 0, 0, ord('a'))
    assert bytes(result) == bytes([0, 0, ord('a')])


def test_emit_backref_token():
    result = bytearray()
    emit_token(result, 3, 5, ord('x'))
    assert bytes(result) == bytes([3, 5, ord('x')])


def test_emit_multiple_tokens():
    result = bytearray()
    emit_token(result, 0, 0, ord('h'))
    emit_token(result, 0, 0, ord('i'))
    assert len(result) == 6
    assert result[2] == ord('h')
    assert result[5] == ord('i')


def test_emit_end_of_string_token():
    """next_char = 0 signals end of string."""
    result = bytearray()
    emit_token(result, 1, 3, 0)
    assert bytes(result) == bytes([1, 3, 0])


def test_read_token():
    data = bytes([5, 10, ord('z')])
    assert read_token(data, 0) == (5, 10, ord('z'))


def test_tokens_from_bytes_single():
    data = bytes([0, 0, ord('a')])
    assert tokens_from_bytes(data) == [(0, 0, ord('a'))]


def test_tokens_from_bytes_multiple():
    data = bytes([0, 0, ord('a'), 1, 2, ord('b')])
    tokens = tokens_from_bytes(data)
    assert tokens == [(0, 0, ord('a')), (1, 2, ord('b'))]


def test_tokens_from_bytes_invalid_length():
    with pytest.raises(ValueError):
        tokens_from_bytes(bytes([0, 0]))  # only 2 bytes, not multiple of 3


def test_is_literal_token():
    assert is_literal_token(0, 0) is True
    assert is_literal_token(1, 0) is False
    assert is_literal_token(0, 1) is False
    assert is_literal_token(3, 5) is False


def test_describe_token_literal():
    desc = describe_token(0, 0, ord('x'))
    assert 'literal' in desc
    assert 'x' in desc


def test_describe_token_backref():
    desc = describe_token(4, 7, ord('a'))
    assert 'backref' in desc
    assert 'offset=4' in desc
    assert 'length=7' in desc


def test_emit_boundary_values():
    result = bytearray()
    emit_token(result, 255, 15, 255)
    assert bytes(result) == bytes([255, 15, 255])


def test_emit_out_of_range_offset():
    result = bytearray()
    with pytest.raises(ValueError):
        emit_token(result, 256, 0, ord('a'))


def test_emit_out_of_range_length():
    result = bytearray()
    with pytest.raises(ValueError):
        emit_token(result, 0, 16, ord('a'))


if __name__ == "__main__":
    import sys
    exit_code = pytest.main([__file__, "-rA"])
    sys.exit(exit_code)
