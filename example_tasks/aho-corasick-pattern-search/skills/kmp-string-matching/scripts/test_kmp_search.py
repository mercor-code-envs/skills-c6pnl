"""Unit tests for KMP string matching."""
import sys
import pytest
from kmp_search import kmp_search, build_lps


def test_lps_simple():
    assert build_lps("abcabc") == [0, 0, 0, 1, 2, 3]


def test_lps_all_same():
    assert build_lps("aaaa") == [0, 1, 2, 3]


def test_basic_match():
    assert kmp_search("aabxaab", "aab") == [0, 4]


def test_no_match():
    assert kmp_search("hello", "xyz") == []


def test_overlapping():
    assert kmp_search("aaa", "aa") == [0, 1]


def test_pattern_equals_text():
    assert kmp_search("abc", "abc") == [0]


def test_empty_pattern():
    assert kmp_search("hello", "") == []


def test_empty_text():
    assert kmp_search("", "abc") == []


def test_pattern_longer_than_text():
    assert kmp_search("ab", "abc") == []


def test_single_char():
    assert kmp_search("abcabc", "a") == [0, 3]


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)
