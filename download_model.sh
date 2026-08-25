#!/usr/bin/env bash
# Download your model weight file.
#
# Rules:
#   - Must be idempotent (safe to run multiple times).
#   - Must download without any credentials (public URL only).
#   - The output path must match `_runtime.model_path` in metadata.json.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="$HERE/model"
MODEL_FILE="$MODEL_DIR/qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf"
MODEL_URL="https://huggingface.co/Nini0la/edgeimci-qwen3-0.6b-sft-gguf/resolve/6af69949d91fbe2628d88a6ed7df62a944cd71a3/qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf"
EXPECTED_SHA256="26d11ee99801455fcef011a3e5ff124b2ff1cce943ed06cbe611c8fbcc42aca2"

mkdir -p "$MODEL_DIR"

sha256_file() {
  if command -v sha256sum > /dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  elif command -v shasum > /dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d' ' -f1
  else
    echo "error: no SHA-256 utility found" >&2
    return 1
  fi
}

if [[ -f "$MODEL_FILE" ]]; then
  if [[ "$(sha256_file "$MODEL_FILE")" == "$EXPECTED_SHA256" ]]; then
    echo "verified model already present at $MODEL_FILE"
    exit 0
  fi
  echo "error: existing model has the wrong SHA-256: $MODEL_FILE" >&2
  exit 1
fi

echo "downloading $MODEL_URL to $MODEL_FILE (~610 MB)"

if command -v curl > /dev/null 2>&1; then
  curl -L --fail --progress-bar -o "$MODEL_FILE.partial" "$MODEL_URL"
elif command -v wget > /dev/null 2>&1; then
  wget --show-progress -O "$MODEL_FILE.partial" "$MODEL_URL"
else
  echo "error: neither curl nor wget found" >&2
  exit 1
fi

ACTUAL_SHA256="$(sha256_file "$MODEL_FILE.partial")"
if [[ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]]; then
  rm -f "$MODEL_FILE.partial"
  echo "error: model SHA-256 mismatch" >&2
  echo "expected: $EXPECTED_SHA256" >&2
  echo "actual:   $ACTUAL_SHA256" >&2
  exit 1
fi

mv "$MODEL_FILE.partial" "$MODEL_FILE"
echo "verified: $MODEL_FILE"
