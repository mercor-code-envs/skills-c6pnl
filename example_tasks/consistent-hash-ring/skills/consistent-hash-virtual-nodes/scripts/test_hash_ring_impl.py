"""Unit tests for hash_ring_impl.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from hash_ring_impl import HashRing


def test_empty_ring():
    ring = HashRing()
    assert ring.get_node("key") is None


def test_single_node():
    ring = HashRing(nodes=["only"])
    for i in range(50):
        assert ring.get_node(f"k{i}") == "only"


def test_deterministic():
    ring = HashRing(nodes=["a", "b", "c"])
    keys = [f"key_{i}" for i in range(100)]
    r1 = {k: ring.get_node(k) for k in keys}
    r2 = {k: ring.get_node(k) for k in keys}
    assert r1 == r2


def test_load_distribution():
    ring = HashRing(nodes=[f"node{i}" for i in range(10)])
    counts: dict[str, int] = {}
    for i in range(10_000):
        n = ring.get_node(f"workload_{i}")
        counts[n] = counts.get(n, 0) + 1
    ratio = max(counts.values()) / min(counts.values())
    assert ratio < 3.0, f"Load ratio {ratio:.2f} exceeds 3.0"


def test_node_count():
    ring = HashRing(nodes=["x", "y", "z"])
    assert len(ring._sorted_keys) == 3 * 150


def test_vnode_key_format():
    """Verify virtual node keys use the canonical 'node:i' format."""
    import hashlib
    ring = HashRing(nodes=["server1"], replicas=3)
    expected_hashes = {
        hashlib.md5(f"server1:{i}".encode()).hexdigest()
        for i in range(3)
    }
    assert expected_hashes.issubset(set(ring._sorted_keys))


def test_remove_node():
    ring = HashRing(nodes=["a", "b"])
    ring.remove_node("b")
    for i in range(100):
        assert ring.get_node(f"k{i}") == "a"


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)
