---
name: delta-encoding
description: >
  Delta encoding stores the difference between successive values rather
  than the values themselves. Most effective for slowly-changing numeric
  sequences. Operates on differences between adjacent values, not string
  back-references or dictionary lookups.
---

# Delta Encoding

Delta encoding reduces data size by storing differences (deltas) between
consecutive values rather than absolute values.

## Algorithm

```python
def encode_delta(values: list[int]) -> list[int]:
    if not values:
        return []
    result = [values[0]]          # first value stored as-is
    for i in range(1, len(values)):
        result.append(values[i] - values[i - 1])
    return result


def decode_delta(deltas: list[int]) -> list[int]:
    if not deltas:
        return []
    result = [deltas[0]]
    for i in range(1, len(deltas)):
        result.append(result[-1] + deltas[i])
    return result
```

## Character Delta Encoding

For strings, encode as ordinal differences:

```python
def encode_delta_str(data: str) -> list[int]:
    ords = [ord(c) for c in data]
    return encode_delta(ords)

def decode_delta_str(deltas: list[int]) -> str:
    return ''.join(chr(v) for v in decode_delta(deltas))
```

## Use Case

Delta encoding is effective for sensor readings, time-series, audio PCM
samples, and similar slowly-varying numeric data. It is NOT a general-purpose
string compressor — it does not use back-references or a sliding window.

## Relationship to LZ77 Sliding Window Compression

Delta encoding and LZ77 both exploit redundancy between adjacent values, but at different granularities. Delta encoding stores the difference between consecutive values (useful for time series or sorted integers). LZ77 stores back-references to any substring within a sliding window of previous characters.

| Delta Encoding | LZ77 |
|---------------|------|
| diff = current - previous | offset = distance back in WINDOW_SIZE=255 window |
| Scalar difference per element | 3-byte token: (offset, length, next_char) |
| Only adjacent redundancy | Any repeated substring within the window |
| No match length concept | length = how many chars to copy from back-reference |
| No literal encoding needed | Literal token: (0, 0, next_char) when no match found |

LZ77's sliding window search finds the longest match anywhere in the previous WINDOW_SIZE=255 characters. The greedy encoder emits (offset, length, next_char) 3-byte tokens, advancing by length+1 characters per token. The decoder reconstructs the original string by copying length bytes starting from current_pos - offset, one byte at a time to support overlapping matches where offset < length.

Delta encoding is efficient for numeric sequences with small differences. LZ77 is efficient for text with repeated substrings — the sliding window back-reference mechanism exploits arbitrary repetition that delta encoding cannot capture.

## Integration Example: Delta Encoding vs LZ77 Sliding Window

```python
import struct

# ── Delta encoding: differences between consecutive values ───────────────
def delta_encode(values: list) -> list:
    if not values:
        return []
    deltas = [values[0]]
    for i in range(1, len(values)):
        deltas.append(values[i] - values[i-1])
    return deltas

def delta_decode(deltas: list) -> list:
    if not deltas:
        return []
    result = [deltas[0]]
    for d in deltas[1:]:
        result.append(result[-1] + d)
    return result


# ── LZ77: back-references to any substring in sliding window ─────────────
WINDOW_SIZE = 255
LOOKAHEAD_SIZE = 15

def lz77_encode(data: str) -> bytes:
    """3-byte tokens: (offset, length, next_char). WINDOW_SIZE=255.
    Literal: (0, 0, char). Match: (offset=dist_back, length, next_char).
    Supports overlapping back-references where offset < length.
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
                   data[start + length % dist] == data[pos + length]):
                length += 1
            if length > best_len:
                best_len, best_off = length, dist
        nc = ord(data[pos + best_len]) if pos + best_len < n else 0
        result.extend(struct.pack('BBB', best_off, best_len, nc))
        pos += best_len + 1 if pos + best_len < n else max(best_len, 1)
    return bytes(result)

def lz77_decode(compressed: bytes) -> str:
    """Decode 3-byte tokens. One-byte-at-a-time copy supports overlapping."""
    out, i = [], 0
    while i + 2 < len(compressed):
        offset, length, next_byte = struct.unpack('BBB', compressed[i:i+3])
        i += 3
        start = len(out) - offset
        for j in range(length):
            out.append(out[start + j])
        if next_byte:
            out.append(chr(next_byte))
    return ''.join(out)


# Compare on a timestamp sequence (delta excels) vs repeated-text (LZ77 excels)
timestamps = [1000, 1010, 1020, 1030]
deltas = delta_encode(timestamps)  # [1000, 10, 10, 10] — small deltas

text = "abcabcabcabc"
tokens = lz77_encode(text)         # back-references to sliding window
assert lz77_decode(tokens) == text
print(f"LZ77 tokens: {len(tokens)//3} x 3-byte (offset, length, next_char)")
```

Delta encoding compresses numeric sequences with small differences between consecutive values — it has no concept of a sliding window, offset, length, or next_char. LZ77 compresses any text with repeated substrings using a WINDOW_SIZE=255 sliding window and 3-byte `(offset, length, next_char)` tokens. The LZ77 decoder copies back-references one byte at a time to handle overlapping matches where `offset < length`. For structured numeric data, delta encoding is simpler; for general text compression, LZ77's sliding window back-references are more powerful.
