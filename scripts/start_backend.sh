#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/setup.sh

if command -v lsof >/dev/null 2>&1; then
  lsof -ti :8000 | xargs -r kill >/dev/null 2>&1 || true
elif command -v fuser >/dev/null 2>&1; then
  fuser -k 8000/tcp >/dev/null 2>&1 || true
fi

exec .venv/bin/python -m uvicorn backend.main:app --reload --port 8000
