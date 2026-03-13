"""Tests for LZ77 sliding window search and encode/decode."""
import pytest
from sliding_window import find_longest_match, encode, decode, WINDOW_SIZE, LOOKAHEAD_SIZE


def test_no_match_at_start():
    """First character has empty window — no match."""
    off, length = find_longest_match("abcabc", 0)
    assert off == 0
    assert length == 0


def test_simple_match():
    """'abc' in window matches 'abc' at pos 3."""
    off, length = find_longest_match("abcabc", 3)
    assert off == 3
    assert length == 3


def test_overlapping_match():
    """'a' in window at pos 1 of 'aaaaa' — overlapping match."""
    off, length = find_longest_match("aaaaa", 1)
    assert off == 1
    assert length >= 1  # at least one, up to LOOKAHEAD_SIZE


def test_longest_match_preferred():
    """Among multiple matches, the longest must be chosen."""
    # 'abc' appears at index 0; at pos=6 lookahead is 'abc' → offset=6, length=3
    off, length = find_longest_match("abcxyzabc", 6)
    assert length == 3
    assert off == 6


def test_encode_empty():
    assert encode("") == b""


def test_encode_single_char():
    result = encode("a")
    assert result == bytes([0, 0, ord('a')])


def test_encode_no_repeats():
    compressed = encode("abcde")
    assert len(compressed) == 15  # 5 literals × 3 bytes
    tokens = [(compressed[i], compressed[i+1]) for i in range(0, 15, 3)]
    assert all(off == 0 and ln == 0 for off, ln in tokens)


def test_encode_aaaa_compressed():
    compressed = encode("aaaa")
    assert len(compressed) < 12
    assert decode(compressed) == "aaaa"


def test_encode_overlapping_aaaaaa():
    compressed = encode("aaaaaa")
    tokens = [(compressed[i], compressed[i+1], compressed[i+2])
              for i in range(0, len(compressed), 3)]
    # Must have a token with offset=1 and length > 1
    assert any(off == 1 and ln > 1 for off, ln, _ in tokens)


def test_roundtrip_basic():
    for s in ["a", "ab", "abc", "abcabc", "aaaa", "hello world"]:
        assert decode(encode(s)) == s, f"Round-trip failed for {s!r}"


def test_roundtrip_repetitive():
    s = "abcdef" * 15
    assert decode(encode(s)) == s


def test_decode_literal_only():
    data = bytes([0, 0, ord('h'), 0, 0, ord('i')])
    assert decode(data) == "hi"


def test_decode_backref_overlapping():
    # Emit 'a', then backref offset=1 length=4 next=0 → 'a' + 'aaaa' = 'aaaaa'
    data = bytes([0, 0, ord('a'), 1, 4, 0])
    assert decode(data) == "aaaaa"


def test_window_size_constant():
    assert WINDOW_SIZE == 255


def test_lookahead_size_constant():
    assert LOOKAHEAD_SIZE == 15


if __name__ == "__main__":
    import sys
    exit_code = pytest.main([__file__, "-rA"])
    sys.exit(exit_code)
