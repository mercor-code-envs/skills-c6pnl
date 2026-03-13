#!/usr/bin/env bash
set -euo pipefail
pip install pytest --quiet
echo "Dependencies installed: pytest"
echo "Input files available:"
echo "  /app/input_files/log_samples.txt  — 30 server log entries with error patterns"
echo "  /app/input_files/keywords.txt     — 10 keywords to search for"
