"""Unit tests for jump_hash.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from jump_hash import jump_hash, string_to_int64, JumpHashRouter


def test_jump_hash_range():
    for n in range(1, 20):
        for key_int in range(100):
            idx = jump_hash(key_int, n)
            assert 0 <= idx < n


def test_jump_hash_deterministic():
    for _ in range(3):
        assert jump_hash(42, 10) == jump_hash(42, 10)


def test_single_bucket():
    for key in range(100):
        assert jump_hash(key, 1) == 0


def test_router_empty():
    r = JumpHashRouter()
    assert r.get_node("key") is None


def test_router_single_node():
    r = JumpHashRouter(nodes=["only"])
    for i in range(50):
        assert r.get_node(f"k{i}") == "only"


def test_router_deterministic():
    r = JumpHashRouter(nodes=["a", "b", "c"])
    keys = [f"key_{i}" for i in range(100)]
    r1 = [r.get_node(k) for k in keys]
    r2 = [r.get_node(k) for k in keys]
    assert r1 == r2


def test_router_distribution():
    r = JumpHashRouter(nodes=[f"node{i}" for i in range(10)])
    counts: dict[str, int] = {}
    for i in range(10_000):
        n = r.get_node(f"key_{i}")
        counts[n] = counts.get(n, 0) + 1
    ratio = max(counts.values()) / min(counts.values())
    assert ratio < 2.0


def test_string_to_int64():
    v = string_to_int64("test")
    assert isinstance(v, int)
    assert 0 <= v < 2**64


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)
