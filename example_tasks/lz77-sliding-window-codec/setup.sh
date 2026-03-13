#!/usr/bin/env bash
set -euo pipefail
pip install pytest --quiet
echo "Dependencies installed: pytest"
echo "Input files available:"
echo "  /app/input_files/corpus.txt    — sample text corpus with repetitive patterns for compression testing"
echo "  /app/input_files/codec_spec.txt — LZ77 codec implementation specification"
