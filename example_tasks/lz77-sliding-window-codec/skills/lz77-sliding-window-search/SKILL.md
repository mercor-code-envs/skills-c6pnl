---
name: lz77-sliding-window-search
description: >
  Implements the LZ77 sliding window longest-match search algorithm.
  Covers the overlapping back-reference trick (offset < length), the
  encode() loop with correct position advancement, and the decode()
  loop with one-at-a-time copy for overlap safety.
---

# LZ77 Sliding Window Search

## The Sliding Window

At each encoding position `pos`, we look back up to `WINDOW_SIZE` characters
for the **longest matching prefix** of the lookahead buffer.

```
|<---- WINDOW (up to 255 chars) ---->|<-- LOOKAHEAD (up to 15) -->|
 data[win_start ... pos-1]            data[pos ... pos+14]
                                      ^
                                   current position
```

Key property: the window grows as we advance `pos`. Characters we just
encoded become part of the search window for future tokens.

## Overlapping Copies

LZ77 allows `length > offset` (the match extends past the window boundary
into the lookahead area). This creates **run-length-like** repeats:

**Example**: encoding `"aaaaaa"` at position 1 (window = `"a"`):
- `offset = 1`, `length = 5`
- Copy character at `(pos - 1) + (j % 1)` for j = 0..4 → `"aaaaa"`
- This is valid because we read one character at a time from the growing output

The formula for the source character when copying position `j`:
```
source_index = start + (j % dist)   where dist = pos - start
```

## Longest Match Search

Search **all** positions in the window, not just the first match. Return the
position that gives the **maximum `length`**:

```python
WINDOW_SIZE = 255
LOOKAHEAD_SIZE = 15

def find_longest_match(data: str, pos: int) -> tuple[int, int]:
    """Return (offset, length) of longest match for data[pos:] in the window.

    offset = 0, length = 0 means no match found (emit literal).
    """
    n = len(data)
    win_start = max(0, pos - WINDOW_SIZE)
    best_len = 0
    best_off = 0

    for start in range(win_start, pos):
        length = 0
        dist = pos - start          # distance backwards = offset
        # Overlapping: use modulo to wrap within the matched region
        while (length < LOOKAHEAD_SIZE and
               pos + length < n and
               data[start + (length % dist)] == data[pos + length]):
            length += 1

        if length > best_len:
            best_len = length
            best_off = dist

    return best_off, best_len
```

### Position Advancement

| Situation | advance |
|-----------|---------|
| Match found, next char exists | `best_len + 1` |
| Match goes to end of string | `best_len` |
| No match, char exists | `1` (best_len=0, advance=0+1=1) |

## decode() Back-Reference Copying

Copy back-references **one character at a time** — this naturally handles
overlapping cases where `length > offset`.

**Why `result[start + j]` and NOT `result[start:start+length]`?**

With `offset=1, length=4` and `result=['a']`:
- `start = 0`
- j=0: append `result[0]` = 'a' → result = ['a','a']
- j=1: append `result[1]` = 'a' → result = ['a','a','a']
- j=2: append `result[2]` = 'a' → result = ['a','a','a','a']
- j=3: append `result[3]` = 'a' → result = ['a','a','a','a','a']

A slice copy `result[0:4]` would fail because index 1, 2, 3 don't exist yet.

## Common Mistakes

| Mistake | Symptom |
|---------|---------|
| `result[start:start+length]` in decode | IndexError for overlapping copies |
| Breaking after first match instead of finding longest | Poor compression ratio; may also fail tests |
| Forgetting `% dist` in encode overlap formula | Wrong characters in overlapping region |
| Using `LOOKAHEAD_SIZE + 1` in while condition | Matches 1 char too long; off-by-one |
| Not setting `advance = best_len` at end of string | Infinite loop when last token is a match |
