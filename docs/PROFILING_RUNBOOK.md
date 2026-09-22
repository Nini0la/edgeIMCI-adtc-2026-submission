# ADTC Participant Profiling Runbook

This runbook prepares an Ubuntu 22.04 laptop booted from USB for a repeatable, CPU-only ADTC participant profile of the newly selected 4B-alpha-second Q4_K_M GGUF. Run the stages in order in the same Bash session; stop on any failed check.

## Scope

The current submission artifact is:

- Model: `EdgeIMCI-4B-alpha-second-Q4_K_M`
- File: `model/EdgeIMCI-4B-alpha-second-Q4_K_M.gguf`
- Size: 2,497,280,288 bytes
- SHA-256: `a4a8c5bb2d9f3401defa1cb8ea007812d5916c0242d8306a1c7ed6322d550919`
- Hosting repository: `Nini0la/edgeimci-4b-alpha-second-gguf`
- Hosted revision: `1aeace1a2eb6e46e5e93d6536cbd1c19db982e53`, successfully uploaded and publicly available. Use this immutable revision in the committed `MODEL_URL` in `download_model.sh`, not a moving `main` URL or the old model's URL.

The branch must contain the updated metadata, static downloader pin, and `scripts/verify_model_artifact.py` before proceeding. If the published branch still names the old artifact, stop and wait for the integration update. Historical 0.6B reports are not measurements of this model.

Modal is not required. This procedure does not establish a pass on the official 8 GB laptop profile, nor clinical qualification. Those require separate evidence.

## 0. Check USB Storage and Memory First

Before installing or downloading anything, inspect the current live-USB mounts:

```bash
findmnt /
findmnt -T "$HOME"
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
df -hT / "$HOME" /tmp
free -h
swapon --show
```

The inspected Ubuntu session reports `$HOME` on the `/cow` overlay (5.8 GiB), `/tmp` on tmpfs (5.8 GiB), 11 GiB RAM, and no swap. The live USB is `/dev/sdb` (57.3 GB); its existing `/dev/sdb4` partition is ext4, labelled `writable`, with 52.9 GB capacity, initially mounted only at `/var/log` and `/var/crash`. Capacity is not free space: check `df` below. **Root/home persistence is not verified.** Treat the live root and home as ephemeral, and keep the model, builds, managed Python, environments, caches, data, and reports off both that overlay and `/tmp`.

### Mount the Existing Partition on This Inspected Machine Only

The device-specific commands below apply **only to the inspected machine above**, after confirming the current `lsblk` output still identifies `/dev/sdb4` as that USB partition. Device names can change after reboot. On another machine, identify an existing suitable persistent filesystem and substitute its verified device and mount path; never blindly assume `sdb4`. Do not touch the internal `/dev/sda`, format, repartition, or unmount the existing log mounts.

Mount the **existing** filesystem at an additional mount point. If the owner already mounted it there, skip the mount operation and verify it instead. Use a dedicated Bash session:

```bash
set -euo pipefail
sudo mkdir -p /mnt/adtc-storage
if ! mountpoint -q /mnt/adtc-storage; then
  sudo mount /dev/sdb4 /mnt/adtc-storage
fi
findmnt --mountpoint /mnt/adtc-storage -o SOURCE,TARGET,FSTYPE,OPTIONS
df -hT /mnt/adtc-storage
test "$(findmnt -n -o SOURCE --mountpoint /mnt/adtc-storage)" = /dev/sdb4
test "$(findmnt -n -o FSTYPE --mountpoint /mnt/adtc-storage)" = ext4
case ",$(findmnt -n -o OPTIONS --mountpoint /mnt/adtc-storage)," in
  *,rw,*) ;;
  *) printf '%s\n' 'Storage is not mounted read-write; stop.' >&2; exit 1 ;;
esac
```

Stop and review the `findmnt` source, mount options, and `df` free space before continuing. Plan for at least **30 GB of persistent free space**, plus headroom for build intermediates, caches, and existing USB logs. This is a planning allowance, not a measured maximum. USB 3 or an external SSD is preferable to a slow flash drive. No partitioning or formatting is needed.

Create a **new workspace directory only**, and give the current user ownership of just that directory. The guard deliberately stops if it already exists; for a resumed workspace, skip creation/chown, inspect its contents and ownership, and reuse it without clearing anything. Never recursively chown the filesystem or its existing directories:

```bash
export ADTC_HOME=/mnt/adtc-storage/edgeimci-work
test ! -e "$ADTC_HOME"
sudo mkdir "$ADTC_HOME"
sudo chown "$(id -u):$(id -g)" "$ADTC_HOME"
test -w "$ADTC_HOME"
findmnt -T "$ADTC_HOME" -o SOURCE,TARGET,FSTYPE,OPTIONS
df -hT "$ADTC_HOME"
```

### Route All Profiling Storage to `ADTC_HOME`

Export these paths **before installing uv or Python**, including on every resumed shell. `$HOME` need not be persistent. Do not use `sudo` for uv, Python, cloning, builds, or profiling:

```bash
export XDG_CACHE_HOME="$ADTC_HOME/cache"
export XDG_DATA_HOME="$ADTC_HOME/data"
export TMPDIR="$ADTC_HOME/tmp"
export TMP="$TMPDIR"
export TEMP="$TMPDIR"
export HF_HOME="$XDG_CACHE_HOME/huggingface"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export UV_CACHE_DIR="$XDG_CACHE_HOME/uv"
export UV_PYTHON_INSTALL_DIR="$ADTC_HOME/python"
export UV_INSTALL_DIR="$ADTC_HOME/bin"
export UV_PYTHON_BIN_DIR="$ADTC_HOME/bin"
export UV_NO_MODIFY_PATH=1
mkdir -p "$ADTC_HOME/repos" "$ADTC_HOME/venvs" "$ADTC_HOME/artifacts" \
  "$XDG_DATA_HOME" "$TMPDIR" "$HF_DATASETS_CACHE" "$UV_CACHE_DIR" \
  "$UV_PYTHON_INSTALL_DIR" "$UV_INSTALL_DIR"
export PATH="$UV_INSTALL_DIR:$PATH"
```

After reboot, re-identify and remount the USB partition, verify its source/free space, export the same `ADTC_HOME` and storage variables, and activate the retained environment. The workspace survives on ext4; this does **not** establish persistence of the live Ubuntu root. Do not accidentally recreate the workspace in an unmounted `/mnt` directory on the overlay.

## 1. Install System Packages

On Ubuntu 22.04, these system packages still install into the live root, not `ADTC_HOME`. They can support this session, but treat them as ephemeral and reinstall them after reboot. Monitor `df -h /` and `free -h` during installation/builds; persistent workspace storage does not add RAM or root-overlay capacity:

```bash
sudo apt update
sudo apt install -y \
  git curl wget ca-certificates \
  build-essential cmake ninja-build pkg-config python3-dev \
  libopenblas-dev libffi-dev libssl-dev lm-sensors lsb-release jq time
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

The previously measured ASUS had an Intel Core i5-4210U with two physical cores, four logical threads, 11 GiB RAM, and no swap. Record the actual current hardware, available RAM, and swap; do not substitute those historical values or treat that machine as an official 8 GB result. If sensors are unavailable, record that limitation rather than claiming a temperature or throttling pass.

## 2. Install an Isolated Python 3.11 Environment

Ubuntu 22.04 normally provides Python 3.10. Use `uv` to install Python 3.11 without replacing the system interpreter. Create this environment once. If it already exists, activate and inspect it instead of replacing it; preserve environments used for older reports:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$UV_INSTALL_DIR:$PATH"
command -v uv

uv python install 3.11
uv python dir
uv cache dir
uv venv --python 3.11 "$ADTC_HOME/venvs/adtc-profiler-4b"
source "$ADTC_HOME/venvs/adtc-profiler-4b/bin/activate"
python --version
```

Verify that `command -v uv`, `uv python dir`, and `uv cache dir` resolve under `ADTC_HOME`, not the RAM-backed home. The earlier `UV_INSTALL_DIR`, `UV_PYTHON_INSTALL_DIR`, and cache exports prevent the large managed interpreter and dependency downloads from defaulting to `$HOME`.

## 3. Clone the Submission

Clone the published integration branch (no submission commit is assumed here):

```bash
cd "$ADTC_HOME/repos"
git clone \
  --branch chore/sync-upstream-provenance \
  --single-branch \
  https://github.com/Nini0la/edgeIMCI-adtc-2026-submission.git
cd edgeIMCI-adtc-2026-submission
```

For an existing clone **under the persistent workspace**, use this alternative instead of cloning over it. A clone on `main` may not yet have the integration branch locally, so fetch it before switching. If the only existing clone is on the ephemeral home, leave it untouched and make a fresh clone above rather than downloading the model there. Stop if the worktree is dirty; do not discard local changes:

```bash
cd "$ADTC_HOME/repos/edgeIMCI-adtc-2026-submission"
test -z "$(git status --porcelain)"
git fetch origin refs/heads/chore/sync-upstream-provenance:refs/remotes/origin/chore/sync-upstream-provenance
if git show-ref --verify --quiet refs/heads/chore/sync-upstream-provenance; then
  git switch chore/sync-upstream-provenance
else
  git switch --create chore/sync-upstream-provenance --no-track origin/chore/sync-upstream-provenance
fi
git pull --ff-only origin chore/sync-upstream-provenance
```

Record and inspect the exact commit and model path:

```bash
git rev-parse HEAD
git status --porcelain
test -z "$(git status --porcelain)"
jq -e '._runtime.model_path == "model/EdgeIMCI-4B-alpha-second-Q4_K_M.gguf"' metadata.json
test -f scripts/verify_model_artifact.py
```

The status command must print nothing before a retained profile. Record the actual checked-out SHA, not a guessed future commit. A development profile may use this branch, but rerun from the final submission commit after integration because the profiler records the checked-out commit in `submission.json`. Do not pull or edit the checkout during a run.

## 4. Download and Verify the GGUF

From the submission repository root:

```bash
bash download_model.sh
python3 scripts/verify_model_artifact.py
sha256sum model/EdgeIMCI-4B-alpha-second-Q4_K_M.gguf
stat --printf='%s bytes\n' model/EdgeIMCI-4B-alpha-second-Q4_K_M.gguf
```

Expected SHA-256:

```text
a4a8c5bb2d9f3401defa1cb8ea007812d5916c0242d8306a1c7ed6322d550919
```

Expected size:

```text
2497280288 bytes
```

Stop if verification fails or either value differs. The verifier uses only the Python standard library and streams the hash rather than loading the 2.5 GB file into RAM. Run it even when the model already exists: the template downloader may skip an existing file without checking its bytes. Official template rules permit downloader edits only to `MODEL_FILE` and `MODEL_URL`, so verification remains a separate step; do not add verification logic to the downloader.

## 5. Build the Pinned CPU `llama-bench`

The profiler requires `llama-bench` on `PATH`. Build this exact `llama.cpp` revision in its own directory, without replacing any historical build:

```bash
cd "$ADTC_HOME/repos"
git clone https://github.com/ggml-org/llama.cpp.git llama.cpp-4b-profile
cd llama.cpp-4b-profile
git checkout aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3

cmake -S . -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CUDA=OFF \
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
export PATH="$ADTC_HOME/repos/llama.cpp-4b-profile/build/bin:$PATH"
command -v llama-bench
git -C "$ADTC_HOME/repos/llama.cpp-4b-profile" rev-parse HEAD
sha256sum "$(command -v llama-bench)"
```

This pinned `llama-bench` does not support `--version`. Record its source commit and executable hash instead; benchmark JSON also reports the short build commit.

Run a short direct smoke test:

```bash
cd "$ADTC_HOME/repos/edgeIMCI-adtc-2026-submission"
llama-bench \
  -m model/EdgeIMCI-4B-alpha-second-Q4_K_M.gguf \
  -p 32 \
  -n 8 \
  -t 2 \
  -ngl 0 \
  --output json
```

The ADTC throughput profiler also forces zero GPU layers. `GGML_NATIVE=ON` targets this laptop's CPU; do not copy this binary to a different CPU and assume it is compatible. If this build directory already exists, verify its clean source checkout and exact pin instead of cloning or rebuilding over historical evidence.

The [2026-09-22 preliminary laptop result](../provenance/4B-alpha-second/profiling/2026-09-22-cpu/README.md) used a time-limited alternative: a native CPU build with `GGML_BLAS=OFF`, `-p 128 -n 32 -t 2 -ngl 0 -r 1`, and GNU time. Its source/build lived in disposable live-session storage; the model and results remained on the external flash drive. It is console-derived evidence, not a run of this OpenBLAS-enabled full workflow or a completed ADTC profile.

## 6. Install the Pinned ADTC Profiler

Install the official source pin and its default accuracy dependencies. The two explicit dependency versions match the official lock at this pin. A VCS install alone does not enforce that lock, so preserve the full resolved environment too:

```bash
source "$ADTC_HOME/venvs/adtc-profiler-4b/bin/activate"
export CMAKE_BUILD_PARALLEL_LEVEL=2
export CMAKE_ARGS="-DGGML_CUDA=OFF -DGGML_NATIVE=ON -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS"
uv pip install \
  --no-binary-package llama-cpp-python \
  "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git@7f117dde3d8f2a0b3d3f05948a7bfd4bf693e909" \
  "llama-cpp-python==0.3.34" "lm-eval==0.4.12"
uv pip check
python -c 'import llama_cpp, lm_eval; from importlib.metadata import version; print("llama-cpp-python", version("llama-cpp-python")); print("lm-eval", version("lm-eval"))'
adtc-profiler run --help
```

The official profiler `main` was confirmed at `7f117dde3d8f2a0b3d3f05948a7bfd4bf693e909` when preparing this runbook; use the pin, not a moving branch. Before a final submission run, check for a newer organizer-mandated revision. If it changes, record it and rerun the complete profile.

Accuracy runs the quantized GGUF in-process through **`llama-cpp-python`**, with its own bundled llama.cpp backend. It does not use the external `llama-bench` binary or inherit its source pin. Both paths must load this model successfully. Do not install CUDA or CUDA Torch for this CPU workflow; the default profiler accuracy stack is sufficient. A successful throughput smoke test alone does not validate the accuracy backend.

## 7. Capture Preflight Evidence

Create a unique timestamped run directory outside the Git checkout. Repeat this stage for every new attempt; never reuse or overwrite old result paths. Keep the same shell so `RUN_DIR` and cache variables remain set:

```bash
mkdir -p "$ADTC_HOME/artifacts"
RUN_DIR="$(mktemp -d "$ADTC_HOME/artifacts/4b-alpha-second-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")"
export RUN_DIR
mkdir "$RUN_DIR/smoke" "$RUN_DIR/cache-warm" "$RUN_DIR/retained"
cd "$ADTC_HOME/repos/edgeIMCI-adtc-2026-submission"

export ADTC_CPU_THREADS=2
date -u > "$RUN_DIR/start-utc.txt"
uname -a > "$RUN_DIR/uname.txt"
lsb_release -a > "$RUN_DIR/os-release.txt" 2>&1
lscpu > "$RUN_DIR/lscpu.txt"
free -h > "$RUN_DIR/memory-before.txt"
swapon --show > "$RUN_DIR/swap.txt"
findmnt > "$RUN_DIR/mounts.txt"
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS > "$RUN_DIR/storage.txt"
df -hT > "$RUN_DIR/disk-free.txt"
sensors > "$RUN_DIR/sensors-before.txt" 2>&1 || printf '%s\n' 'Sensors unavailable; see log.'
git rev-parse HEAD > "$RUN_DIR/submission-commit.txt"
git status --porcelain > "$RUN_DIR/worktree-status.txt"
test ! -s "$RUN_DIR/worktree-status.txt"
python3 scripts/verify_model_artifact.py > "$RUN_DIR/model-verification.txt" 2>&1
sha256sum model/EdgeIMCI-4B-alpha-second-Q4_K_M.gguf > "$RUN_DIR/model.sha256"
stat --printf='%s bytes\n' model/EdgeIMCI-4B-alpha-second-Q4_K_M.gguf > "$RUN_DIR/model-size.txt"
cp metadata.json download_model.sh "$RUN_DIR/"
sha256sum "$(command -v llama-bench)" > "$RUN_DIR/llama-bench.sha256"
git -C "$ADTC_HOME/repos/llama.cpp-4b-profile" rev-parse HEAD > "$RUN_DIR/llama-cpp-commit.txt"
cp "$ADTC_HOME/repos/llama.cpp-4b-profile/build/CMakeCache.txt" "$RUN_DIR/"
python --version > "$RUN_DIR/python-version.txt"
uv --version > "$RUN_DIR/uv-version.txt"
uv pip freeze > "$RUN_DIR/profiler-environment.txt"
python -c 'from importlib.metadata import distribution; print(distribution("adtc-profiler").read_text("direct_url.json"))' > "$RUN_DIR/profiler-source.json"
printf '%s\n' "ADTC_CPU_THREADS=$ADTC_CPU_THREADS" "CMAKE_ARGS=$CMAKE_ARGS" \
  "CMAKE_BUILD_PARALLEL_LEVEL=$CMAKE_BUILD_PARALLEL_LEVEL" \
  "ADTC_HOME=$ADTC_HOME" "XDG_CACHE_HOME=$XDG_CACHE_HOME" "XDG_DATA_HOME=$XDG_DATA_HOME" \
  "UV_INSTALL_DIR=$UV_INSTALL_DIR" "UV_PYTHON_INSTALL_DIR=$UV_PYTHON_INSTALL_DIR" \
  "UV_CACHE_DIR=$UV_CACHE_DIR" "UV_PYTHON_BIN_DIR=$UV_PYTHON_BIN_DIR" \
  "HF_HOME=$HF_HOME" "HF_DATASETS_CACHE=$HF_DATASETS_CACHE" "TMPDIR=$TMPDIR" \
  > "$RUN_DIR/run-settings.txt"
printf 'Evidence directory: %s\n' "$RUN_DIR"
```

`worktree-status.txt` must be empty. `ADTC_CPU_THREADS=2` controls the external throughput benchmark; do not assume it controls the separate accuracy backend, which uses its own defaults. Do not dump the entire environment into logs because it may contain credentials.

## 8. Run a Fast Participant Smoke Profile

Connect AC power, close unrelated applications, and let the laptop return to a stable idle temperature. Then run:

```bash
cd "$ADTC_HOME/repos/edgeIMCI-adtc-2026-submission"
source "$ADTC_HOME/venvs/adtc-profiler-4b/bin/activate"
export PATH="$ADTC_HOME/repos/llama.cpp-4b-profile/build/bin:$PATH"
export ADTC_CPU_THREADS=2

adtc-profiler run \
  --submission "$PWD" \
  --mode participant \
  --output "$RUN_DIR/smoke/submission.json" \
  --skip-accuracy 2>&1 | tee "$RUN_DIR/smoke/console.log"
```

Inspect the smoke report:

```bash
jq '{throughput, memory, cpu_thermal, reproducibility, model_info, accuracy}' \
  "$RUN_DIR/smoke/submission.json"
```

An empty `accuracy` array is expected only for this smoke run.

## 9. Warm the Accuracy Cache Online

While still online, run the complete pipeline once to exercise the separate accuracy backend and populate the persistent dataset cache. These explicit options are the pinned profiler's defaults: ARC-Easy, 50 items, seed 42. This is a small development check, not clinical qualification or the organizer's hidden audit benchmark:

```bash
unset HF_HUB_OFFLINE HF_DATASETS_OFFLINE
adtc-profiler run \
  --submission "$PWD" \
  --mode participant \
  --accuracy-task arc_easy --accuracy-limit 50 --seed 42 \
  --output "$RUN_DIR/cache-warm/submission.json" \
  2>&1 | tee "$RUN_DIR/cache-warm/console.log"
jq -e '.accuracy | type == "array" and length > 0' "$RUN_DIR/cache-warm/submission.json"
```

Do not proceed with an empty accuracy array, even if the process exited zero: participant mode can emit an empty array after an accuracy failure. Diagnose the console log for missing dependencies, unsupported model/backend, memory pressure, or download failures, then start a new attempt directory. Never relabel the smoke report as complete.

## 10. Retain a Complete Offline Profile

Only after a successful cache-warming run, keep the same environment and cache paths, allow the laptop to cool, and enable offline dataset access. Do not clear the cache between stages. If offline loading fails, return online to complete caching, then repeat in a new attempt directory; do not silently retain an online retry as an offline run.

```bash
export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
test -z "$(git status --porcelain)"
python3 scripts/verify_model_artifact.py
free -h > "$RUN_DIR/retained/memory-before.txt"
sensors > "$RUN_DIR/retained/sensors-before.txt" 2>&1 || printf '%s\n' 'Sensors unavailable; see log.'
printf '%s\n' "HF_HUB_OFFLINE=$HF_HUB_OFFLINE" "HF_DATASETS_OFFLINE=$HF_DATASETS_OFFLINE" \
  > "$RUN_DIR/retained/offline-settings.txt"
date -u > "$RUN_DIR/retained/start-utc.txt"
/usr/bin/time -v -o "$RUN_DIR/retained/time-and-rss.txt" \
  adtc-profiler run \
  --submission "$PWD" \
  --mode participant \
  --accuracy-task arc_easy --accuracy-limit 50 --seed 42 \
  --output "$RUN_DIR/retained/submission.json" \
  2>&1 | tee "$RUN_DIR/retained/console.log"
date -u > "$RUN_DIR/retained/end-utc.txt"
free -h > "$RUN_DIR/retained/memory-after.txt"
sensors > "$RUN_DIR/retained/sensors-after.txt" 2>&1 || printf '%s\n' 'Sensors unavailable; see log.'
```

The retained command must omit `--skip-accuracy`. The profiler's memory and thermal sampling wraps throughput, not the subsequent accuracy stage. Preserve the supplementary GNU `time -v` elapsed-time and maximum-RSS record for the full command as well; it is not a replacement for the profiler's defined memory metric or full-stage thermal monitoring.

Verify that accuracy is present and that the report captured the checked-out submission commit:

```bash
jq -e '.accuracy | type == "array" and length > 0' "$RUN_DIR/retained/submission.json"
jq -e '.accuracy | any(.benchmark == "arc_easy" and .samples == 50 and (.score | type == "number"))' \
  "$RUN_DIR/retained/submission.json"
jq -e '.reproducibility.random_seed == 42' "$RUN_DIR/retained/submission.json"
git status --porcelain > "$RUN_DIR/retained/worktree-status.txt"
test ! -s "$RUN_DIR/retained/worktree-status.txt"
git rev-parse HEAD > "$RUN_DIR/retained/submission-commit.txt"
cmp "$RUN_DIR/submission-commit.txt" "$RUN_DIR/retained/submission-commit.txt"
test "$(git rev-parse --short=12 HEAD)" = \
  "$(jq -r '.reproducibility.git_commit_sha' "$RUN_DIR/retained/submission.json")"
python3 scripts/verify_model_artifact.py > "$RUN_DIR/retained/model-verification.txt" 2>&1
```

All checks must pass, including a clean worktree, unchanged full commit, and the report's matching short commit. Inspect the measurements for missing/zero throughput, RSS, temperature availability, and throttling; do not infer an official hardware pass from the file size alone:

```bash
jq '{throughput, memory, accuracy, cpu_thermal, reproducibility, model_info}' \
  "$RUN_DIR/retained/submission.json"
```

Preserve hashes for all three reports and the retained run log:

```bash
sha256sum "$RUN_DIR/smoke/submission.json" "$RUN_DIR/cache-warm/submission.json" \
  "$RUN_DIR/retained/submission.json" "$RUN_DIR/retained/console.log" \
  > "$RUN_DIR/results.sha256"
```

## Final-Run Rules

- Use the exact final submission commit with a clean worktree.
- Use the exact GGUF bytes and verify their size and SHA-256.
- Keep the laptop connected to AC power.
- Use two throughput threads on the documented two-core laptop; record any hardware or thread-count difference.
- Do not use GPU offload.
- Close background workloads and allow the laptop to cool between runs.
- Do not retain a report with an empty accuracy array.
- Preserve the entire unique run directory: all reports and hashes, console logs, Git commit and clean status, environment and build capture, model checksum and size, runtime versions, memory/RSS, timing, and sensor records. Back it up before rebooting a USB session.
- Rerun the complete profile after any model, metadata, profiler, runtime, or submission commit change.

## Separate Application Acceptance

Profiling requires `llama-bench`; it does not require the GUI, Node.js, Modal, or `llama-completion`.

The template GUI and its historical acceptance path still target the legacy 0.6B model and are **not integrated with the selected 4B artifact**. Do not use `setup.sh`, `run.sh`, or historical GUI acceptance results to validate this model. Application integration and clinical/domain acceptance are separate work; this runbook only produces participant profiling evidence.
