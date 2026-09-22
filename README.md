# EdgeIMCI ADTC 2026 Submission

EdgeIMCI is an offline research model for primary-healthcare sick-child encounters. Its structured-extraction mode converts worker findings into bounded JSON for validation and downstream deterministic IMCI logic. This is team `edge-imci`'s Laptop LLM submission package in `healthcare_medical`.

**The submitted artifact is the standalone 4B-alpha-second Q4_K_M GGUF.**

**Legacy Experimental GUI:** Retained for historical context. It uses an earlier model integration and is not the interface evaluated in this submission. Extraction reliability and error handling remain under development.

## Selected Artifact

`main` is the final submission branch. See the [integration review](docs/SUBMISSION_INTEGRATION.md)
for branch disposition, retained historical evidence, and published-snapshot errata.

The owner selected **4B-alpha-second**, the enriched 2,258-row fine-tune, for public hosting, submission-template updates, and Ubuntu profiling. This selection is not clinical approval or a declaration that Gate 2 is complete.

| Field | Value |
|---|---|
| Model | EdgeIMCI-4B-alpha-second-Q4_K_M |
| Base | `Qwen/Qwen3-4B` |
| Base revision | `1cfa9a7208912126459214e8b04321603b3df60c` |
| Training run | `multitask2258-20260922-v1--qwen4-e2-lr3-s20260824` |
| Runtime / format | `llama.cpp` / GGUF Q4_K_M |
| File | `EdgeIMCI-4B-alpha-second-Q4_K_M.gguf` |
| Size | 2,497,280,288 bytes |
| SHA-256 | `a4a8c5bb2d9f3401defa1cb8ea007812d5916c0242d8306a1c7ed6322d550919` |
| Hosting destination | [Nini0la/edgeimci-4b-alpha-second-gguf](https://huggingface.co/Nini0la/edgeimci-4b-alpha-second-gguf) |

The public GGUF and original adapter are pinned to Hugging Face revision `1aeace1a2eb6e46e5e93d6536cbd1c19db982e53`. Anonymous hosting metadata matches the expected sizes and weight hashes. See [`artifact.json`](provenance/4B-alpha-second/artifact.json) and the static `download_model.sh`; do not substitute `main` or confuse this pin with the base-model revision.

## Download and Profile

**The supported 4B path is artifact verification and standalone official profiling, not the bundled GUI.** Official profiling does not require Node.js, npm, or the GUI. Follow [`docs/PROFILING_RUNBOOK.md`](docs/PROFILING_RUNBOOK.md) for the Ubuntu CPU runtime and ADTC profiler environment.

From the repository root:

```bash
bash download_model.sh
python3 scripts/verify_model_artifact.py
```

The expected destination is `model/EdgeIMCI-4B-alpha-second-Q4_K_M.gguf`, matching `metadata.json`. Public download must require no credentials. Inference can run offline after the required model/runtime downloads.

`download_model.sh` is the official template: **only `MODEL_FILE` and `MODEL_URL` may change**. Its existing-file skip is not an integrity check. Byte-count and SHA-256 verification belongs in the separate `python3 scripts/verify_model_artifact.py` step, not in modifications to the downloader's logic.

A [preliminary 4B-alpha-second CPU microbenchmark](provenance/4B-alpha-second/profiling/2026-09-22-cpu/README.md) on 2026-09-22 reported **12.15 tokens/s prompt processing (128 tokens)**, **5.42 tokens/s generation (32 tokens)** and **4.063 GiB peak process RSS** on an Intel Core i5-4210U with two threads. This is one repetition, transcribed from operator-supplied console output; original flash-drive evidence import and a complete scoreable ADTC profile remain **pending**. No thermal, ARC-Easy, ADTC score or official 8 GB qualification is claimed. [`REPORT.md`](REPORT.md) separates this preliminary result from historical 0.6B measurements.

## Legacy Experimental GUI

The application backend, model checksum, and frozen extraction prompt remain pinned to the **old 0.6B integration**. They have not been migrated or qualified for 4B-alpha-second.

- `setup.sh` and `run.sh` are legacy GUI entry points, **not a working 4B demo**. Updating the submission downloader does not update that backend.
- `scripts/verify_llama_cpp_integration.sh` and [`docs/LLAMA_CPP_INTEGRATION.md`](docs/LLAMA_CPP_INTEGRATION.md) are **legacy-only and not compatible with 4B**; they do not verify the new artifact.
- The retained `app/`, `web/`, and application tests are not evidence of 4B GUI integration. Do not bypass their old checksum guards to load the new model.

## Provenance and Evidence

The new packet is [`provenance/4B-alpha-second/`](provenance/4B-alpha-second/README.md). It retains original configuration, loss logs, source receipt and hashes, conversion commands, and public-prompt smoke outputs. LoRA used 2 epochs, learning rate `0.0003`, seed `20260824`, rank 16, alpha 32, and dropout **0.05**.

The terminal fine-tuned checkpoint scored 139/139 JSON valid, 135/139 strict-schema valid, 131/139 exact, and 132/139 routing correct on VALIDATION. Failures include 2/119 false rejects, 1/20 unsafe engine admissions, and 2/4 urgent misses. These are not full Q4 validation results. The F16 and Q4 GGUFs each passed 2/2 public prompts for exact JSON targets and deterministic state, under the recorded extraction-v2 wrapper.

`metadata.json` contains unwrapped inputs; the 2/2 JSON smoke result applies only to the recorded extraction-v2 wrapped protocol, not judge free-form inference.

A public reconstruction from the selected training release's sources is available at [Nini0la/edgeimci-beta0-1k-multitask-enriched-2258-v1](https://huggingface.co/datasets/Nini0la/edgeimci-beta0-1k-multitask-enriched-2258-v1/tree/da8daa8efbd583d92000920366085f6dd00c3fb2), pinned to revision `da8daa8efbd583d92000920366085f6dd00c3fb2`. It provides 2,258 TRAIN and 139 VALIDATION rows as JSONL and Parquet; TRAIN is not byte-identical to the original training file, while VALIDATION JSONL is byte-identical. Anonymous Hugging Face `datasets` loading was verified. The card marks the release `license: other`, clinical review pending, and not authorized for clinical use.

The original adapter is publicly downloadable with `python3 provenance/4B-alpha-second/download_adapter.py`; it is checksum-verified into an ignored local directory, not vendored as a large Git blob. A [three-prompt base-versus-fine-tuned demonstration](provenance/4B-alpha-second/before_after.md) now retains actual paired outputs; it is not a held-out benchmark. Confirm organizer acceptance of the hosted adapter arrangement. Consolidated dataset/source-license review, broader matched validation, complete ADTC profiling, and independent clinical review remain separate outstanding work. See [`provenance/README.md`](provenance/README.md), [`REPORT.md`](REPORT.md), and [`MODEL_CARD.md`](MODEL_CARD.md) for evidence boundaries.

## Safety and License

This is a provisional research/competition artifact, not a diagnostic system or production medical device. Independent clinical review remains pending; autonomous or production clinical use is not authorized. The old model's six clinical-threshold failures must not be attributed to this different fine-tune.

The submission repository is [GNU GPL v3](LICENSE). The base model [Qwen/Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B/tree/1cfa9a7208912126459214e8b04321603b3df60c) is Apache-2.0; this is not a blanket license determination for the training dataset. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and [`licenses/Apache-2.0.txt`](licenses/Apache-2.0.txt).
