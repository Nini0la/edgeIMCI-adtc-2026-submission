# Gate 2 Model Provenance Handoff

**Status: incomplete.** The selected submission/profiling candidate is **4B-alpha-second**, the enriched 2,258-row run. The owner authorized public hosting, submission-template updates, and Ubuntu profiling. This is distinct from clinical approval; original research-only receipts remain unchanged, and clinical use is not authorized.

## Selected Candidate

| Field | Value |
|---|---|
| Evidence packet | [`4B-alpha-second/`](4B-alpha-second/README.md) |
| Run | `multitask2258-20260922-v1--qwen4-e2-lr3-s20260824` |
| Base model | `Qwen/Qwen3-4B`, Apache-2.0 |
| Base/tokenizer revision | `1cfa9a7208912126459214e8b04321603b3df60c` |
| Recipe | BF16 LoRA; 2 epochs, LR 0.0003, seed 20260824, rank 16, alpha 32, dropout 0.05 |
| Final GGUF | `EdgeIMCI-4B-alpha-second-Q4_K_M.gguf`, 2,497,280,288 bytes |
| Final SHA-256 | `a4a8c5bb2d9f3401defa1cb8ea007812d5916c0242d8306a1c7ed6322d550919` |
| Public hosting destination | `Nini0la/edgeimci-4b-alpha-second-gguf` |
| Hosted pin | `1aeace1a2eb6e46e5e93d6536cbd1c19db982e53`; see [`artifact.json`](4B-alpha-second/artifact.json) |

## Evidence Inventory

- [`training_config.json`](4B-alpha-second/training_config.json): original LoRA/optimization/tokenization settings and software pins.
- [`remote_run_manifest.json`](4B-alpha-second/remote_run_manifest.json): original successful source receipt, checkpoint history, dataset hashes, and terminal evaluation.
- [`trainer_log_history.json`](4B-alpha-second/trainer_log_history.json): retained training and loss logs.
- [`artifact_hashes.json`](4B-alpha-second/artifact_hashes.json): original adapter and merged-checkpoint inventory, not the weight files themselves.
- [`dataset_info.md`](4B-alpha-second/dataset_info.md): exact enriched release identity, 2,258 TRAIN / 139 VALIDATION records, hashes, split policy, sources and disclosure gaps.
- [`merge_quantization.md`](4B-alpha-second/merge_quantization.md) and [`conversion_manifest.json`](4B-alpha-second/conversion_manifest.json): recorded merge policy, verified source files, F16/Q4 conversion commands and hashes; historical merge implementation is not recovered here.
- [`smoke_results.json`](4B-alpha-second/smoke_results.json): F16 and Q4 each pass 2/2 public prompts for exact parsed JSON and deterministic state under the recorded wrapper.
- [`before_after.md`](4B-alpha-second/before_after.md): terminal fine-tuned results with an explicitly missing matched-base comparison.

The original adapter is public in the HF repository's `adapter/` directory at the same immutable revision. [`artifact.json`](4B-alpha-second/artifact.json) binds its exact hashes and sizes; `python3 provenance/4B-alpha-second/download_adapter.py` fetches and verifies the weights/config into an ignored local directory. Git retains provenance and hosted references, not vendored weights. Do not equate an inventory of original files with independently downloadable training inputs or a completed Gate 2 packet.

## Remaining Work

- Confirm organizer acceptance of public immutable adapter hosting plus the fetch helper rather than large weight blobs in Git.
- Complete consolidated dataset/source-license review. The public message-normalized release is pinned at [Hugging Face revision `da8daa8efbd583d92000920366085f6dd00c3fb2`](https://huggingface.co/datasets/Nini0la/edgeimci-beta0-1k-multitask-enriched-2258-v1/tree/da8daa8efbd583d92000920366085f6dd00c3fb2), but its `license: other` declaration does not establish redistribution rights.
- Complete matched pinned-base-versus-fine-tuned evaluation with identical authorized held-out inputs and evaluation settings; do not use the sealed TEST set.
- Run actual target-laptop Ubuntu profiling on the exact selected GGUF and retain the complete scoreable ADTC evidence. No old performance figures transfer to 4B.
- Complete independent clinical/source-governance review before any clinical-use claim. Hosting/profiling selection is not that approval.

The GUI backend, checksum, and prompt remain pinned to 0.6B. Runtime migration is not part of this selection: legacy `setup.sh`, `run.sh`, and integration verification are not compatible with 4B. Official artifact profiling is independent of the Node GUI.


## Historical 0.6B Artifact

This is the old submission model and the still-pinned GUI integration, **not the selected 4B profiling artifact**. Its original training dataset, complete logs, adapter, and merge path have not been linked here. Do not fill those gaps with either later campaign's evidence.

| Field | Historical value |
|---|---|
| Base | `Qwen/Qwen3-0.6B` at `c1899de289a04d12100db370d81485cdf75e47ca` |
| Recipe | LoRA SFT, merged; 3 epochs, LR 0.0002, seed 20260824 |
| GGUF | `qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf`, Q8_0 |
| SHA-256 | `26d11ee99801455fcef011a3e5ff124b2ff1cce943ed06cbe611c8fbcc42aca2` |
| Hosting | `Nini0la/edgeimci-qwen3-0.6b-sft-gguf` at `6af69949d91fbe2628d88a6ed7df62a944cd71a3` |
| Conversion revision | `aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3` |

Its benchmark figures and six clinical-threshold failures remain historical, as labeled in [`REPORT.md`](../REPORT.md), and are not claims about the new 4B model.
