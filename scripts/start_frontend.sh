#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/setup.sh

if command -v lsof >/dev/null 2>&1; then
  lsof -ti :5173 | xargs -r kill >/dev/null 2>&1 || true
elif command -v fuser >/dev/null 2>&1; then
  fuser -k 5173/tcp >/dev/null 2>&1 || true
fi

echo "Starting React frontend on http://localhost:5173 ..."
cd frontend
exec npm run dev
