A distributed caching layer needs to assign cache keys to servers in a way that minimizes redistribution when servers are added or removed. Initial cache servers are listed in `/app/input_files/servers.txt`.

A scaffold file is provided at `/app/input_files/cache_router.py`. Complete the implementation and place the finished file at `/app/cache_router.py`.

Requirements:
- `get_node(key)` must consistently return the same server for the same key
- When a node is added or removed, only the minimum necessary keys should remap
- The ring must support dynamic node addition and removal
- Load must be reasonably balanced across all nodes
- `get_node` returns None when the ring is empty