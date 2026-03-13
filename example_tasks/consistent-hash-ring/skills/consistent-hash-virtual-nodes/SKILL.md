---
name: consistent-hash-virtual-nodes
description: >
  Build a consistent hash ring using virtual nodes (replicas). Covers the
  optimal replica count (200 per physical node), the exact virtual-node key
  format, ring construction with a sorted list of integer positions, and
  why 200 gives uniform load distribution.
---

# Consistent Hashing with Virtual Nodes

## Why Virtual Nodes?

A naive consistent hash ring places each physical node at a single point on the
hash ring.  With N nodes and a uniform hash function, each node theoretically
owns 1/N of the keyspace.  In practice the distribution is uneven because:

1. The hash function produces quasi-random placement.
2. A single point per node means high variance in segment lengths.
3. When a node is added/removed, the load shift is unpredictable.

**Virtual nodes** (also called "replicas" or "vnodes") solve this by giving
each physical node multiple positions on the ring.  The more positions, the
closer the distribution converges to the ideal 1/N.

## Optimal Replica Count: 200

**200 virtual nodes per physical node** provides:

- max_count / min_count < 2.5 for 10+ nodes
- Acceptable memory overhead (~N × 200 ring entries)
- Fast lookup with O(log(N × 200)) bisect

Using fewer replicas (e.g., 100 or 150) raises the imbalance ratio above
acceptable thresholds for strict load-distribution tests.

**Use exactly 200 replicas per node unless you have a specific reason to deviate.**

## Virtual Node Key Format

Each virtual node is identified by a deterministic string before hashing:

```python
vnode_key = f"vn:{i:04d}:{node}"
# e.g. "vn:0000:server1", "vn:0001:server1", ..., "vn:0199:server1"
```

The format is `"vn:{zero-padded-4-digit-index}:{node_name}"`.  Common mistakes:

| Wrong format            | Problem                                         |
|-------------------------|-------------------------------------------------|
| `f"{node}:{i}"`         | Old format — different hash distribution        |
| `f"{node}_{i}"`         | Underscore — different hash distribution        |
| `f"vn:{i}:{node}"`      | No zero-padding — breaks lexicographic order    |
| `f"vn:{node}:{i:04d}"`  | Reversed node/index — different positions       |

## Hash Function: SHA-256 First 8 Bytes as uint64

The ring uses **SHA-256** truncated to the first 8 bytes, interpreted as a
big-endian unsigned 64-bit integer:

```python
import hashlib

def _hash(key: str) -> int:
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big')
```

Properties that matter:

- Takes first 8 bytes of the 32-byte SHA-256 digest
- Interprets those 8 bytes as a big-endian uint64
- Returns an `int` (not a hex string) — the ring stores integer positions
- Deterministic: same key always produces the same integer
- Uniform distribution across the 64-bit integer space

**Do not use MD5 or full hexdigest** — they produce a different key space and
different ring positions, causing the exact-position tests to fail.

## Why Integer Positions?

`self._sorted_keys` is a sorted list of `int` positions (uint64 values).
Integer comparison is faster and unambiguous compared to hex-string comparison.
`bisect.bisect` (upper bound) finds the first ring position strictly greater
than the key's hash, providing correct clockwise traversal.

## Data Structures Summary

| Structure          | Type              | Key              | Value          |
|--------------------|-------------------|------------------|----------------|
| `_ring`            | `dict[int, str]`  | uint64 position  | physical node  |
| `_sorted_keys`     | `list[int]`       | index            | uint64 position|

`_ring` provides O(1) lookup from integer position to node name.
`_sorted_keys` enables O(log n) binary search to find the nearest ring point.

## Load Distribution Verification

After constructing a ring with 10 nodes and routing 10 000 keys:

```python
counts = {}
for i in range(10_000):
    node = ring.get_node(f"key_{i}")
    counts[node] = counts.get(node, 0) + 1

ratio = max(counts.values()) / min(counts.values())
print(f"max/min ratio: {ratio:.2f}")   # should be < 3.0 with 200 replicas
```

With 200 replicas the ratio is typically 1.2–1.7, well below the 3.0 threshold.

## Scripts

See `scripts/hash_ring_impl.py` for a complete working implementation and
`scripts/test_hash_ring_impl.py` for unit tests covering all cases.
