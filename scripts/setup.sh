#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# ── Python setup ──
PYTHON=${PYTHON:-python3}
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  PYTHON=python
fi
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "ERROR: Python is required but not installed or not on PATH." >&2
  exit 1
fi

VENV=".venv"
if [ ! -d "$VENV" ]; then
  echo "Creating Python virtual environment in $VENV"
  "$PYTHON" -m venv "$VENV"
fi

echo "Upgrading pip and installing Python dependencies..."
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/pip" install -r requirements.txt

# ── Node.js / Frontend setup ──
if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: Node.js is required but not installed or not on PATH." >&2
  echo "Install it from https://nodejs.org/ and try again." >&2
  exit 1
fi

echo "Installing frontend dependencies..."
cd frontend
npm install
cd "$ROOT_DIR"

echo ""
echo "Setup complete!"
echo "  Backend:  activate the environment with: source $VENV/bin/activate"
echo "  Frontend: ready to run with: cd frontend && npm run dev"
