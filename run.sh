#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
  echo "error: run 'bash setup.sh' first" >&2
  exit 1
fi

if [[ ! -f web/dist/index.html ]]; then
  echo "error: frontend build missing; run 'bash setup.sh' first" >&2
  exit 1
fi

EXTRACTOR="${EDGEIMCI_EXTRACTOR:-llama-cpp}"
export EDGEIMCI_MODEL_PATH="${EDGEIMCI_MODEL_PATH:-$ROOT/model/qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf}"
export LLAMA_CPP_BIN="${LLAMA_CPP_BIN:-llama-completion}"
export EDGE_IMCI_REPO_ROOT="$ROOT"
export PYTHONPATH="$ROOT/src:$ROOT${PYTHONPATH:+:$PYTHONPATH}"

exec .venv/bin/python -m app --extractor "$EXTRACTOR" "$@"
