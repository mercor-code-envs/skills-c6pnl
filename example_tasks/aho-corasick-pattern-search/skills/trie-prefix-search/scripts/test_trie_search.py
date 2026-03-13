"""Unit tests for plain Trie prefix search."""
import sys
import pytest
from trie_search import Trie


@pytest.fixture
def populated_trie():
    t = Trie()
    for word in ["apple", "app", "application", "apply", "banana", "band", "bandana"]:
        t.insert(word)
    return t


def test_search_exact_match(populated_trie):
    assert populated_trie.search("app") is True
    assert populated_trie.search("apple") is True


def test_search_not_in_trie(populated_trie):
    assert populated_trie.search("ap") is False
    assert populated_trie.search("banan") is False


def test_starts_with_true(populated_trie):
    assert populated_trie.starts_with("app") is True
    assert populated_trie.starts_with("ban") is True


def test_starts_with_false(populated_trie):
    assert populated_trie.starts_with("xyz") is False


def test_words_with_prefix_app(populated_trie):
    words = populated_trie.words_with_prefix("app")
    assert set(words) == {"app", "apple", "application", "apply"}


def test_words_with_prefix_band(populated_trie):
    words = populated_trie.words_with_prefix("band")
    assert set(words) == {"band", "bandana"}


def test_words_with_prefix_no_match(populated_trie):
    assert populated_trie.words_with_prefix("xyz") == []


def test_empty_trie():
    t = Trie()
    assert t.search("hello") is False
    assert t.starts_with("he") is False
    assert t.words_with_prefix("he") == []


def test_insert_and_search_empty_string():
    t = Trie()
    t.insert("")
    assert t.search("") is True


def test_words_with_full_word_as_prefix(populated_trie):
    # "app" is both a word and a prefix of "apple" etc.
    words = populated_trie.words_with_prefix("app")
    assert "app" in words
    assert "apple" in words


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)
