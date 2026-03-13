"""
Ketama consistent hash ring — libketama-compatible implementation.
Uses host:port:shard key format and 160 virtual nodes per server (40 groups × 4 points).
"""
import hashlib
import bisect
import struct


class KetamaRing:
    """
    Ketama-compatible consistent hash ring for memcached.

    Key format: f"{host}:{port}:{i}" for i in range(40), then 4 hash points
    are extracted per MD5 digest → 160 virtual nodes per server total.
    """

    def __init__(self, servers: list[str] = None) -> None:
        self._ring: dict[int, str] = {}
        self._sorted_keys: list[int] = []
        for server in (servers or []):
            self.add_server(server)

    def _points(self, server: str) -> list[tuple[int, str]]:
        """Generate all 160 (hash_point, server) tuples for a server."""
        points = []
        for i in range(40):
            key_str = f"{server}:{i}"
            md5_bytes = hashlib.md5(key_str.encode()).digest()
            for j in range(4):
                point = struct.unpack(">I", md5_bytes[j * 4:(j + 1) * 4])[0]
                points.append((point, server))
        return points

    def add_server(self, server: str) -> None:
        for point, srv in self._points(server):
            self._ring[point] = srv
            bisect.insort(self._sorted_keys, point)

    def remove_server(self, server: str) -> None:
        for point, _ in self._points(server):
            if point in self._ring and self._ring[point] == server:
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

    def get_servers(self) -> list[str]:
        return list(set(self._ring.values()))

    def virtual_node_count(self, server: str) -> int:
        return sum(1 for v in self._ring.values() if v == server)


if __name__ == "__main__":
    servers = ["cache1:11211", "cache2:11211", "cache3:11211"]
    ring = KetamaRing(servers=servers)
    print(f"Virtual nodes per server: {ring.virtual_node_count('cache1:11211')}")

    counts: dict[str, int] = {}
    for i in range(9000):
        srv = ring.get_server(f"mykey:{i}")
        counts[srv] = counts.get(srv, 0) + 1
    print("Distribution:")
    for srv, count in sorted(counts.items()):
        print(f"  {srv}: {count}")
