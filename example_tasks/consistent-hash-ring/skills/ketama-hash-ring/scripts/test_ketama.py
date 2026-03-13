"""Unit tests for ketama.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from ketama import KetamaRing


def test_empty():
    ring = KetamaRing()
    assert ring.get_server("key") is None


def test_single_server():
    ring = KetamaRing(servers=["cache1:11211"])
    for i in range(50):
        assert ring.get_server(f"k{i}") == "cache1:11211"


def test_160_virtual_nodes():
    ring = KetamaRing(servers=["cache1:11211"])
    count = ring.virtual_node_count("cache1:11211")
    assert count == 160, f"Expected 160 virtual nodes, got {count}"


def test_deterministic():
    ring = KetamaRing(servers=["a:1", "b:1", "c:1"])
    keys = [f"key_{i}" for i in range(100)]
    r1 = [ring.get_server(k) for k in keys]
    r2 = [ring.get_server(k) for k in keys]
    assert r1 == r2


def test_remove_server():
    ring = KetamaRing(servers=["a:1", "b:1"])
    ring.remove_server("b:1")
    for i in range(50):
        assert ring.get_server(f"k{i}") == "a:1"


def test_load_distribution():
    servers = [f"cache{i}:11211" for i in range(5)]
    ring = KetamaRing(servers=servers)
    counts: dict[str, int] = {}
    for i in range(5000):
        srv = ring.get_server(f"key_{i}")
        counts[srv] = counts.get(srv, 0) + 1
    ratio = max(counts.values()) / min(counts.values())
    assert ratio < 3.0


if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)
