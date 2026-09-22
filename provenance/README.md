# Gate 2 Model Provenance Handoff

**Status:** Incomplete. This directory is a handoff checklist, not a completed Gate 2 evidence bundle. Replace each pending item with the original artifact or a reproducible record before submission.

## Established Facts

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

## Required Inputs

The following evidence is not yet present and must not be inferred or fabricated:

- Original LoRA adapter weights, or the complete training scripts and configuration needed to reproduce them.
- Training and validation logs, including the loss history and checkpoint-selection evidence.
- Dataset names, source URLs, versions, licenses, split policy, and checksums.
- Commands and tool versions used to merge the LoRA adapter into the base checkpoint.
- Commands and tool versions used to convert and quantize the merged checkpoint to GGUF Q8_0.
- A reproducible comparison of the pinned base model and final fine-tuned model on a held-out structured-extraction set.

## Expected Final Layout

Use the applicable files when the source materials become available; do not create empty substitutes for missing evidence.

```text
provenance/
├── adapter_model.safetensors   # or complete training scripts/configuration
├── training_log.txt
├── dataset_info.md
├── merge_quantization.md
└── evaluation.md
```

`dataset_info.md` should identify every training and validation source and include checksums for local or derived datasets. `merge_quantization.md` should make the path from the pinned base checkpoint to the hosted GGUF reproducible. `evaluation.md` should document prompts, dataset split, decoding settings, schema-validity rate, exact-match results, and representative base-versus-fine-tuned outputs.
