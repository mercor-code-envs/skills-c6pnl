"""
Jump consistent hash implementation (Lamping & Veach, 2014).
Maps keys to buckets in O(ln N) with no data structures.
"""
import hashlib
import struct


def jump_hash(key: int, num_buckets: int) -> int:
    """
    Map a 64-bit integer key to a bucket in [0, num_buckets).
    """
    b = -1
    j = 0
    while j < num_buckets:
        b = j
        key = (key * 2862933555777941757 + 1) & 0xFFFFFFFFFFFFFFFF
        j = int((b + 1) * (2**31 / ((key >> 33) + 1)))
    return b


def string_to_int64(key: str) -> int:
    """Convert string key to 64-bit integer for jump_hash."""
    digest = hashlib.md5(key.encode()).digest()
    return struct.unpack('<Q', digest[:8])[0]


class JumpHashRouter:
    """
    Node router using jump consistent hash.
    NOTE: Minimal disruption only guaranteed when adding nodes at the end.
    """

    def __init__(self, nodes: list[str] = None) -> None:
        self._nodes: list[str] = list(nodes or [])

    def add_node(self, node: str) -> None:
        """Append node — jump hash is consistent only for append operations."""
        self._nodes.append(node)

    def remove_node(self, node: str) -> None:
        """Remove node. Only safe to remove the last node without reshuffling."""
        if node in self._nodes:
            self._nodes.remove(node)

    def get_node(self, key: str) -> str | None:
        if not self._nodes:
            return None
        idx = jump_hash(string_to_int64(key), len(self._nodes))
        return self._nodes[idx]

    def get_nodes(self) -> list[str]:
        return list(self._nodes)


if __name__ == "__main__":
    router = JumpHashRouter(nodes=[f"shard{i}" for i in range(8)])
    counts: dict[str, int] = {}
    for i in range(8_000):
        node = router.get_node(f"key_{i}")
        counts[node] = counts.get(node, 0) + 1

    print("Jump hash distribution (8k keys, 8 shards):")
    for shard, count in sorted(counts.items()):
        print(f"  {shard}: {count}")
    ratio = max(counts.values()) / min(counts.values())
    print(f"max/min ratio: {ratio:.2f}")
