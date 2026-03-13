"""
Consistent hash ring implementation using virtual nodes.
Demonstrates 150 replicas per node with MD5 hashing and canonical key format.
"""
import hashlib
import bisect


class HashRing:
    """
    A consistent hash ring using virtual nodes.

    Each physical node is placed at `replicas` (default 150) positions on
    the ring.  Keys are routed to the first ring point >= their hash,
    wrapping around to 0 when past the end.
    """

    def __init__(self, nodes: list[str] = None, replicas: int = 150) -> None:
        self._replicas = replicas
        self._ring: dict[str, str] = {}
        self._sorted_keys: list[str] = []
        for node in (nodes or []):
            self.add_node(node)

    def _hash(self, key: str) -> str:
        return hashlib.md5(key.encode()).hexdigest()

    def add_node(self, node: str) -> None:
        for i in range(self._replicas):
            vnode_key = f"{node}:{i}"
            h = self._hash(vnode_key)
            self._ring[h] = node
            bisect.insort(self._sorted_keys, h)

    def remove_node(self, node: str) -> None:
        for i in range(self._replicas):
            vnode_key = f"{node}:{i}"
            h = self._hash(vnode_key)
            if h in self._ring:
                del self._ring[h]
                idx = bisect.bisect_left(self._sorted_keys, h)
                if idx < len(self._sorted_keys) and self._sorted_keys[idx] == h:
                    self._sorted_keys.pop(idx)

    def get_node(self, key: str) -> str | None:
        if not self._ring:
            return None
        h = self._hash(key)
        idx = bisect.bisect_left(self._sorted_keys, h)
        if idx == len(self._sorted_keys):
            idx = 0
        return self._ring[self._sorted_keys[idx]]

    def get_nodes(self) -> list[str]:
        return list(set(self._ring.values()))


if __name__ == "__main__":
    ring = HashRing(nodes=["server1", "server2", "server3"])
    counts: dict[str, int] = {}
    for i in range(10_000):
        node = ring.get_node(f"key_{i}")
        counts[node] = counts.get(node, 0) + 1

    print("Load distribution (10k keys, 3 nodes, 150 replicas):")
    for node, count in sorted(counts.items()):
        bar = "#" * (count // 50)
        print(f"  {node}: {count:5d}  {bar}")
    ratio = max(counts.values()) / min(counts.values())
    print(f"max/min ratio: {ratio:.2f}")
