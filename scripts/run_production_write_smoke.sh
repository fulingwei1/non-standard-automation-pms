#!/usr/bin/env bash
set -euo pipefail

python -m pytest -q tests/api/test_production_write_smoke.py "$@"
