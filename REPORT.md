# Technical Report - EdgeIMCI Offline Structured Extraction

**Team ID:** edgeimci
**Domain:** healthcare_medical
**Model:** EdgeIMCI-Qwen3-0.6B-SFT-Q8_0

---

## Problem

EdgeIMCI converts primary-healthcare worker descriptions of sick-child findings into a bounded JSON encounter record. The target setting is frontline care where connectivity, cloud budgets, and access to high-end computing are limited. Local inference keeps the extraction path available offline and avoids sending encounter text to an external inference service.

This model is not a diagnostic system and is not authorized for production clinical use. Its output is recoverable encounter state for a constrained downstream workflow. The selected research checkpoint passed JSON/schema validity but retained documented clinical-threshold failures in the project evaluation.

---

## Design Decisions

- **Base model:** Qwen/Qwen3-0.6B at revision `c1899de289a04d12100db370d81485cdf75e47ca` (Apache-2.0).
- **Fine-tuning:** LoRA structured-extraction SFT, merged after training; 3 epochs, learning rate 0.0002, seed 20260824.
- **Runtime:** CPU-only `llama.cpp`, converted and quantized at commit `aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3`.
- **Quantization:** Q8_0 was selected because it preserved the tested JSON output exactly and scored 0.64 on the profiler's 50-sample ARC-Easy check, compared with 0.50 for Q4_K_M.
- **Alternatives:** BF16, Q8_0, and Q4_K_M all passed the retained JSON parse, schema, and exact-output smoke check. Q4_K_M was faster and smaller, but its observed accuracy reduction outweighed those gains because accuracy is half of the ADTC score.
- **Final artifact:** `qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf`, 639,446,752 bytes (609.82 MiB), SHA-256 `26d11ee99801455fcef011a3e5ff124b2ff1cce943ed06cbe611c8fbcc42aca2`.
- **Hosting:** Hugging Face repository `Nini0la/edgeimci-qwen3-0.6b-sft-gguf`, model commit `6af69949d91fbe2628d88a6ed7df62a944cd71a3`. The download script pins that immutable revision and fails closed on a checksum mismatch.

---

## Constraints

- Target profile: an 8 GB-class laptop with integrated graphics and CPU inference.
- Development device: ASUS laptop, Ubuntu 22.04.5 LTS, Intel Core i5-4210U (2 cores/4 threads), 11 GiB installed RAM, and no swap.
- No GPU offload was used for the retained `llama-bench` comparison.
- The model and runtime operate offline after the one-time model download.
- The GGUF is approximately 610 MB, leaving substantial headroom under the challenge memory limit.

---

## Benchmarks

| Metric | Value |
|---|---|
| Machine | ASUS / Intel Core i5-4210U / Ubuntu 22.04.5 |
| GGUF | Q8_0, 639,446,752 bytes, SHA-256 `26d11ee99801455fcef011a3e5ff124b2ff1cce943ed06cbe611c8fbcc42aca2` |
| `llama.cpp` | `aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3` (`b9637`) |
| Prompt processing | 65.59 tokens/s (`llama-bench`, 512 tokens) |
| Generation speed | 21.72 tokens/s (`llama-bench`, 128 tokens) |
| ADTC quick-profile generation | 18.94 tokens/s |
| First-token latency | 8,851.28 ms |
| Peak / steady RSS | 774.59 MB / 729.21 MB |
| Peak VMS | 1,304.30 MB |
| Peak temperature | 75.0 C |
| CPU utilization p99 | 64.0% |
| Thermal throttling | No |
| Self-reported performance / efficiency | 100.00 / 89.19 |
| Accuracy smoke | ARC-Easy acc_norm 0.64, 50 samples |
| Structured extraction smoke | JSON parse PASS; schema PASS; exact match PASS |

The ADTC quick participant profile used `--skip-accuracy`; accuracy was measured separately with the same pinned profiler and exact Q8_0 bytes. These are participant development measurements from the target ASUS, not organizer audit results. A complete participant report without `--skip-accuracy` remains a separate finalization step, and organizer audit measurements may differ.
