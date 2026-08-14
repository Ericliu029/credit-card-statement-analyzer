#!/bin/zsh
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$APP_DIR/.runtime"
RUNTIME_BIN="$RUNTIME_DIR/bin"
UV="$RUNTIME_BIN/uv"
VENV="$APP_DIR/.venv-macos"
MODEL="llama3.2:3b"

print_step() {
  printf "\n==> %s\n" "$1"
}

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This installer must be run on macOS."
  read "?Press Return to close."
  exit 1
fi

cd "$APP_DIR"
mkdir -p "$RUNTIME_BIN"

print_step "Preparing the private Python runtime"
if [[ ! -x "$UV" ]]; then
  curl --fail --location --silent --show-error https://astral.sh/uv/install.sh | \
    env UV_UNMANAGED_INSTALL="$RUNTIME_BIN" sh
fi

"$UV" python install 3.12
if [[ ! -x "$VENV/bin/python" ]]; then
  "$UV" venv --python 3.12 "$VENV"
fi
"$UV" pip install --python "$VENV/bin/python" --requirement "$APP_DIR/requirements.txt"

print_step "Checking optional local AI"
OLLAMA_BIN="$(command -v ollama 2>/dev/null || true)"
if [[ -z "$OLLAMA_BIN" && -x "/Applications/Ollama.app/Contents/Resources/ollama" ]]; then
  OLLAMA_BIN="/Applications/Ollama.app/Contents/Resources/ollama"
fi

if [[ -z "$OLLAMA_BIN" ]]; then
  echo "Ollama is not installed yet. The official download page will open."
  echo "Install Ollama, then run this installer one more time to enable local AI categorization."
  open "https://ollama.com/download/mac"
else
  if ! curl --silent --fail http://localhost:11434/api/version >/dev/null 2>&1; then
    open -a Ollama >/dev/null 2>&1 || true
    for _ in {1..20}; do
      if curl --silent --fail http://localhost:11434/api/version >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done
  fi

  if curl --silent --fail http://localhost:11434/api/version >/dev/null 2>&1; then
    "$OLLAMA_BIN" pull "$MODEL"
  else
    echo "Ollama did not start. You can open Ollama and run this installer again later."
  fi
fi

print_step "Installation complete"
echo "Starting Credit Card Statement Analyzer..."
exec "$APP_DIR/Start Credit Card Analyzer.command"
