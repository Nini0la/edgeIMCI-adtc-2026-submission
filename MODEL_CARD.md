# EdgeIMCI-4B-alpha-second-Q4_K_M

## Summary

4B-alpha-second is the enriched 2,258-row LoRA fine-tune of `Qwen/Qwen3-4B`, run `multitask2258-20260922-v1--qwen4-e2-lr3-s20260824`, exported at terminal epoch 2 and quantized to GGUF Q4_K_M. The owner selected it for public hosting, submission-template updates, and Ubuntu profiling, not clinical deployment.

Its structured mode extracts bounded sick-child encounter JSON for schema validation and downstream deterministic IMCI logic. Training also targets bounded free-form behavior; the retained validation and public smoke do not establish comprehensive free-form safety or effectiveness.

## Artifact and Training

| Field | Value |
|---|---|
| File | `EdgeIMCI-4B-alpha-second-Q4_K_M.gguf` |
| Size | 2,497,280,288 bytes |
| SHA-256 | `a4a8c5bb2d9f3401defa1cb8ea007812d5916c0242d8306a1c7ed6322d550919` |
| Hosting destination | [Nini0la/edgeimci-4b-alpha-second-gguf](https://huggingface.co/Nini0la/edgeimci-4b-alpha-second-gguf) |
| Hosted pin | `1aeace1a2eb6e46e5e93d6536cbd1c19db982e53`; see [`artifact.json`](provenance/4B-alpha-second/artifact.json) |
| Base source | [Qwen/Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B/tree/1cfa9a7208912126459214e8b04321603b3df60c) |
| Base/tokenizer revision | `1cfa9a7208912126459214e8b04321603b3df60c` |
| Model source license | Apache-2.0 |
| Fine-tuning | BF16 LoRA, not QLoRA; adapter merged after training |
| Recipe | 2 epochs, LR 0.0003, seed 20260824; rank 16, alpha 32, dropout 0.05 |
| Data | [`beta0_1k_multitask_enriched_2258_v1`](https://huggingface.co/datasets/Nini0la/edgeimci-beta0-1k-multitask-enriched-2258-v1/tree/da8daa8efbd583d92000920366085f6dd00c3fb2) at `da8daa8efbd583d92000920366085f6dd00c3fb2`: TRAIN 2,258; VALIDATION 139; no TEST use recorded |
| Conversion | `llama.cpp` commit `aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3`; F16 then Q4_K_M |

Original configuration, training/loss logs, source receipt, artifact hashes, and conversion/smoke records are in [`provenance/4B-alpha-second/`](provenance/4B-alpha-second/README.md). The original adapter is public under HF `adapter/` at the hosted pin; its checksums are recorded in `artifact.json` and the fetch helper verifies both files. Weights are not vendored in Git; organizer acceptance of hosted adapter delivery should be confirmed. The public dataset provides a message-normalized TRAIN reconstruction from sources, not byte-identical to the original training file, and byte-identical VALIDATION JSONL, with Parquet publication views. Its card uses `license: other` and asserts no general redistribution license while source-rights review remains incomplete. The base model's Apache-2.0 license does not settle dataset rights; this submission repository is GPL v3.

## Evaluation

| Terminal checkpoint VALIDATION metric | Result |
|---|---:|
| JSON valid | 139/139 |
| Strict schema valid | 135/139 |
| Whole-prediction exact | 131/139 |
| Routing correct | 132/139 |
| False rejects | 2/119 |
| Unsafe engine admissions | 1/20 |
| Urgent misses | 2/4 |

These are terminal fine-tuned checkpoint results, not a full Q4 validation run. F16 and Q4 each passed 2/2 public extraction prompts with exact parsed JSON and matching deterministic states under the extraction-v2 wrapper, thinking disabled, temperature 0, seed 0, context 3072, and maximum generation 1200 tokens. That small smoke does not establish quantization equivalence beyond those prompts.

A [preliminary Ubuntu CPU microbenchmark](provenance/4B-alpha-second/profiling/2026-09-22-cpu/README.md) on 2026-09-22 reported 12.15 tokens/s for 128-token prompt processing, 5.42 tokens/s for 32-token generation, and GNU time maximum RSS of 4.063 GiB on an Intel Core i5-4210U with two threads and no GPU offload. It used one repetition per test and is recorded from the operator's pasted console output; original raw-file import is pending. This is not an accuracy evaluation, full ADTC profile, or official 8 GB qualification.

A [three-prompt paired base-versus-fine-tuned demonstration](provenance/4B-alpha-second/before_after.md) is retained: on two public extraction examples, exact-target agreement was 0/2 for the base and 2/2 for the merged fine-tune; a third free-form response pair is reported qualitatively. This illustrates learned project-specific behavior, not held-out quality or clinical reliability. Broader matched validation, repeatability measurements, sustained thermals, ARC-Easy and a complete scoreable ADTC report remain **pending**. See [`REPORT.md`](REPORT.md) and [`provenance/README.md`](provenance/README.md).

## Intended Use and Limits

Use is limited to research and competition evaluation with human review. The supported submission path is standalone artifact profiling, which does not require Node.js or a GUI. **The bundled GUI backend and integration verification scripts remain pinned to the old 0.6B checksum/prompt and are not compatible with this 4B model.** `setup.sh` / `run.sh` are not a working 4B demonstration.

The model may omit findings, misread negation, emit invalid schemas, misroute inputs, or miss urgent conditions, as the retained results demonstrate. Independent clinical/manual fact-fidelity review is pending; the validation set is small and not clinical effectiveness evidence. Owner selection for hosting/profiling is not clinical approval. Autonomous or production clinical use is not authorized.

Historical 0.6B benchmark results and its six clinical-threshold failures describe a different artifact and must not be attributed to this model.
