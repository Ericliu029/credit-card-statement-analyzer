#!/bin/zsh
set -e

MODEL="llama3.2:3b"

if ! command -v ollama >/dev/null 2>&1; then
  echo "Install Ollama from https://ollama.com/download/mac and run this script again."
  open "https://ollama.com/download/mac"
  exit 1
fi

if ! curl --silent --fail http://localhost:11434/api/version >/dev/null; then
  open -a Ollama
  sleep 3
fi

ollama pull "$MODEL"
echo "Local AI is ready: $MODEL"
