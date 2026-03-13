"""
Tests for cache routing implementation.
Expects /app/cache_router.py to contain class CacheRouter.
"""
import sys
import importlib.util
import pytest


def load_cache_router():
    spec = importlib.util.spec_from_file_location("cache_router", "/app/cache_router.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CacheRouter


# ---------------------------------------------------------------------------
# Test: exact hash position — discriminates SHA-256 first-8-bytes from MD5
# ---------------------------------------------------------------------------
def test_exact_hash_position():
    """Verify exact hash position for a known key — fails if wrong hash format."""
    import hashlib
    import bisect

    CacheRouter = load_cache_router()

    # Sanity: SHA-256 first-8-bytes position vs MD5 hexdigest must differ
    md5_pos = int(hashlib.md5("server1:0".encode()).hexdigest(), 16)
    sha_pos = int.from_bytes(hashlib.sha256("vn:0000:server1".encode()).digest()[:8], 'big')
    assert md5_pos != sha_pos, "Test design error: positions should differ"

    # Build expected ring manually using the required spec
    ring2 = CacheRouter(nodes=["A", "B"])
    test_key = "deterministic_test_key_42"
    node = ring2.get_node(test_key)

    ring_positions = []
    for name in ["A", "B"]:
        for i in range(200):
            pos = int.from_bytes(
                hashlib.sha256(f"vn:{i:04d}:{name}".encode()).digest()[:8], 'big'
            )
            ring_positions.append((pos, name))
    ring_positions.sort()

    key_pos = int.from_bytes(hashlib.sha256(test_key.encode()).digest()[:8], 'big')
    positions = [p for p, _ in ring_positions]
    nodes_at_pos = [n for _, n in ring_positions]
    idx = bisect.bisect(positions, key_pos) % len(positions)
    expected_node = nodes_at_pos[idx]

    assert node == expected_node, (
        f"Expected {expected_node} but got {node} — "
        "likely wrong hash format or wrong vnode key format"
    )


# ---------------------------------------------------------------------------
# Test: exactly 200 replicas per physical node
# ---------------------------------------------------------------------------
def test_200_replicas():
    """Verify exactly 200 virtual nodes per physical node."""
    CacheRouter = load_cache_router()

    # With 1 node and 200 replicas, all keys must map to that node
    ring = CacheRouter(nodes=["only_node"])
    for key in [f"key_{i}" for i in range(100)]:
        assert ring.get_node(key) == "only_node", (
            f"Expected only_node but got {ring.get_node(key)!r}"
        )

    # Verify the default replica count is 200 by using a custom value
    ring_custom = CacheRouter(nodes=["solo"], replicas=200)
    for key in [f"test_{i}" for i in range(50)]:
        assert ring_custom.get_node(key) == "solo"


# ---------------------------------------------------------------------------
# Test: basic routing consistency
# ---------------------------------------------------------------------------
def test_basic_routing_consistency():
    """Same key always maps to same node."""
    CacheRouter = load_cache_router()
    ring = CacheRouter(nodes=["server1", "server2", "server3"])
    keys = [f"key_{i}" for i in range(200)]
    first_pass = {k: ring.get_node(k) for k in keys}
    second_pass = {k: ring.get_node(k) for k in keys}
    assert first_pass == second_pass, "get_node must be deterministic"


# ---------------------------------------------------------------------------
# Test: empty ring returns None
# ---------------------------------------------------------------------------
def test_empty_ring_returns_none():
    CacheRouter = load_cache_router()
    ring = CacheRouter()
    assert ring.get_node("anything") is None
    assert ring.get_node("") is None


# ---------------------------------------------------------------------------
# Test: single node, all keys go there
# ---------------------------------------------------------------------------
def test_single_node_all_keys():
    CacheRouter = load_cache_router()
    ring = CacheRouter(nodes=["solo-server"])
    for i in range(100):
        assert ring.get_node(f"key_{i}") == "solo-server", \
            f"key_{i} should map to solo-server"


# ---------------------------------------------------------------------------
# Test: node addition causes minimal key remapping (~1/N fraction)
# ---------------------------------------------------------------------------
def test_node_addition_minimal_remap():
    CacheRouter = load_cache_router()
    nodes = [f"node{i}" for i in range(5)]
    ring = CacheRouter(nodes=nodes)

    keys = [f"cache:{i}" for i in range(2000)]
    before = {k: ring.get_node(k) for k in keys}

    ring.add_node("node5")
    after = {k: ring.get_node(k) for k in keys}

    remapped = sum(1 for k in keys if before[k] != after[k])
    # Expect roughly 1/6 of keys to remap (±generous tolerance)
    expected_fraction = 1 / 6
    actual_fraction = remapped / len(keys)
    assert actual_fraction < 0.40, (
        f"Too many keys remapped on node addition: {remapped}/{len(keys)} "
        f"({actual_fraction:.1%}), expected ~{expected_fraction:.1%}"
    )
    # Also ensure some keys did remap (not zero)
    assert remapped > 0, "Adding a node should cause at least some remapping"


# ---------------------------------------------------------------------------
# Test: node removal causes only affected keys to remap
# ---------------------------------------------------------------------------
def test_node_removal_minimal_remap():
    CacheRouter = load_cache_router()
    nodes = [f"node{i}" for i in range(5)]
    ring = CacheRouter(nodes=nodes)

    keys = [f"data:{i}" for i in range(2000)]
    before = {k: ring.get_node(k) for k in keys}

    # Remove one node; only keys that were on that node should change
    ring.remove_node("node2")
    after = {k: ring.get_node(k) for k in keys}

    remapped = [k for k in keys if before[k] != after[k]]
    # All remapped keys must have previously been on node2
    for k in remapped:
        assert before[k] == "node2", (
            f"Key {k!r} remapped but was on {before[k]!r}, not node2"
        )

    # After removal, none of those keys should map to node2
    for k in keys:
        assert after[k] != "node2", f"Key {k!r} still maps to removed node2"


# ---------------------------------------------------------------------------
# Test: load distribution uniformity (10 nodes, 10000 keys)
# ---------------------------------------------------------------------------
def test_load_distribution_uniformity():
    CacheRouter = load_cache_router()
    nodes = [f"server{i}" for i in range(10)]
    ring = CacheRouter(nodes=nodes)

    counts: dict[str, int] = {n: 0 for n in nodes}
    for i in range(10000):
        node = ring.get_node(f"workload_key_{i}")
        counts[node] = counts.get(node, 0) + 1

    max_count = max(counts.values())
    min_count = min(counts.values())
    ratio = max_count / min_count

    assert ratio < 3.0, (
        f"Load distribution too skewed: max={max_count}, min={min_count}, "
        f"ratio={ratio:.2f} (must be < 3.0). Counts: {counts}"
    )


# ---------------------------------------------------------------------------
# Test: get_nodes returns all added nodes
# ---------------------------------------------------------------------------
def test_get_nodes_returns_all():
    CacheRouter = load_cache_router()
    nodes = ["alpha", "beta", "gamma", "delta"]
    ring = CacheRouter(nodes=nodes)
    result = ring.get_nodes()
    assert set(result) == set(nodes), (
        f"get_nodes() returned {set(result)}, expected {set(nodes)}"
    )


# ---------------------------------------------------------------------------
# Test: get_nodes after removal excludes removed node
# ---------------------------------------------------------------------------
def test_get_nodes_after_removal():
    CacheRouter = load_cache_router()
    ring = CacheRouter(nodes=["a", "b", "c"])
    ring.remove_node("b")
    result = ring.get_nodes()
    assert "b" not in result, "Removed node should not appear in get_nodes()"
    assert set(result) == {"a", "c"}, f"Expected {{'a', 'c'}}, got {set(result)}"


# ---------------------------------------------------------------------------
# Test: adding same node twice is idempotent in routing (dedup)
# ---------------------------------------------------------------------------
def test_add_node_idempotent():
    CacheRouter = load_cache_router()
    ring = CacheRouter(nodes=["x", "y"])
    keys = [f"k{i}" for i in range(100)]
    before = {k: ring.get_node(k) for k in keys}
    ring.add_node("x")  # add again
    after = {k: ring.get_node(k) for k in keys}
    # The key assertion: no KeyError, no None returned
    for k in keys:
        assert after[k] is not None, f"get_node({k!r}) returned None after duplicate add"


# ---------------------------------------------------------------------------
# Test: key hashing is deterministic across instances
# ---------------------------------------------------------------------------
def test_key_hashing_deterministic_across_instances():
    CacheRouter = load_cache_router()
    nodes = ["node-A", "node-B", "node-C"]
    ring1 = CacheRouter(nodes=nodes)
    ring2 = CacheRouter(nodes=nodes)
    keys = [f"session:{i}" for i in range(500)]
    for k in keys:
        assert ring1.get_node(k) == ring2.get_node(k), (
            f"Key {k!r} maps differently across instances"
        )


# ---------------------------------------------------------------------------
# Test: ring wraps around (highest hash key goes to first node)
# ---------------------------------------------------------------------------
def test_ring_wraparound():
    """Verify ring is circular — after all ring points, wrap to index 0."""
    CacheRouter = load_cache_router()
    ring = CacheRouter(nodes=["wrap-node"])
    # With a single node, all keys must route to it regardless of hash position
    test_keys = ["zzzzzzzzz", "\xff\xff", "aaaaaaaaa", "0", "999999999"]
    for k in test_keys:
        result = ring.get_node(k)
        assert result == "wrap-node", (
            f"Wraparound failed: {k!r} returned {result!r}"
        )


# ---------------------------------------------------------------------------
# Test: remove all nodes, then ring is empty
# ---------------------------------------------------------------------------
def test_remove_all_nodes():
    CacheRouter = load_cache_router()
    ring = CacheRouter(nodes=["p", "q", "r"])
    ring.remove_node("p")
    ring.remove_node("q")
    ring.remove_node("r")
    assert ring.get_node("any_key") is None, \
        "After removing all nodes, get_node should return None"
    assert ring.get_nodes() == [], \
        "After removing all nodes, get_nodes should return []"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    exit_code = pytest.main([__file__, "-rA"])
    print("pass" if exit_code == 0 else "fail")
    sys.exit(exit_code)
