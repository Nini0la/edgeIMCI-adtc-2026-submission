# EdgeIMCI Verified Baseline

This submission subset began as an explicit source allowlist extracted from
EdgeIMCI commit `c62b3f436148b4a7f5f6a070a2c3af28aeb07cf9`. The local adapter was
promoted from the immutable V2 archive with SHA-256
`6f1c4019fa43ed4c8d9fd8e4c1e551ff5716ae096d4b86aac2495010db104fde`.
The adapter itself has SHA-256
`15c799722d4f7fe0e7d8ae41ceae0755dacf096d9bf804dde04daf5dbb846d08`.

## Acceptance Scope

The baseline ASUS run proved the existing product in `stub` mode:

- React/Vite worker interface
- Python HTTP API
- extraction/review/evaluation workflow
- five existing approved fixture demonstrations
- schema validation
- deterministic completeness, classification, management, and rendering

The promoted subset adds local GGUF extraction as an explicit mode. See
`LLAMA_CPP_INTEGRATION.md` for its scope and acceptance command.

## Excluded Material

- credentials and environment files
- private TEST records
- generated, golden, canary, and training corpora
- experiment and review outputs
- checkpoints, model weights, and GGUF files
- training and Modal deployment machinery
- source PDFs and unrelated research tooling

## Baseline Verification

Requirements are Python 3.10 or newer and Node.js `^20.19.0` or `>=22.12.0`.
From this directory run:

```bash
bash scripts/verify_llama_cpp_integration.sh
```

The integration script reruns all retained backend and frontend checks and then
exercises the real Q8_0 model.

The exact-model phase ends with a JSON receipt whose `status` is `PASS`.
