# EdgeIMCI ADTC 2026 Submission

EdgeIMCI is an offline structured-extraction model for primary-healthcare sick-child encounters. It converts free-form PHC worker findings into a bounded JSON encounter record for schema validation and downstream deterministic IMCI logic.

This repository is the ADTC 2026 Laptop LLM submission package for team `edgeimci` in the `healthcare_medical` domain.

## Submission Artifact

| Field | Value |
| --- | --- |
| Model | EdgeIMCI-Qwen3-0.6B-SFT-Q8_0 |
| Base model | `Qwen/Qwen3-0.6B` |
| Runtime | `llama.cpp` |
| Quantization | GGUF Q8_0 |
| Parameters | 596,049,920 |
| File | `qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf` |
| Size | 639,446,752 bytes |
| SHA-256 | `26d11ee99801455fcef011a3e5ff124b2ff1cce943ed06cbe611c8fbcc42aca2` |
| Hosting | [Hugging Face](https://huggingface.co/Nini0la/edgeimci-qwen3-0.6b-sft-gguf) |

The download script pins immutable Hugging Face model commit `6af69949d91fbe2628d88a6ed7df62a944cd71a3` and verifies the SHA-256 before installing the model.
See [`MODEL_CARD.md`](MODEL_CARD.md) for intended use, provenance, and limitations.

## Download

No credentials are required:

```bash
bash download_model.sh
```

The script is idempotent and writes the verified model to the path declared in `metadata.json`:

```text
model/qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf
```

After download, inference runs locally without network access.

## Run The GUI

Requirements:

- Python 3.10 or newer
- Node.js and npm
- The exact qualified `llama-completion` build described below

Install dependencies, build the frontend, and download the verified model:

```bash
bash setup.sh
```

This is a source-checkout application bundle, not a standalone Python wheel.
Run `setup.sh` and `run.sh` from the repository root so the versioned schemas
and frontend assets remain bound to the application.

Point the application at the qualified runtime and start the local GUI:

```bash
export LLAMA_CPP_BIN=/path/to/llama-completion
bash run.sh
```

Open <http://127.0.0.1:8000>. The worker enters findings only; the application
adds the frozen extraction instruction internally, validates the model JSON,
allows review, and runs deterministic IMCI logic.

The adapter fails closed unless the runtime is the qualified `llama.cpp` b9637
executable at commit `aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3` with SHA-256
`a41d3d5fec1173afc89323a026a8f3612a9de2692a8c825223852627e8277641`.

To exercise the interface without loading the model:

```bash
EDGEIMCI_SKIP_MODEL_DOWNLOAD=1 bash setup.sh
EDGEIMCI_EXTRACTOR=stub bash run.sh
```

## Verification

Run the complete local and exact-model verification after the model and
qualified runtime are available:

```bash
export LLAMA_CPP_BIN=/path/to/llama-completion
bash scripts/verify_llama_cpp_integration.sh
```

## Profile

The selected GGUF was measured on an ASUS laptop running Ubuntu 22.04.5 with an Intel Core i5-4210U and CPU-only `llama.cpp` inference.

| Metric | Result |
| --- | ---: |
| ADTC quick-profile generation | 18.94 tokens/s |
| First-token latency | 8,851.28 ms |
| Peak RSS | 774.59 MB |
| Steady-state RSS | 729.21 MB |
| Peak CPU temperature | 75.0 C |
| Thermal throttling | No |
| Self-reported performance score | 100.00 |
| Self-reported efficiency score | 89.19 |
| ARC-Easy accuracy smoke | 0.64 `acc_norm`, 50 samples |

The ADTC quick participant profile used `--skip-accuracy`; the accuracy smoke was run separately with the same pinned profiler and exact GGUF bytes. These are participant measurements, not organizer audit results. See [`REPORT.md`](REPORT.md) for conversion comparisons, provenance, constraints, and limitations.

## Repository Files

- [`metadata.json`](metadata.json): team, domain, prompts, and runtime metadata.
- [`download_model.sh`](download_model.sh): anonymous, revision-pinned, checksum-verifying model download.
- [`REPORT.md`](REPORT.md): technical report and ASUS benchmark evidence.
- [`MODEL_CARD.md`](MODEL_CARD.md): model provenance, intended use, and limitations.
- [`model/`](model/): local model destination; weights are excluded from Git.
- [`app/`](app/): local API, extraction adapters, and deterministic service flow.
- [`src/edge_imci/`](src/edge_imci/): bounded schemas and deterministic IMCI logic.
- [`web/`](web/): worker-facing React interface.
- [`acceptance/public_prompts.json`](acceptance/public_prompts.json): expected structured outputs for the two submitted prompts.
- [`docs/LLAMA_CPP_INTEGRATION.md`](docs/LLAMA_CPP_INTEGRATION.md): qualified runtime details and limitations.

## Safety and Scope

EdgeIMCI is a provisional research and competition artifact. It is not a diagnostic system, a production medical device, or authorized for autonomous clinical use. The retained project evaluation recorded six preregistered clinical-threshold failures despite strong JSON and schema validity. Human oversight and further clinical qualification remain necessary.

## License

The submission repository is provided under the [GNU GPL v3](LICENSE). The
promoted EdgeIMCI application subset and model have Apache-2.0 provenance; see
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and
[`licenses/Apache-2.0.txt`](licenses/Apache-2.0.txt).
