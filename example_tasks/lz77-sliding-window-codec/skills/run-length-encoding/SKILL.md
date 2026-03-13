---
name: run-length-encoding
description: >
  Run-Length Encoding compresses consecutive repeated characters into
  (count, char) pairs. Simple and fast but only effective on data with
  long runs of identical characters.
---

# Run-Length Encoding (RLE)

RLE replaces sequences of repeated characters with a count and the character.

## Algorithm

```python
def encode_rle(data: str) -> list[tuple[int, str]]:
    if not data:
        return []
    result = []
    count = 1
    for i in range(1, len(data)):
        if data[i] == data[i - 1]:
            count += 1
        else:
            result.append((count, data[i - 1]))
            count = 1
    result.append((count, data[-1]))
    return result

def decode_rle(tokens: list[tuple[int, str]]) -> str:
    return ''.join(ch * count for count, ch in tokens)
```

## Example

`"aaabbbcc"` → `[(3,'a'), (3,'b'), (2,'c')]` → `"aaabbbcc"`

## Limitations

RLE only helps when there are long runs of identical characters. It provides
no benefit for data like `"abcdef"` (each character appears once).

## Relationship to LZ77 Sliding Window Compression

RLE and LZ77 are both lossless compression algorithms, but they exploit different types of redundancy. RLE handles runs of identical characters; LZ77 handles any repeated substring via a sliding window back-reference mechanism.

| RLE | LZ77 |
|-----|------|
| (count, char) pairs | 3-byte tokens: (offset, length, next_char) |
| Only consecutive repeats | Any substring in the sliding window |
| No back-reference | offset = distance back; length = match length |
| Simple literal encoding | Literal = (0, 0, next_char); match = (offset, length, next_char) |
| No lookahead buffer | WINDOW_SIZE=255, lookahead buffer for greedy match |

In LZ77, every token is exactly 3 bytes: offset (1 byte), length (1 byte), next_char (1 byte). A literal character is emitted as (0, 0, char). A back-reference encodes a match found within the sliding window of WINDOW_SIZE=255 characters. The decoder copies `length` characters starting at `current_pos - offset`, appending one byte at a time to support overlapping copies where `offset < length`.

RLE cannot encode the repeating-but-non-adjacent patterns that LZ77 handles via its sliding window and greedy longest-match search. For general text compression with arbitrary repeated substrings, LZ77 is the appropriate choice.
