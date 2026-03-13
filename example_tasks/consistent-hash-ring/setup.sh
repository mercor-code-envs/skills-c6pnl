#!/usr/bin/env bash
set -euo pipefail
pip install pytest --quiet
echo "Dependencies installed: pytest"
echo "Input files available:"
echo "  /app/input_files/servers.txt      — 8 initial cache node hostnames"
echo "  /app/input_files/design_notes.txt — engineering design document for the hash ring"
