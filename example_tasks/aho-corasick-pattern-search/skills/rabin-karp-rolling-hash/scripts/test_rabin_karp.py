"""Unit tests for Rabin-Karp rolling hash search."""
import sys
import pytest
from rabin_karp import rabin_karp


def test_basic():
    assert rabin_karp("abcabcabc", "abc") == [0, 3, 6]


def test_no_match():
    assert rabin_karp("hello", "xyz") == []


def test_single_occurrence():
    assert rabin_karp("hello world", "world") == [6]


def test_overlapping():
    assert rabin_karp("aaa", "aa") == [0, 1]


def test_pattern_equals_text():
    assert rabin_karp("abc", "abc") == [0]


def test_empty_pattern():
    assert rabin_karp("hello", "") == []


def test_empty_text():
    assert rabin_karp("", "abc") == []


def test_pattern_longer_than_text():
    assert rabin_karp("ab", "abc") == []


def test_single_char_pattern():
    assert rabin_karp("abcabc", "a") == [0, 3]


def test_returns_sorted():
    result = rabin_karp("xyzxyz", "xyz")
    assert result == sorted(result)


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)
