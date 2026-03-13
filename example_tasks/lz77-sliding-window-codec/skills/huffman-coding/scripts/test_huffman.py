"""Tests for Huffman coding."""
import pytest
from huffman import build_tree, build_codes, encode_huffman, decode_huffman


def test_empty():
    bits, codes = encode_huffman("")
    assert bits == ""
    assert codes == {}
    assert decode_huffman("", {}) == ""


def test_single_char():
    bits, codes = encode_huffman("a")
    assert 'a' in codes
    assert decode_huffman(bits, codes) == "a"


def test_roundtrip_simple():
    s = "abracadabra"
    bits, codes = encode_huffman(s)
    assert decode_huffman(bits, codes) == s


def test_frequent_char_shorter_code():
    """Most frequent character should get the shortest code."""
    s = "aaaaabbc"
    bits, codes = encode_huffman(s)
    assert len(codes['a']) <= len(codes['b'])
    assert len(codes['b']) <= len(codes['c'])


def test_roundtrip_long():
    s = "the quick brown fox jumps over the lazy dog" * 5
    bits, codes = encode_huffman(s)
    assert decode_huffman(bits, codes) == s


def test_compression_ratio():
    """Huffman should use fewer bits than 8 bits/char for repetitive input."""
    s = "a" * 100 + "b" * 50
    bits, codes = encode_huffman(s)
    raw_bits = len(s) * 8
    assert len(bits) < raw_bits


if __name__ == "__main__":
    import sys
    exit_code = pytest.main([__file__, "-rA"])
    sys.exit(exit_code)
