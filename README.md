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
- [`model/`](model/): local model destination; weights are excluded from Git.

## Safety and Scope

EdgeIMCI is a provisional research and competition artifact. It is not a diagnostic system, a production medical device, or authorized for autonomous clinical use. The retained project evaluation recorded six preregistered clinical-threshold failures despite strong JSON and schema validity. Human oversight and further clinical qualification remain necessary.

## License

The submission repository is provided under the [GNU GPL v3](LICENSE). The Qwen3 base model and published fine-tuned model artifact use the Apache-2.0 license.
