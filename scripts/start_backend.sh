#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/setup.sh
exec .venv/bin/python -m uvicorn backend.main:app --reload --port 8000
