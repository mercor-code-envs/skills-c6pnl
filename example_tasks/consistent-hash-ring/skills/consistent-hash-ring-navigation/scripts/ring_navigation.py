"""
Demonstrates consistent hash ring navigation: bisect_left with wraparound.
"""
import hashlib
import bisect


class HashRing:
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
        """
        Route a key to a node using bisect_left + wraparound.

        1. Hash the key to a hex digest.
        2. bisect_left finds the first ring point >= key_hash.
        3. If past the end (idx == len), wrap to index 0.
        4. Look up the physical node for that ring point.
        """
        if not self._ring:
            return None
        h = self._hash(key)
        idx = bisect.bisect_left(self._sorted_keys, h)
        if idx == len(self._sorted_keys):
            idx = 0  # wraparound: past last ring point, loop to start
        return self._ring[self._sorted_keys[idx]]

    def get_nodes(self) -> list[str]:
        return list(set(self._ring.values()))

    def debug_lookup(self, key: str) -> None:
        """Show step-by-step navigation for a key."""
        h = self._hash(key)
        idx = bisect.bisect_left(self._sorted_keys, h)
        wrapped = idx == len(self._sorted_keys)
        if wrapped:
            idx = 0
        ring_point = self._sorted_keys[idx]
        node = self._ring[ring_point]
        print(f"key={key!r}")
        print(f"  key_hash = {h}")
        print(f"  ring_point = {ring_point} (index {idx}{'  [WRAPPED]' if wrapped else ''})")
        print(f"  -> node: {node}")


if __name__ == "__main__":
    ring = HashRing(nodes=["web1", "web2", "web3"])
    print("=== Ring Navigation Demo ===\n")

    for key in ["user:1001", "session:abc", "cache:data", "zzzzz"]:
        ring.debug_lookup(key)
        print()

    # Demonstrate minimal remapping on node removal
    keys = [f"req_{i}" for i in range(1000)]
    before = {k: ring.get_node(k) for k in keys}
    ring.remove_node("web2")
    after = {k: ring.get_node(k) for k in keys}
    remapped = [k for k in keys if before[k] != after[k]]
    print(f"Removed web2: {len(remapped)}/1000 keys remapped "
          f"(expected ~333, all from web2)")
    non_web2 = [k for k in remapped if before[k] != "web2"]
    print(f"Keys remapped NOT from web2: {len(non_web2)} (should be 0)")
