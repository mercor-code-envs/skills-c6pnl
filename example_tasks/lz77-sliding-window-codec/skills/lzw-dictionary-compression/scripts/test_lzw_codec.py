"""Tests for LZW codec."""
import pytest
from lzw_codec import encode_lzw, decode_lzw


def test_empty():
    assert encode_lzw("") == []
    assert decode_lzw([]) == ""


def test_single_char():
    codes = encode_lzw("a")
    assert codes == [ord('a')]
    assert decode_lzw(codes) == "a"


def test_roundtrip_simple():
    for s in ["abcdef", "aaabbb", "abababab", "hello world"]:
        assert decode_lzw(encode_lzw(s)) == s


def test_compression():
    """Repeated patterns should result in fewer codes than characters."""
    s = "abababababab"
    codes = encode_lzw(s)
    assert len(codes) < len(s)


def test_roundtrip_long():
    s = "the quick brown fox " * 10
    assert decode_lzw(encode_lzw(s)) == s


if __name__ == "__main__":
    import sys
    exit_code = pytest.main([__file__, "-rA"])
    sys.exit(exit_code)
