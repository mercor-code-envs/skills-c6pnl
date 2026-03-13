A data archiving system needs a streaming compression codec for text data. Implement a sliding window compression codec. A sample corpus for compression testing is at `/app/input_files/corpus.txt` and the codec specification at `/app/input_files/codec_spec.txt`.

A scaffold file is provided at `/app/input_files/compressor.py`. Complete the implementation and place the finished file at `/app/compressor.py`.

Requirements:
- `decode(encode(s)) == s` for any string
- Repeated patterns must be compressed (encoded size < raw size for repetitive input)
- Handle overlapping back-references (e.g., copying a pattern longer than the match distance)
- Each token is exactly 3 bytes: `(offset, length, next_char)` packed as `struct.pack('BBB', ...)`