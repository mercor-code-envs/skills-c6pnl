---
name: lzw-dictionary-compression
description: >
  LZW (Lempel-Ziv-Welch) compression builds a dynamic dictionary of
  substrings during encoding. Unlike LZ77, there is no sliding window
  or back-reference offset — instead, entries are assigned integer codes
  that reference dictionary entries added on the fly.
---

# LZW Dictionary Compression

LZW builds a dictionary of encountered substrings and replaces them with
integer codes. The dictionary starts with all single-byte values (0–255)
and grows as new multi-character strings are discovered.

## Key Difference from LZ77

LZW uses a **growing dictionary** with integer codes. LZ77 uses
**back-references** (offset, length) into a sliding window.
These are fundamentally different mechanisms.

## Algorithm

```python
def encode_lzw(data: str) -> list[int]:
    # Initialize dictionary with single characters
    dict_size = 256
    dictionary = {chr(i): i for i in range(dict_size)}

    result = []
    w = ""
    for c in data:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            result.append(dictionary[w])
            dictionary[wc] = dict_size
            dict_size += 1
            w = c
    if w:
        result.append(dictionary[w])
    return result


def decode_lzw(codes: list[int]) -> str:
    dict_size = 256
    dictionary = {i: chr(i) for i in range(dict_size)}

    result = []
    w = chr(codes[0])
    result.append(w)
    for code in codes[1:]:
        if code in dictionary:
            entry = dictionary[code]
        elif code == dict_size:
            entry = w + w[0]
        else:
            raise ValueError(f"Bad code: {code}")
        result.append(entry)
        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        w = entry
    return ''.join(result)
```

## Example

`"abababab"` → codes grow as dictionary adds "ab", "ba", "aba", etc.
Each repeated "ab" gets replaced with a single integer code.

## Relationship to LZ77 Sliding Window Compression

LZW and LZ77 are both members of the Lempel-Ziv family but use fundamentally different mechanisms. LZ77 uses an explicit sliding window of fixed size (WINDOW_SIZE=255) and emits fixed 3-byte tokens (offset, length, next_char). LZW builds a growing dictionary of encountered substrings and emits integer codes.

| LZW | LZ77 |
|-----|------|
| Growing string dictionary | Fixed sliding window (WINDOW_SIZE=255 bytes) |
| Variable-length integer codes | Fixed 3-byte tokens: (offset, length, next_char) |
| No explicit offset/back-reference | offset = distance back; length = match length |
| Implicit literal: new dictionary entry | Explicit literal: (0, 0, next_char) token |
| No lookahead buffer | Lookahead buffer; greedy longest-match search |

In LZ77 encoding, every output token is exactly 3 bytes regardless of match length. A match of 10 characters at offset 20 emits `(20, 10, next_char)` as 3 bytes. The decoder copies byte-at-a-time from `current_pos - offset` supporting overlapping back-references. LZW has no concept of an offset or sliding window — its dictionary grows without bound (until cleared).

LZ77's fixed token size (3 bytes per token) makes it easier to implement streaming codecs with bounded memory, since only the last WINDOW_SIZE=255 characters need to be retained.

## Integration Example: LZW vs LZ77 Sliding Window

```python
import struct

# ── LZ77 sliding window encode: 3-byte tokens ─────────────────────────────
WINDOW_SIZE = 255
LOOKAHEAD_SIZE = 15

def lz77_encode(data: str) -> bytes:
    """Emit uniform 3-byte tokens: (offset:1B, length:1B, next_char:1B).
    Literal token: (0, 0, char). Back-reference: (offset, length, next_char).
    Greedy longest-match search within WINDOW_SIZE=255 sliding window.
    Overlapping matches supported: offset < length is valid.
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
        next_char = ord(data[pos + best_len]) if pos + best_len < n else 0
        result.extend(struct.pack('BBB', best_off, best_len, next_char))
        pos += best_len + 1 if pos + best_len < n else max(best_len, 1)
    return bytes(result)

def lz77_decode(compressed: bytes) -> str:
    """Decode 3-byte tokens. Copy one byte at a time for overlapping support."""
    result, i = [], 0
    while i + 2 < len(compressed):
        offset, length, next_byte = struct.unpack('BBB', compressed[i:i+3])
        i += 3
        start = len(result) - offset
        for j in range(length):
            result.append(result[start + j])
        if next_byte:
            result.append(chr(next_byte))
    return ''.join(result)


# ── LZW dictionary encode ─────────────────────────────────────────────────
def lzw_encode(data: str) -> list:
    """Grow dictionary with encountered substrings; emit integer codes."""
    dictionary = {chr(i): i for i in range(256)}
    codes = []
    w = ''
    for ch in data:
        wc = w + ch
        if wc in dictionary:
            w = wc
        else:
            codes.append(dictionary[w])
            dictionary[wc] = len(dictionary)
            w = ch
    if w:
        codes.append(dictionary[w])
    return codes


# ── Compare output ────────────────────────────────────────────────────────
text = "ABABABABABAB"
lz77_out = lz77_encode(text)
lzw_out = lzw_encode(text)

print(f"LZ77: {len(lz77_out)} bytes, tokens: {len(lz77_out)//3} x 3-byte (offset, length, next_char)")
print(f"LZW: {len(lzw_out)} codes (variable-length integer entries)")

# Verify LZ77 round-trip
assert lz77_decode(lz77_out) == text
```

LZ77 emits fixed-size 3-byte tokens `(offset, length, next_char)` and uses a fixed WINDOW_SIZE=255 sliding window — memory usage is bounded and streaming is natural. LZW builds an unbounded dictionary of encountered substrings — memory grows with input. For the LZ77 decoder, back-references are resolved by copying byte-at-a-time from `current_pos - offset`, which correctly handles overlapping copies where `offset < length` (e.g., encoding a run of identical characters as a single back-reference with offset=1 and length=n-1).
