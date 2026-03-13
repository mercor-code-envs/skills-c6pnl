---
name: lz77-token-format
description: >
  Defines the exact LZ77 token format used by the sliding window codec:
  each token is a 3-byte (offset, length, next_char) tuple. Covers the
  no-match literal case, end-of-string handling, and WINDOW_SIZE=255,
  LOOKAHEAD_SIZE=15 constants.
---

# LZ77 Token Format and Byte Encoding

LZ77 compresses data by replacing repeated substrings with back-references
to earlier occurrences. Every token encodes either a literal character or a
back-reference plus the character that follows the match.

## Constants

```python
WINDOW_SIZE = 255    # maximum look-back distance (bytes)
LOOKAHEAD_SIZE = 15  # maximum match length (bytes)
```

These values are **fixed**. Using different values breaks interoperability.

## Token Structure

Each token is exactly **3 bytes**: `(offset, length, next_char)`

| Field | Type | Range | Meaning |
|-------|------|-------|---------|
| `offset` | `int` | 0 – 255 | Distance **backwards** from current position to start of match |
| `length` | `int` | 0 – 15 | Number of characters in the match |
| `next_char` | `int` (byte) | 0 – 255 | `ord` of the character immediately after the match; `0` if end of string |

## No-Match (Literal) Token

When no match is found in the window, emit a **literal token**:

```
offset = 0, length = 0, next_char = ord(current_char)
```

Advance position by 1.

## Match Token

When a match of length `L` is found starting at distance `D` backwards:

```
offset = D, length = L, next_char = ord(data[pos + L])
```

Advance position by `L + 1`.

## End of String

If the match extends to the very end of the input (no character follows):

```
offset = D, length = L, next_char = 0
```

Advance position by `L` (no +1 since there is no next character to consume).

## Byte Encoding

Use `struct.pack` and `struct.unpack` with format `'BBB'` (three unsigned bytes):

```python
import struct

# Encoding one token
def emit_token(result: bytearray, offset: int, length: int, next_char: int) -> None:
    result.extend(struct.pack('BBB', offset, length, next_char))

# Decoding one token
def read_token(compressed: bytes, i: int) -> tuple[int, int, int]:
    offset, length, next_byte = struct.unpack('BBB', compressed[i:i + 3])
    return offset, length, next_byte
```

The compressed byte stream length is always a multiple of 3.

## Complete Token Examples

| Input | Token(s) | Explanation |
|-------|----------|-------------|
| `"a"` | `(0, 0, 97)` | No match; literal 'a' (ord=97) |
| `"ab"` | `(0, 0, 97)` `(0, 0, 98)` | Two literals |
| `"aaaa"` | `(0, 0, 97)` `(1, 3, 0)` | Literal 'a', then back-ref offset=1 len=3, end of string |
| `"abcabc"` | `(0,0,97)` `(0,0,98)` `(0,0,99)` `(3,3,0)` | Three literals then back-ref to "abc" |

## Decode Logic

> **⚠️ TWO RULES THAT BREAK TESTS IF VIOLATED:**
> 1. Check `if length > 0` (NOT `if offset > 0`) before copying the back-reference.
> 2. Check `if next_byte != 0` before appending the next character.
>    **`next_byte == 0` is end-of-string padding — appending it causes `aaaaa\x00` instead of `aaaaa`.**

## Common Mistakes

| Mistake | Symptom |
|---------|---------|
| Using a 2-tuple `(offset, length)` — no `next_char` | Decoder loses one character per token |
| Using 4 bytes per token | Incompatible byte stream; decoder produces garbage |
| `next_char` as the char **before** the match | Off-by-one in every token |
| **Not checking `if next_byte != 0` in decode** | **`test_decode_overlapping_token` fails with `aaaaa\x00` instead of `aaaaa`** |
| Omitting end-of-string `advance = length` (not `length + 1`) | Infinite loop or skipped chars at end |
| Copying backref bytes all at once (e.g. slice copy) | Overlapping refs decode incorrectly; use one-byte-at-a-time loop |
