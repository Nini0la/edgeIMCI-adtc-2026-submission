# EdgeIMCI-Qwen3-0.6B-SFT-Q8_0

## Summary

EdgeIMCI-Qwen3-0.6B-SFT-Q8_0 is a fine-tuned `Qwen/Qwen3-0.6B` model used only
to convert free-form primary-healthcare sick-child findings into the bounded
EdgeIMCI encounter JSON schema. Deterministic code performs all downstream
completeness checks, classifications, management selection, and rendering.

## Artifact

- File: `qwen3-0.6b-sft-selected-seed-20260824-q8_0.gguf`
- Quantization: GGUF Q8_0
- Size: 639,446,752 bytes
- SHA-256: `26d11ee99801455fcef011a3e5ff124b2ff1cce943ed06cbe611c8fbcc42aca2`
- Immutable model revision: `6af69949d91fbe2628d88a6ed7df62a944cd71a3`
- Base model: `Qwen/Qwen3-0.6B`
- License: Apache License 2.0

## Intended Use

The model is an offline research and competition artifact for structured
extraction within the included GUI. It is not intended to diagnose, classify,
or recommend treatment without the deterministic EdgeIMCI pipeline and human
review.

## Limitations

The retained project evaluation recorded six preregistered clinical-threshold
failures despite strong JSON and schema validity. The model may omit findings,
misread negation, or produce schema-invalid output. The adapter therefore fails
closed, preserves unknown values, and requires worker review before evaluation.

This artifact is not a medical device and is not authorized for autonomous or
production clinical use. See [`REPORT.md`](REPORT.md) for evaluation details and
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for provenance.
