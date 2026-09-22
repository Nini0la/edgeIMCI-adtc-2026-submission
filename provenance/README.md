# Gate 2 Model Provenance Handoff

**Status:** Incomplete. The two Beta0-1K candidate runs below now have documented dataset, recipe, run, and validation records. Neither candidate is the GGUF currently declared in `metadata.json`, and neither is authorized for promotion, deployment, or clinical use.

## Current Submission Artifact

The currently packaged artifact is still the 0.6B GGUF. Its original training dataset, complete training logs, adapter, and merge path have not yet been linked to this repository.

| Field | Value |
|---|---|
| Base model source | `huggingface:Qwen/Qwen3-0.6B` |
| Base model commit | `c1899de289a04d12100db370d81485cdf75e47ca` |
| Fine-tuning method | LoRA structured-extraction SFT, merged after training |
| Training summary | 3 epochs, learning rate 0.0002, seed 20260824 |
| Final GGUF | `qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf` |
| Final GGUF SHA-256 | `26d11ee99801455fcef011a3e5ff124b2ff1cce943ed06cbe611c8fbcc42aca2` |
| Hosted artifact revision | `6af69949d91fbe2628d88a6ed7df62a944cd71a3` |
| `llama.cpp` conversion revision | `aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3` |
| Quantization | GGUF Q8_0 |

Do not use the Beta0-1K candidate records to fill the current artifact's `metadata.json` provenance. That would incorrectly attribute the 0.6B GGUF to a different base model and training campaign.

## Shortlisted Candidate Runs

These runs were explicitly shortlisted for provenance review. Both completed successfully in campaign `multitask1831-20260922-v1`.

| Candidate | Base model | Epochs | Learning rate | Seed | Status |
|---|---|---:|---:|---:|---|
| [`qwen17-e3-lr1-s3407`](qwen17-e3-lr1-s3407.json) | `Qwen/Qwen3-1.7B` | 3 | 0.0001 | 3407 | Research candidate only |
| [`qwen4-e2-lr3-s20260824`](qwen4-e2-lr3-s20260824.json) | `Qwen/Qwen3-4B` | 2 | 0.0003 | 20260824 | Research candidate only |

Shared evidence:

- [`dataset_info.md`](dataset_info.md): exact dataset identity, counts, hashes, split policy, and authorization boundary.
- [`training_recipe.md`](training_recipe.md): shared LoRA recipe and the parameters that differ between candidates.
- [`evaluation.md`](evaluation.md): terminal validation comparison and limitations.

The candidate records deliberately omit laptop inference profiling, GGUF conversion, quantization, and runtime measurements. Those facts must be produced for the exact final bytes after a candidate is selected and packaged.

## Remaining Submission Work

- Decide which candidate, if either, replaces the current 0.6B submission artifact.
- Record an explicit promotion decision after the pending independent clinical and source-governance review.
- Export and preserve the chosen merged checkpoint or adapter from the recorded artifact manifest.
- Produce reproducible merge, GGUF conversion, and quantization commands for the chosen candidate.
- Host the exact GGUF at an immutable public revision and record its byte count and SHA-256.
- Update `metadata.json`, `MODEL_CARD.md`, `download_model.sh`, runtime constants, and tests together.
- Run public-prompt validation and laptop profiling against those exact final bytes.

The current `metadata.json` still lacks `provenance.training_datasets`. It should remain unresolved rather than being populated with the Beta0-1K release until the submitted GGUF is actually derived from one of these candidate runs.
