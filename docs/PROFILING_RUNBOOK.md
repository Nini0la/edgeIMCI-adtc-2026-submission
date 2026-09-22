# ADTC Participant Profiling Runbook

This runbook prepares the target ASUS laptop for a repeatable, CPU-only ADTC participant profile of the GGUF currently declared in `metadata.json`.

## Scope

The current submission artifact is:

- Model: `EdgeIMCI-Qwen3-0.6B-SFT-Q8_0`
- File: `model/qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf`
- Size: 639,446,752 bytes
- SHA-256: `26d11ee99801455fcef011a3e5ff124b2ff1cce943ed06cbe611c8fbcc42aca2`
- Hosted revision: `6af69949d91fbe2628d88a6ed7df62a944cd71a3`

The Beta0-1K candidates under `provenance/` are not packaged GGUF submission artifacts and must not be profiled as if they replaced this model.

Modal is not required. The current GGUF is downloaded from its immutable public Hugging Face revision by `download_model.sh`.

## Required Persistent Storage

Do not use a non-persistent “Try Ubuntu” session. Package installations, source builds, model weights, caches, and reports must survive reboot. Use a persistent live USB, a full Ubuntu installation on external storage, or an internal installation.

Allow at least 20 GB of persistent free space. USB 3 or an external SSD is preferred over a slow flash drive.

## 1. Install System Packages

On Ubuntu 22.04:

```bash
sudo apt update
sudo apt install -y \
  git curl wget ca-certificates \
  build-essential cmake ninja-build pkg-config \
  libopenblas-dev lm-sensors jq
```

Initialize and check temperature sensors:

```bash
sudo sensors-detect --auto
sensors
```

Record the target environment:

```bash
lscpu
free -h
swapon --show
df -h
uname -a
```

The previously measured ASUS target had an Intel Core i5-4210U with two physical cores, four logical threads, 11 GiB RAM, and no swap.

## 2. Install an Isolated Python 3.11 Environment

Ubuntu 22.04 normally provides Python 3.10. Use `uv` to install Python 3.11 without replacing the system interpreter:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

uv python install 3.11
mkdir -p "$HOME/.venvs"
uv venv --python 3.11 "$HOME/.venvs/adtc-profiler"
source "$HOME/.venvs/adtc-profiler/bin/activate"
python --version
```

## 3. Clone the Submission

For the current unmerged integration branch:

```bash
mkdir -p "$HOME/adtc"
cd "$HOME/adtc"
git clone \
  --branch chore/sync-upstream-provenance \
  --single-branch \
  https://github.com/Nini0la/edgeIMCI-adtc-2026-submission.git
cd edgeIMCI-adtc-2026-submission
```

Record and inspect the exact commit:

```bash
git rev-parse HEAD
git status --porcelain
```

The status command must print nothing before a final profile. A development profile may use this branch, but the final scoreable profile must be rerun from the final merged submission commit because the profiler records the checked-out commit in `submission.json`.

## 4. Download and Verify the GGUF

From the submission repository root:

```bash
bash download_model.sh
sha256sum model/qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf
stat --printf='%s bytes\n' model/qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf
```

Expected SHA-256:

```text
26d11ee99801455fcef011a3e5ff124b2ff1cce943ed06cbe611c8fbcc42aca2
```

Expected size:

```text
639446752 bytes
```

Stop if either value differs.

## 5. Build the Pinned CPU `llama-bench`

The profiler requires `llama-bench` on `PATH`. Build the `llama.cpp` revision already recorded in `REPORT.md`:

```bash
cd "$HOME/adtc"
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
git checkout aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3

cmake -S . -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_NATIVE=ON \
  -DGGML_BLAS=ON \
  -DGGML_BLAS_VENDOR=OpenBLAS \
  -DLLAMA_CURL=OFF

cmake --build build \
  --config Release \
  -j2 \
  --target llama-bench
```

Make the binary available in the current shell:

```bash
export PATH="$HOME/adtc/llama.cpp/build/bin:$PATH"
command -v llama-bench
llama-bench --version
```

Run a short direct smoke test:

```bash
cd "$HOME/adtc/edgeIMCI-adtc-2026-submission"
llama-bench \
  -m model/qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf \
  -p 32 \
  -n 8 \
  -t 2 \
  -ngl 0 \
  --output json
```

The ADTC profiler also forces zero GPU layers, so the measured path is CPU-only.

## 6. Install the Pinned ADTC Profiler

Activate the profiler environment and install the recorded profiler source revision:

```bash
source "$HOME/.venvs/adtc-profiler/bin/activate"
uv pip install \
  "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git@7f117dde3d8f2a0b3d3f05948a7bfd4bf693e909"
adtc-profiler --help
```

Before the final submission run, check organizer instructions for a newer mandatory profiler revision. If the profiler changes, record the new revision and rerun the complete profile.

## 7. Capture Preflight Evidence

Keep profiler outputs outside the Git checkout so the submission worktree remains clean:

```bash
mkdir -p "$HOME/adtc-artifacts"
cd "$HOME/adtc/edgeIMCI-adtc-2026-submission"

lscpu > "$HOME/adtc-artifacts/lscpu.txt"
free -h > "$HOME/adtc-artifacts/memory-before.txt"
swapon --show > "$HOME/adtc-artifacts/swap.txt"
sensors > "$HOME/adtc-artifacts/sensors-before.txt"
git rev-parse HEAD > "$HOME/adtc-artifacts/submission-commit.txt"
git status --porcelain > "$HOME/adtc-artifacts/worktree-status.txt"
sha256sum model/qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf \
  > "$HOME/adtc-artifacts/model.sha256"
llama-bench --version > "$HOME/adtc-artifacts/llama-bench-version.txt" 2>&1
uv pip freeze > "$HOME/adtc-artifacts/profiler-environment.txt"
```

`worktree-status.txt` must be empty for the final run.

## 8. Run a Fast Participant Smoke Profile

Connect AC power, close unrelated applications, and let the laptop return to a stable idle temperature. Then run:

```bash
cd "$HOME/adtc/edgeIMCI-adtc-2026-submission"
source "$HOME/.venvs/adtc-profiler/bin/activate"
export PATH="$HOME/adtc/llama.cpp/build/bin:$PATH"
export ADTC_CPU_THREADS=2

adtc-profiler run \
  --submission "$PWD" \
  --mode participant \
  --output "$HOME/adtc-artifacts/submission-smoke.json" \
  --skip-accuracy
```

Inspect the smoke report:

```bash
jq '{throughput, memory, cpu_thermal, reproducibility, model_info, accuracy}' \
  "$HOME/adtc-artifacts/submission-smoke.json"
```

An empty `accuracy` array is expected only for this smoke run.

## 9. Run the Complete Scoreable Profile

The complete participant run must omit `--skip-accuracy`:

```bash
adtc-profiler run \
  --submission "$PWD" \
  --mode participant \
  --output "$HOME/adtc-artifacts/submission.json"
```

The first full accuracy run may download and cache the evaluation dataset. If that happens, let it finish, allow the laptop to cool, and repeat the complete run so setup and cache activity do not contaminate the retained run.

Verify that accuracy is present and that the report captured the checked-out submission commit:

```bash
jq -e '.accuracy | length > 0' "$HOME/adtc-artifacts/submission.json"
git rev-parse --short=12 HEAD
jq -r '.reproducibility.git_commit_sha' "$HOME/adtc-artifacts/submission.json"
```

The two commit values must match. Inspect the retained measurements:

```bash
jq '{throughput, memory, accuracy, cpu_thermal, reproducibility, model_info}' \
  "$HOME/adtc-artifacts/submission.json"
```

Preserve the report checksum and final sensor reading:

```bash
sha256sum "$HOME/adtc-artifacts/submission.json" \
  > "$HOME/adtc-artifacts/submission.json.sha256"
sensors > "$HOME/adtc-artifacts/sensors-after.txt"
```

## Final-Run Rules

- Use the exact final submission commit with a clean worktree.
- Use the exact GGUF bytes and verify their size and SHA-256.
- Keep the laptop connected to AC power.
- Use the same two physical CPU threads unless the hardware topology differs.
- Do not use GPU offload.
- Close background workloads and allow the laptop to cool between runs.
- Do not retain a report with an empty accuracy array.
- Preserve `submission.json`, its checksum, the Git commit, environment capture, model checksum, profiler package list, `llama-bench` version, and sensor records together.
- Rerun the complete profile after any model, metadata, profiler, runtime, or submission commit change.

## Separate Application Acceptance

Profiling requires `llama-bench`; it does not require the GUI, Node.js, Modal, or `llama-completion`.

The optional application acceptance script, `scripts/verify_llama_cpp_integration.sh`, additionally requires the historically qualified `llama-completion` executable with SHA-256 `a41d3d5fec1173afc89323a026a8f3612a9de2692a8c825223852627e8277641`. A fresh source build may not reproduce that executable digest. This does not block ADTC profiling.
