# EdgeIMCI ADTC 2026 Submission

EdgeIMCI is an offline research model for primary-healthcare sick-child encounters. Its structured-extraction mode converts worker findings into bounded JSON for validation and downstream deterministic IMCI logic. This is team `edge-imci`'s Laptop LLM submission package in `healthcare_medical`.

## Selected Artifact

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

Actual target-laptop 4B profiling is **pending**. No 4B speed, memory, thermal, ARC-Easy, or ADTC score is claimed here. [`REPORT.md`](REPORT.md) retains the older 0.6B figures explicitly as historical measurements of a different artifact.

## Legacy GUI Boundary

The application backend, model checksum, and frozen extraction prompt remain pinned to the **old 0.6B integration**. They have not been migrated or qualified for 4B-alpha-second.

- `setup.sh` and `run.sh` are legacy GUI entry points, **not a working 4B demo**. Updating the submission downloader does not update that backend.
- `scripts/verify_llama_cpp_integration.sh` and [`docs/LLAMA_CPP_INTEGRATION.md`](docs/LLAMA_CPP_INTEGRATION.md) are **legacy-only and not compatible with 4B**; they do not verify the new artifact.
- The retained `app/`, `web/`, and application tests are not evidence of 4B GUI integration. Do not bypass their old checksum guards to load the new model.

## Provenance and Evidence

The new packet is [`provenance/4B-alpha-second/`](provenance/4B-alpha-second/README.md). It retains original configuration, loss logs, source receipt and hashes, conversion commands, and public-prompt smoke outputs. LoRA used 2 epochs, learning rate `0.0003`, seed `20260824`, rank 16, alpha 32, and dropout **0.05**.

The terminal fine-tuned checkpoint scored 139/139 JSON valid, 135/139 strict-schema valid, 131/139 exact, and 132/139 routing correct on VALIDATION. Failures include 2/119 false rejects, 1/20 unsafe engine admissions, and 2/4 urgent misses. These are not full Q4 validation results. The F16 and Q4 GGUFs each passed 2/2 public prompts for exact JSON targets and deterministic state, under the recorded extraction-v2 wrapper.

The selected training release is public at [Nini0la/edgeimci-beta0-1k-multitask-enriched-2258-v1](https://huggingface.co/datasets/Nini0la/edgeimci-beta0-1k-multitask-enriched-2258-v1/tree/da8daa8efbd583d92000920366085f6dd00c3fb2), pinned to revision `da8daa8efbd583d92000920366085f6dd00c3fb2`. It exposes the preserved 2,258-row TRAIN and 139-row VALIDATION partitions as JSONL and Parquet. Anonymous Hugging Face `datasets` loading was verified. The card marks the release `license: other`, clinical review pending, and not authorized for clinical use.

The original adapter is publicly downloadable with `python3 provenance/4B-alpha-second/download_adapter.py`; it is checksum-verified into an ignored local directory, not vendored as a large Git blob. **Gate 2 remains incomplete:** consolidated dataset/source-license review, matched pinned-base-versus-fine-tuned evaluation, and independent clinical review are missing. Confirm organizer acceptance of the hosted adapter arrangement. See [`provenance/README.md`](provenance/README.md), [`REPORT.md`](REPORT.md), and [`MODEL_CARD.md`](MODEL_CARD.md) for evidence boundaries and remaining work.

## Safety and License

This is a provisional research/competition artifact, not a diagnostic system or production medical device. Independent clinical review remains pending; autonomous or production clinical use is not authorized. The old model's six clinical-threshold failures must not be attributed to this different fine-tune.

The submission repository is [GNU GPL v3](LICENSE). The base model [Qwen/Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B/tree/1cfa9a7208912126459214e8b04321603b3df60c) is Apache-2.0; this is not a blanket license determination for the training dataset. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and [`licenses/Apache-2.0.txt`](licenses/Apache-2.0.txt).
