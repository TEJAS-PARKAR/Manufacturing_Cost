#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

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

echo "Upgrading pip and installing dependencies..."
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/pip" install -r requirements.txt

echo "Setup complete. Activate the environment with: source $VENV/bin/activate"
