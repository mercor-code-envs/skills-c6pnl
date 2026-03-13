"""Tests for sliding window compression codec."""
import sys
import random
import pytest

sys.path.insert(0, "/app")
from compressor import encode, decode, WINDOW_SIZE, LOOKAHEAD_SIZE


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def test_constants_defined():
    """WINDOW_SIZE and LOOKAHEAD_SIZE must have correct values."""
    assert WINDOW_SIZE == 255
    assert LOOKAHEAD_SIZE == 15


# ---------------------------------------------------------------------------
# Empty and trivial inputs
# ---------------------------------------------------------------------------

def test_empty_string_encode():
    assert encode("") == b""


def test_empty_string_decode():
    assert decode(b"") == ""


def test_single_char_encode():
    """Single character 'a' must encode to exactly 3 bytes: (0, 0, ord('a'))."""
    result = encode("a")
    assert result == bytes([0, 0, ord('a')])


def test_single_char_roundtrip():
    assert decode(encode("a")) == "a"


def test_single_char_z():
    result = encode("z")
    assert result == bytes([0, 0, ord('z')])


# ---------------------------------------------------------------------------
# All-literal encoding (no repeated patterns)
# ---------------------------------------------------------------------------

def test_abc_all_literals():
    """'abc' has no repeated chars — all tokens must be (0, 0, char) literals."""
    compressed = encode("abc")
    assert len(compressed) == 9  # 3 tokens × 3 bytes
    tokens = [(compressed[i], compressed[i + 1], compressed[i + 2])
              for i in range(0, len(compressed), 3)]
    for offset, length, char in tokens:
        assert offset == 0
        assert length == 0
    assert decode(compressed) == "abc"


def test_all_different_chars_no_backrefs():
    """A string with all unique characters should encode as all literals."""
    s = "abcdefghij"
    compressed = encode(s)
    tokens = [(compressed[i], compressed[i + 1], compressed[i + 2])
              for i in range(0, len(compressed), 3)]
    for offset, length, _ in tokens:
        assert offset == 0
        assert length == 0
    assert decode(compressed) == s


# ---------------------------------------------------------------------------
# Round-trip correctness
# ---------------------------------------------------------------------------

def test_roundtrip_hello_world():
    s = "hello world"
    assert decode(encode(s)) == s


def test_roundtrip_abcabc():
    assert decode(encode("abcabc")) == "abcabc"


def test_roundtrip_aaaa():
    assert decode(encode("aaaa")) == "aaaa"


def test_roundtrip_long_sentence():
    s = "the quick brown fox jumps over the lazy dog"
    assert decode(encode(s)) == s


def test_roundtrip_repeated_phrase():
    s = "abcdef" * 20
    assert decode(encode(s)) == s


def test_roundtrip_random_with_repetitions():
    """Random string over a small alphabet — high chance of back-references."""
    random.seed(12345)
    s = "".join(random.choices("abcde", k=500))
    assert decode(encode(s)) == s


def test_roundtrip_longer_random():
    random.seed(99999)
    s = "".join(random.choices("abcdefghij", k=1000))
    assert decode(encode(s)) == s


# ---------------------------------------------------------------------------
# Back-reference presence
# ---------------------------------------------------------------------------

def test_abcabc_has_backreference():
    """Second 'abc' in 'abcabc' must use a back-reference token (offset > 0)."""
    compressed = encode("abcabc")
    tokens = [(compressed[i], compressed[i + 1], compressed[i + 2])
              for i in range(0, len(compressed), 3)]
    has_backref = any(offset > 0 for offset, _, _ in tokens)
    assert has_backref, "Expected at least one back-reference token for 'abcabc'"


def test_repeated_phrase_has_backreferences():
    """Repeated pattern must produce tokens with offset > 0."""
    compressed = encode("hello hello hello")
    tokens = [(compressed[i], compressed[i + 1], compressed[i + 2])
              for i in range(0, len(compressed), 3)]
    has_backref = any(offset > 0 for offset, _, _ in tokens)
    assert has_backref


# ---------------------------------------------------------------------------
# Compression ratio (repetitive input must be smaller)
# ---------------------------------------------------------------------------

def test_aaaa_compresses():
    """'aaaa' must compress to fewer than 12 bytes (4 literals × 3 bytes)."""
    compressed = encode("aaaa")
    assert len(compressed) < 12
    assert decode(compressed) == "aaaa"


def test_long_repetition_compresses():
    """'a' * 100 must compress to much fewer than 300 bytes."""
    compressed = encode("a" * 100)
    assert len(compressed) < 50, f"Expected < 50 bytes, got {len(compressed)}"
    assert decode(compressed) == "a" * 100


def test_repetitive_input_smaller_than_raw():
    """For repetitive input, compressed size must be less than len(data) * 3."""
    s = "abcdefgh" * 30
    compressed = encode(s)
    assert len(compressed) < len(s) * 3
    assert decode(compressed) == s


# ---------------------------------------------------------------------------
# Overlapping back-references
# ---------------------------------------------------------------------------

def test_overlapping_aaaaaa():
    """'aaaaaa' must use offset=1 back-reference (overlapping copy)."""
    compressed = encode("aaaaaa")
    tokens = [(compressed[i], compressed[i + 1], compressed[i + 2])
              for i in range(0, len(compressed), 3)]
    # At least one token should have offset=1 and length > 1
    has_overlap = any(offset == 1 and length > 1 for offset, length, _ in tokens)
    assert has_overlap, f"Expected offset=1 overlapping token, got tokens: {tokens}"
    assert decode(compressed) == "aaaaaa"


def test_overlapping_roundtrip_many_a():
    """'a' * 50 must round-trip correctly using overlapping copies."""
    s = "a" * 50
    assert decode(encode(s)) == s


def test_overlapping_ababab():
    """'ababababab' — offset=2, overlapping repeat."""
    s = "ababababab"
    assert decode(encode(s)) == s


# ---------------------------------------------------------------------------
# Token byte format
# ---------------------------------------------------------------------------

def test_token_byte_count_multiple_of_3():
    """Compressed output must have a byte count that is a multiple of 3."""
    for s in ["a", "ab", "abc", "abcd", "hello", "aaaaaa"]:
        compressed = encode(s)
        assert len(compressed) % 3 == 0, (
            f"Compressed length {len(compressed)} is not a multiple of 3 for {s!r}"
        )


def test_single_char_exact_bytes():
    """Every single printable ASCII char must encode to exactly 3 bytes."""
    for ch in "abcxyzABCXYZ0123456789":
        compressed = encode(ch)
        assert len(compressed) == 3
        assert compressed[0] == 0   # offset
        assert compressed[1] == 0   # length
        assert compressed[2] == ord(ch)  # next_char


# ---------------------------------------------------------------------------
# Decode correctness for known byte sequences
# ---------------------------------------------------------------------------

def test_decode_literal_tokens():
    """Manually constructed all-literal compressed bytes must decode correctly."""
    # Token (0, 0, 'h'), (0, 0, 'i') → "hi"
    compressed = bytes([0, 0, ord('h'), 0, 0, ord('i')])
    assert decode(compressed) == "hi"


def test_decode_backref_token():
    """Manually constructed back-reference must decode correctly."""
    # (0, 0, 'a') → emit 'a'; then (1, 2, 'b') → copy 2 from offset 1 = 'aa', then 'b' → "aaab"
    compressed = bytes([0, 0, ord('a'), 1, 2, ord('b')])
    assert decode(compressed) == "aaab"


def test_decode_overlapping_token():
    """Back-reference where length > offset (overlapping) must work."""
    # (0, 0, 'a') → 'a'; (1, 4, 0) → copy 4 from offset 1 starting at pos 0 = 'aaaa', no literal
    # Result: 'aaaaa'
    compressed = bytes([0, 0, ord('a'), 1, 4, 0])
    assert decode(compressed) == "aaaaa"


# ---------------------------------------------------------------------------
# End-of-string edge cases
# ---------------------------------------------------------------------------

def test_two_char_roundtrip():
    assert decode(encode("ab")) == "ab"


def test_repeated_two_char():
    assert decode(encode("abab")) == "abab"


def test_string_ending_in_repeated_chars():
    for s in ["abcaa", "xyzz", "hellooo", "abaab"]:
        assert decode(encode(s)) == s


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-rA"])
    print("pass" if exit_code == 0 else "fail")
    sys.exit(exit_code)
