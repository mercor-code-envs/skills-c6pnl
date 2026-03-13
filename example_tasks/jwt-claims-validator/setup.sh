#!/usr/bin/env bash
set -euo pipefail
pip install pytest --quiet
echo "Dependencies installed: pytest"
echo "Uses Python standard library only (hmac, hashlib, base64, json, time)."
echo "Input files available:"
echo "  /app/input_files/auth_spec.txt       — JWT validation specification"
echo "  /app/input_files/sample_config.json  — sample service configuration"
