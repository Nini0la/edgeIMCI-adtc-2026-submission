#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
"$PYTHON" -m venv .venv-integration
.venv-integration/bin/pip install -e ".[dev]"
npm ci --prefix web

.venv-integration/bin/python -m pytest \
  tests/test_holistic_major_sick_child.py \
  tests/test_prototype_app.py \
  tests/test_llama_cpp_extractor.py
npm test --prefix web
npm run build --prefix web
PYTHONPATH="src:." .venv-integration/bin/python scripts/smoke_stub_server.py

export LLAMA_CPP_BIN="${LLAMA_CPP_BIN:-llama-completion}"
export EDGEIMCI_MODEL_PATH="${EDGEIMCI_MODEL_PATH:-$ROOT/model/qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf}"

test -f "$EDGEIMCI_MODEL_PATH"
PYTHONPATH="src:." .venv-integration/bin/python scripts/verify_local_model.py
