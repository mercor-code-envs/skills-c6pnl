---
name: ketama-hash-ring
description: >
  Ketama consistent hash ring as used by libketama and memcached clients.
  Uses MD5 with a host:port:shard key format and 160 virtual nodes per server.
  Different from standard consistent ring hashing in its key format and
  replica count.
---

# Ketama Consistent Hash Ring

## Overview

Ketama is the consistent hash algorithm implemented in **libketama** and used
by memcached clients (libmemcached, pylibmc, spymemcached).  It is based on
consistent ring hashing with virtual nodes but uses a specific key format and
replica count that differs from the generic algorithm.

**Ketama is the standard for memcached clients.**  If you are implementing a
generic consistent hash ring (not tied to memcached), use the standard
`consistent-hash-virtual-nodes` approach instead.

## Ketama Key Format

Ketama identifies virtual nodes with the format:

```python
# Ketama format: "host:port:shard_index"
# where shard_index is computed from the replica group
vnode_key = f"{host}:{port}:{shard}"
```

For a server `cache1:11211` with 40 virtual node groups × 4 hashes per group:

```python
for i in range(40):           # 40 groups
    for j in range(4):        # 4 hashes per group via MD5 bytes
        vnode_key = f"cache1:11211:{i}"
        md5_bytes = hashlib.md5(vnode_key.encode()).digest()
        # Extract 4 hash points from 16-byte MD5 digest
        point = struct.unpack(">I", md5_bytes[j*4:(j+1)*4])[0]
```

This produces 160 virtual nodes per server (40 groups × 4 points), matching
libketama's default.

## The 160-Replica Convention

Libketama uses **160 virtual nodes** per server, derived as 40 server weight
units × 4 hash points per MD5 digest.  This differs from the generic ring's
150-replica convention.

| Library / System       | Replicas per node | Key format               |
|------------------------|-------------------|--------------------------|
| libketama / memcached  | 160               | `host:port:shard` (int)  |
| Generic ring hash      | 150               | `node:i` (string)        |
| Apache Cassandra       | 256               | token range per vnode    |

## Full Ketama Implementation

```python
import hashlib
import bisect
import struct


class KetamaRing:
    def __init__(self, servers: list[str] = None) -> None:
        """
        servers: list of "host:port" strings, e.g. ["cache1:11211"]
        """
        self._ring: dict[int, str] = {}   # int point -> server
        self._sorted_keys: list[int] = []
        for server in (servers or []):
            self.add_server(server)

    def _points(self, server: str) -> list[tuple[int, str]]:
        """Generate 160 (point, server) tuples for one server."""
        points = []
        for i in range(40):
            key = f"{server}:{i}"
            md5 = hashlib.md5(key.encode()).digest()
            for j in range(4):
                point = struct.unpack(">I", md5[j*4:(j+1)*4])[0]
                points.append((point, server))
        return points

    def add_server(self, server: str) -> None:
        for point, srv in self._points(server):
            self._ring[point] = srv
            bisect.insort(self._sorted_keys, point)

    def remove_server(self, server: str) -> None:
        for point, _ in self._points(server):
            if point in self._ring:
                del self._ring[point]
                idx = bisect.bisect_left(self._sorted_keys, point)
                if idx < len(self._sorted_keys) and self._sorted_keys[idx] == point:
                    self._sorted_keys.pop(idx)

    def get_server(self, key: str) -> str | None:
        if not self._ring:
            return None
        h = int(hashlib.md5(key.encode()).hexdigest(), 16) % (2**32)
        idx = bisect.bisect_left(self._sorted_keys, h)
        if idx == len(self._sorted_keys):
            idx = 0
        return self._ring[self._sorted_keys[idx]]
```

## Critical Differences: Ketama vs Generic Ring

1. **Key format**: Ketama uses `f"{host}:{port}:{shard}"` where `shard` is an
   integer counter (0-39), not a sequential virtual node index 0-149.

2. **Hash extraction**: Ketama extracts 4 × 32-bit integers from each MD5
   digest using `struct.unpack(">I", ...)`, placing 4 ring points per MD5.
   Generic ring uses the full hex digest as a string.

3. **Integer ring**: Ketama sorts 32-bit integers; generic sorts hex strings.

4. **Replica count**: 160 (ketama) vs 150 (generic standard).

If you mix these formats — e.g., use ketama's key format with generic's 150
replicas, or vice versa — clients will disagree on key placement.

## Compatibility

Ketama-compatible clients include: libmemcached, pylibmc, spymemcached,
Memcached.Client (PHP), node-memcached.  All produce identical routing for the
same server list.

## Scripts

See `scripts/ketama.py` for the implementation and `scripts/test_ketama.py`
for tests verifying 160 virtual nodes per server and load distribution.
