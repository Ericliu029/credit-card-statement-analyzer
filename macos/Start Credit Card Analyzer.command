#!/bin/zsh
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$APP_DIR/.venv-macos"

cd "$APP_DIR"

if [[ ! -x "$VENV/bin/python" ]]; then
  exec "$APP_DIR/Install Credit Card Analyzer.command"
fi

if ! curl --silent --fail http://localhost:11434/api/version >/dev/null 2>&1; then
  open -a Ollama >/dev/null 2>&1 || true
fi

exec "$VENV/bin/python" -m streamlit run "$APP_DIR/app.py" --server.address 127.0.0.1
