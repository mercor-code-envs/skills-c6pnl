"""Tests for RLE codec."""
import pytest
from rle_codec import encode_rle, decode_rle, encode_rle_bytes, decode_rle_bytes


def test_empty():
    assert encode_rle("") == []
    assert decode_rle([]) == ""


def test_single_char():
    assert encode_rle("a") == [(1, "a")]
    assert decode_rle([(1, "a")]) == "a"


def test_run_of_same():
    assert encode_rle("aaaa") == [(4, "a")]


def test_multiple_runs():
    tokens = encode_rle("aaabbbcc")
    assert tokens == [(3, "a"), (3, "b"), (2, "c")]
    assert decode_rle(tokens) == "aaabbbcc"


def test_no_repetition():
    tokens = encode_rle("abc")
    assert tokens == [(1, "a"), (1, "b"), (1, "c")]


def test_roundtrip():
    for s in ["aaabbbcc", "xyzzzz", "a", "abcdef"]:
        assert decode_rle(encode_rle(s)) == s


def test_bytes_roundtrip():
    for s in ["aaabbbcc", "hello", "a" * 50]:
        assert decode_rle_bytes(encode_rle_bytes(s)) == s


if __name__ == "__main__":
    import sys
    exit_code = pytest.main([__file__, "-rA"])
    sys.exit(exit_code)
