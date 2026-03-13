"""Unit tests for suffix array construction and pattern search."""
import sys
import pytest
from suffix_array import build_suffix_array, build_lcp, search_pattern


def test_suffix_array_banana():
    sa = build_suffix_array("banana")
    # Expected: [5, 3, 1, 0, 4, 2] → a, ana, anana, banana, na, nana
    assert sa == [5, 3, 1, 0, 4, 2]


def test_suffix_array_single_char():
    sa = build_suffix_array("a")
    assert sa == [0]


def test_lcp_banana():
    text = "banana"
    sa = build_suffix_array(text)
    lcp = build_lcp(text, sa)
    # lcp[0] = 0 by definition; lcp[2] = len(lcp("ana","anana")) = 3
    assert lcp[0] == 0
    assert lcp[2] == 3  # "ana" vs "anana"


def test_search_found():
    text = "banana"
    sa = build_suffix_array(text)
    positions = search_pattern(text, sa, "ana")
    assert sorted(positions) == [1, 3]


def test_search_not_found():
    text = "banana"
    sa = build_suffix_array(text)
    assert search_pattern(text, sa, "xyz") == []


def test_search_empty_pattern():
    text = "hello"
    sa = build_suffix_array(text)
    assert search_pattern(text, sa, "") == []


def test_search_pattern_equals_text():
    text = "hello"
    sa = build_suffix_array(text)
    assert search_pattern(text, sa, "hello") == [0]


def test_search_multiple_occurrences():
    text = "abcabcabc"
    sa = build_suffix_array(text)
    positions = search_pattern(text, sa, "abc")
    assert sorted(positions) == [0, 3, 6]


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)
