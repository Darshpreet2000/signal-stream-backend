#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer a project virtualenv if present
if [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
	PY="$SCRIPT_DIR/venv/bin/python"
elif [ -x "$SCRIPT_DIR/../.venv/bin/python" ]; then
	PY="$SCRIPT_DIR/../.venv/bin/python"
else
	PY="python"
fi

exec "$PY" run.py
