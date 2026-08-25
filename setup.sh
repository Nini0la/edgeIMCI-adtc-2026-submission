#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
"$PYTHON" -m venv .venv
.venv/bin/pip install -e ".[dev]"
npm ci --prefix web
npm run build --prefix web

if [[ "${EDGEIMCI_SKIP_MODEL_DOWNLOAD:-0}" != "1" ]]; then
  bash download_model.sh
fi

echo "setup complete"
echo "set LLAMA_CPP_BIN to the qualified llama-completion executable, then run: bash run.sh"
