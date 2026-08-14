#!/bin/zsh
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$APP_DIR/.venv-macos"

cd "$APP_DIR"

if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install -r requirements.txt
fi

exec "$VENV/bin/python" -m streamlit run app.py --server.address 127.0.0.1
