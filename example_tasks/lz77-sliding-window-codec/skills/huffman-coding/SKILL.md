---
name: huffman-coding
description: >
  Huffman coding assigns shorter binary codes to more frequent characters
  and longer codes to rare characters. Uses a priority queue to build an
  optimal prefix-free code tree. Achieves entropy-optimal compression for
  independent symbol distributions.
---

# Huffman Coding

Huffman coding is a frequency-based compression algorithm that assigns
variable-length binary codes based on symbol frequencies.

## Algorithm Overview

1. Count character frequencies in the input
2. Build a min-heap (priority queue) of (frequency, char) nodes
3. Repeatedly merge the two lowest-frequency nodes until one tree remains
4. Traverse the tree to assign codes: left = '0', right = '1'
5. Encode: replace each character with its binary code
6. Decode: traverse the tree using the encoded bits

## Implementation

```python
import heapq
from collections import Counter

def build_huffman_tree(data: str):
    freq = Counter(data)
    heap = [[weight, [char, ""]] for char, weight in freq.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        lo = heapq.heappop(heap)
        hi = heapq.heappop(heap)
        for pair in lo[1:]:
            pair[1] = '0' + pair[1]
        for pair in hi[1:]:
            pair[1] = '1' + pair[1]
        heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])

    return sorted(heapq.heappop(heap)[1:], key=lambda p: (len(p[-1]), p))
```

## Key Difference from LZ77

Huffman coding works on individual symbol frequencies — it does not use
a sliding window or back-references to previous data positions. It is
complementary to LZ77 (used together in DEFLATE/gzip).

## Relationship to LZ77 Sliding Window Compression

Huffman coding and LZ77 are complementary compression stages, often combined (e.g., DEFLATE = LZ77 + Huffman). Huffman eliminates symbol frequency redundancy; LZ77 eliminates repetition redundancy via sliding window back-references.

| Huffman | LZ77 |
|---------|------|
| Frequency-based code assignment | Sliding window back-reference search |
| Variable-length symbol codes | Fixed-size 3-byte tokens: (offset, length, next_char) |
| No concept of window or lookahead | WINDOW_SIZE=255 characters; lookahead buffer for match |
| Encodes individual symbols | Encodes back-references: offset=distance, length=match_length |
| Decodes from bit stream | Decodes by copying length bytes from current_pos-offset; overlapping supported |

In LZ77, a token is always 3 bytes: offset (how far back the match starts), length (how many chars to copy), and next_char (the literal following the match). When offset=0 and length=0, next_char is a literal. The encode function does a greedy longest-match search over the sliding window; the decode function copies byte-at-a-time to support overlapping back-references where offset < length.

Huffman alone doesn't exploit repetition across the text. LZ77 alone doesn't exploit symbol frequency imbalance. DEFLATE applies LZ77 first (back-references reduce repetition), then Huffman (codes the remaining token stream by frequency).

## Integration Example: DEFLATE-Style LZ77 + Huffman Pipeline

```python
import struct, heapq
from collections import Counter

WINDOW_SIZE = 255
LOOKAHEAD_SIZE = 15

# ── LZ77 encode: produce fixed 3-byte tokens (offset, length, next_char) ──
def lz77_encode(data: str) -> bytes:
    """Each token is 3 bytes: (offset:1B, length:1B, next_char:1B).
    Literal: (0, 0, char). Back-reference: (offset, length, next_char).
    Sliding window size = WINDOW_SIZE = 255. Overlapping matches supported.
    """
    result = bytearray()
    pos, n = 0, len(data)
    while pos < n:
        win_start = max(0, pos - WINDOW_SIZE)
        best_len, best_off = 0, 0
        for start in range(win_start, pos):
            dist = pos - start
            length = 0
            while (length < LOOKAHEAD_SIZE and pos + length < n and
                   data[start + (length % dist)] == data[pos + length]):
                length += 1
            if length > best_len:
                best_len, best_off = length, dist
        if pos + best_len < n:
            next_char = ord(data[pos + best_len])
            advance = best_len + 1
        else:
            next_char = 0
            advance = max(best_len, 1)
        result.extend(struct.pack('BBB', best_off, best_len, next_char))
        pos += advance
    return bytes(result)

def lz77_decode(compressed: bytes) -> str:
    """Decode 3-byte tokens. Appends one byte at a time for overlapping copies."""
    result, i = [], 0
    while i + 2 < len(compressed):
        offset, length, next_byte = struct.unpack('BBB', compressed[i:i+3])
        i += 3
        if length > 0:
            start = len(result) - offset
            for j in range(length):
                result.append(result[start + j])  # one byte at a time = overlapping ok
        if next_byte:
            result.append(chr(next_byte))
    return ''.join(result)

# ── Huffman: compress the LZ77 token stream by byte frequency ─────────────
def huffman_encode(data: bytes) -> tuple:
    freq = Counter(data)
    heap = [[w, [sym, '']] for sym, w in freq.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        lo = heapq.heappop(heap)
        hi = heapq.heappop(heap)
        for pair in lo[1:]: pair[1] = '0' + pair[1]
        for pair in hi[1:]: pair[1] = '1' + pair[1]
        heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
    codes = {sym: code for sym, code in heap[0][1:]}
    bits = ''.join(codes[b] for b in data)
    encoded = int(bits, 2).to_bytes((len(bits) + 7) // 8, 'big')
    return encoded, codes

# ── Pipeline: original text -> LZ77 tokens -> Huffman compressed ──────────
def deflate_encode(text: str):
    lz77_tokens = lz77_encode(text)       # 3-byte tokens: (offset, length, next_char)
    compressed, codes = huffman_encode(lz77_tokens)
    return compressed, codes, lz77_tokens
```

In the DEFLATE pipeline, LZ77 produces a stream of uniform 3-byte tokens `(offset, length, next_char)` where the sliding window of WINDOW_SIZE=255 exploits repetition. Huffman then compresses the byte frequencies within that token stream. LZ77 decode reconstructs token-by-token, copying back-references one byte at a time to support overlapping matches where `offset < length`. This two-stage approach combines repetition elimination (LZ77 sliding window) with symbol frequency compression (Huffman codes).
