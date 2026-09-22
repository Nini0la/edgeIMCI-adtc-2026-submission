# Technical Report - EdgeIMCI Offline Structured Extraction

**Team ID:** edge-imci

**Domain:** healthcare_medical

**Selected model:** EdgeIMCI-4B-alpha-second-Q4_K_M

## Problem and Scope

EdgeIMCI converts primary-healthcare worker descriptions of sick-child findings into bounded encounter JSON for validation and deterministic IMCI logic. Local inference targets settings with limited connectivity and computing resources without sending encounter text to an external inference service. The enriched training also targets bounded free-form behavior, which is not established by the extraction-only evidence below.

The owner selected 4B-alpha-second for public hosting, submission-template updates, and Ubuntu profiling. That decision is distinct from independent clinical approval. This is not a diagnostic system, production medical device, or authorization for autonomous clinical use. The existing GUI backend remains checksum/prompt-pinned to 0.6B and is not compatible with the selected 4B artifact; official standalone profiling does not require the Node GUI.

## Model Provenance (Gate 2)

| Item | Recorded evidence |
|---|---|
| Base model source | [Qwen/Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B/tree/1cfa9a7208912126459214e8b04321603b3df60c), Apache-2.0 |
| Base and tokenizer revision | `1cfa9a7208912126459214e8b04321603b3df60c` |
| Run | `multitask2258-20260922-v1--qwen4-e2-lr3-s20260824` |
| Method | BF16 LoRA SFT, not QLoRA; terminal epoch-2 export, adapter merged |
| Recipe | 2 epochs; LR 0.0003; seed 20260824; rank 16; alpha 32; dropout 0.05 |
| Optimization | Effective batch 16; cosine schedule; warmup 0.05; weight decay 0.01; assistant-only loss |
| Tokenization | Thinking disabled; maximum length 3072; no truncation |
| Final file | `EdgeIMCI-4B-alpha-second-Q4_K_M.gguf`, 2,497,280,288 bytes |
| Final SHA-256 | `a4a8c5bb2d9f3401defa1cb8ea007812d5916c0242d8306a1c7ed6322d550919` |
| Hosting | `Nini0la/edgeimci-4b-alpha-second-gguf` at `1aeace1a2eb6e46e5e93d6536cbd1c19db982e53`; see [`artifact.json`](provenance/4B-alpha-second/artifact.json) |

The original [`training_config.json`](provenance/4B-alpha-second/training_config.json), [`trainer_log_history.json`](provenance/4B-alpha-second/trainer_log_history.json), [`remote_run_manifest.json`](provenance/4B-alpha-second/remote_run_manifest.json), and [`artifact_hashes.json`](provenance/4B-alpha-second/artifact_hashes.json) bind the recipe, run, and source outputs. Epoch validation loss was 0.02655767 then 0.01106639; lower loss alone does not establish behavioral improvement. Original receipts retain their research-only authorization flags; subsequent owner selection does not rewrite them or grant clinical approval.

The original LoRA adapter is public in the HF repository's `adapter/` directory at the same immutable pin. Anonymous hosting metadata verifies the weight hash and size; the adapter configuration's bytes also match its original checksum. `python3 provenance/4B-alpha-second/download_adapter.py` retrieves and verifies both files. Adapter weights are not vendored in Git, and organizer acceptance of this hosted arrangement should be confirmed. The base revision, final hosted artifact revision, and submission-repository revision are different identities. The profiler records the latter; do not add `reproducibility.git_commit_sha` to `metadata.json`.

### Dataset

`beta0_1k_multitask_enriched_2258_v1` is project-authored synthetic multitask data from the EdgeIMCI research workspace, extending the 1,831-row baseline by 427 examples. It covers extraction, free-form assessment language, project self-knowledge, scope/safety, and proposition/negation. The clinical source background is WHO's *IMCI Chart Booklet* (March 2014); the examples are not WHO-authored and the booklet is not redistributed.

The public package is [Nini0la/edgeimci-beta0-1k-multitask-enriched-2258-v1](https://huggingface.co/datasets/Nini0la/edgeimci-beta0-1k-multitask-enriched-2258-v1/tree/da8daa8efbd583d92000920366085f6dd00c3fb2), pinned to immutable revision `da8daa8efbd583d92000920366085f6dd00c3fb2`. Anonymous `datasets` loading returned exactly 2,258 TRAIN and 139 VALIDATION rows. The release preserves the frozen partitions without reshuffling, resplitting, or TEST data.

| Partition/artifact | Rows | Frozen training SHA-256 | Public package SHA-256 |
|---|---:|---|---|
| TRAIN JSONL | 2,258 | `95945aa2e451f67348f4600e57c17e4a4acd278f285f2f1fbea9df4b633805f7` | `475934f7def41d3825f4544f7bc911588c58715a7df8946d4337607eb2cf8c78` |
| TRAIN Parquet | 2,258 | Not applicable | `f9334b24e9f440cfd21e85d7b3dcb50a404fe22390708e8ddf3ccb0320aaf670` |
| VALIDATION JSONL | 139 | `76dc64d51f52a8ffbb7a10c5fd10a3fff770a7ee6847cf7fb62c9a00568a58c5` | `76dc64d51f52a8ffbb7a10c5fd10a3fff770a7ee6847cf7fb62c9a00568a58c5` |
| VALIDATION Parquet | 139 | Not applicable | `e66f04506b46ac09483c80adda95f557b8862ed69db567b46d57ca9f79327ff2` |
| Source manifest | Not applicable | `0820f092ed585a46182e075477f9246917629061b03a3f57d92cb1087e303706` | Included as frozen identity |

The final internal TRAIN file was not retained in reachable repository state, so the public JSONL is a deterministic message-normalized reconstruction from the hash-verified 1,831-row baseline and 427-record enrichment source; it does not claim byte identity to the frozen TRAIN serialization. VALIDATION is byte-identical. The public repository uses `license: other` and asserts no general redistribution license while source-rights review remains incomplete. Independent clinical review is also pending. See [`dataset_info.md`](provenance/4B-alpha-second/dataset_info.md) and [`publication.json`](provenance/dataset/publication.json).

### Before/After Fine-Tuning

An actual three-prompt paired demonstration was completed on 2026-09-22. The pinned untouched base and merged 4B-alpha-second used identical rendered prompts/input IDs and effective generation settings: BF16 on NVIDIA L4, greedy decoding, seed 0, thinking disabled, maximum 1200 new tokens.

| Fixed public example | Untouched Qwen3-4B | Fine-tuned 4B-alpha-second |
|---|---|---|
| Public prompt 001: urgent incomplete encounter | `{"route":"INFORMATIONAL_NON_ENCOUNTER"}` | Exact expected encounter JSON |
| Public prompt 002: complete diarrhoea encounter | `{"route":"INFORMATIONAL_NON_ENCOUNTER"}` | Exact expected encounter JSON |
| Free-form question about EdgeIMCI and its rules engine | Longer explanation including language-model generation of "diagnostic recommendations" | Concise explanation placing authority in deterministic IMCI logic |

Extraction exact agreement on these examples was 0/2 versus 2/2. This illustrates learned project-specific formatting/routing; the complete custom schema was not provided in the prompt, and training overlap is not ruled out. It is not a held-out benchmark or evidence of improved clinical reliability. Full prompts, all six raw outputs, settings, limitations, and the reproducible runner are in [`before_after.md`](provenance/4B-alpha-second/before_after.md) and [`before_after_results.json`](provenance/4B-alpha-second/before_after_results.json).

The following table remains the separate 139-row terminal-checkpoint validation result, not a full evaluation of the GGUF. The base has not been evaluated on all 139 rows, so no validation-set improvement is claimed.

| VALIDATION metric | Pinned base before SFT | Fine-tuned terminal checkpoint |
|---|---|---:|
| JSON valid | Pending matched evaluation | 139/139 |
| Strict schema valid | Pending matched evaluation | 135/139 |
| Whole-prediction exact | Pending matched evaluation | 131/139 |
| Routing correct | Pending matched evaluation | 132/139 |
| False rejects | Pending matched evaluation | 2/119 |
| Unsafe engine admissions | Pending matched evaluation | 1/20 |
| Urgent misses | Pending matched evaluation | 2/4 |

The small routing denominators and pending clinical gold review limit interpretation. A broader matched-base validation study remains future work; the paired public examples and F16-versus-Q4 smoke are not substitutes for it. Do not use the sealed TEST set for that work.

### Merge and Quantization

The recipe records post-training adapter merging and the original source inventory binds the exported merged checkpoint. The historical merge implementation is not recovered in this packet. Conversion verified all 14 merged-model files against that inventory, then used `llama.cpp` commit `aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3` to create an F16 control and Q4_K_M, as recorded in [`merge_quantization.md`](provenance/4B-alpha-second/merge_quantization.md) and [`conversion_manifest.json`](provenance/4B-alpha-second/conversion_manifest.json).

Q4_K_M provides a smaller candidate for laptop profiling (2,497,280,288 bytes versus 8,051,284,768 for F16). Both passed **2/2 public prompts**, with exact parsed JSON targets and matching `URGENT_INCOMPLETE` / `COMPLETE` states. The smoke used the extraction-v2 wrapper, thinking disabled, temperature 0, seed 0, context 3072, and at most 1200 generated tokens on Modal CPU. [`smoke_results.json`](provenance/4B-alpha-second/smoke_results.json) retains outputs. This is not full quantization-drift validation, Transformers equivalence, raw free-form testing, or target-laptop profiling.

Actual before/after examples are now retained. Organizer acceptance of hosted adapter delivery, consolidated dataset/source-license review, and complete ADTC profiling remain unresolved. Independent clinical review remains pending; this report does not authorize clinical use.

## Target Profiling

The target is an 8 GB-class laptop using CPU `llama.cpp`. A **preliminary direct CPU microbenchmark** of 4B-alpha-second completed on 2026-09-22. Its evidence is the operator's pasted console output, transcribed in the [profiling evidence packet](provenance/4B-alpha-second/profiling/2026-09-22-cpu/README.md); the original flash-drive files have not yet been imported or independently inspected.

| Preliminary 4B-alpha-second metric | Reported result |
|---|---|
| Machine | Intel Core i5-4210U, Ubuntu live USB; earlier session preflight reported 11 GiB RAM and no swap |
| Artifact identity | Reported SHA-256 matches the selected Q4_K_M GGUF above |
| Runtime | `llama-bench` build `aedb2a5`; requested full pin `aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3` |
| Configuration | CPU-only, 2 threads, zero GPU layers, one repetition per test; requested native build with BLAS disabled |
| Prompt processing | **12.150088 tokens/s**, 128 tokens in 10.534903420 s |
| Generation | **5.418514 tokens/s**, 32 tokens in 5.905677684 s |
| GNU time maximum RSS | **4,259,852 KiB (4.063 GiB)** |
| Whole-command elapsed time | 148.10 seconds, including loading, warmup and both tests |
| Exit status | 0 |

The two rows are separate synthetic tests, not a complete clinical interaction. One repetition does not establish variability; zero reported standard deviation is not evidence of stability. GNU time RSS is not total system memory or the official profiler's sampled memory metric. The 11 GiB machine and short workload do not establish an 8 GB deployment pass. No controlled comparison against the historical 0.6B workloads is claimed.

**Full profiling remains pending:** original evidence import, repeatability, time to first token, sustained thermals, accuracy and a complete scoreable ADTC report. Use [`docs/PROFILING_RUNBOOK.md`](docs/PROFILING_RUNBOOK.md) for that workflow and verify the exact GGUF separately with `python3 scripts/verify_model_artifact.py`. The official downloader retains its template logic; only `MODEL_FILE` and `MODEL_URL` changed. This microbenchmark does not complete Gate 2 or clinical qualification.

## Historical Benchmarks: Different Artifact

**HISTORICAL DIFFERENT ARTIFACT: every figure in this section belongs to the old 0.6B model, not 4B-alpha-second.** These participant measurements are retained for traceability, not carried forward as current scores.

The old Q8_0 choice preserved the tested JSON output and scored 0.64 on a 50-sample ARC-Easy smoke, versus 0.50 for the old Q4_K_M. BF16, Q8_0 and Q4_K_M all passed the retained JSON/schema/exact-output smoke. The old Q4 was faster and smaller, but the observed accuracy difference favored Q8_0. None of that establishes the new 4B quantization tradeoff.

| Historical 0.6B metric | Value |
|---|---|
| Machine | ASUS / Intel Core i5-4210U (2 cores/4 threads) / Ubuntu 22.04.5; 11 GiB RAM, no swap |
| GGUF | Q8_0, 639,446,752 bytes, SHA-256 `26d11ee99801455fcef011a3e5ff124b2ff1cce943ed06cbe611c8fbcc42aca2` |
| `llama.cpp` | `aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3` (`b9637`); CPU-only, no GPU offload |
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

The old ADTC quick profile used `--skip-accuracy`; accuracy was measured separately with the same pinned profiler and exact old Q8_0 bytes. These are not organizer audit results or a complete final profile. The six previously documented clinical-threshold failures also belong to that old project evaluation, not the newly selected 4B fine-tune. The new checkpoint's observed errors are disclosed in its own validation table above.
