# Local Q8_0 Integration

**Legacy 0.6B integration only, not compatible with 4B-alpha-second.** `setup.sh`
now downloads 4B, while the backend and verification script remain pinned to the
old 0.6B model; the commands below are not a working 4B setup/run path. For the
selected model, use the [standalone profiling runbook](PROFILING_RUNBOOK.md).

The historical submission promoted the ASUS-verified V2 `llama-cpp` integration into the
bounded GUI subset. It does not use the later schema-constrained generation
experiment. Model output is parsed strictly and validated after generation.

## Product Changes

- Added `app/extractor/llama_cpp.py`.
- Registered `LlamaCppEncounterExtractor` in `app/extractor/__init__.py`.
- Registered `llama-cpp` in `app/service/service.py`.
- Added `llama-cpp` to the API CLI choices in `app/api.py`.
- Allowed schema-valid `rehydration_stage: "NOT_STARTED"` to enter the existing
  initial-assessment evaluator while retaining rejection of active/reassessment stages.

The legacy 0.6B artifact is pinned to 639,446,752 bytes and SHA-256
`26d11ee99801455fcef011a3e5ff124b2ff1cce943ed06cbe611c8fbcc42aca2`.
The adapter invokes the pinned b9637 `llama-completion` in raw one-shot mode,
with a 2,048-token context, two CPU threads, and serialized requests. The
Ubuntu 22.04 target executable is pinned to SHA-256
`a41d3d5fec1173afc89323a026a8f3612a9de2692a8c825223852627e8277641`
and must report commit `aedb2a5`. Its shallow source checkout reports version
count `1`, so the exact executable digest is the controlling build identity.
The adapter rejects malformed or schema-invalid output, and sends accepted
observations through the existing worker-review and deterministic evaluation
pipeline.

## ASUS Acceptance

Historical acceptance command from the repository root, requiring the old 0.6B
artifact and runtime (the current `setup.sh` does not download that artifact):

```bash
bash scripts/verify_llama_cpp_integration.sh
```

The script defaults to the model under `model/` and `llama-completion` on
`PATH`. Set `EDGEIMCI_MODEL_PATH` or `LLAMA_CPP_BIN` when they are elsewhere.
It reruns backend and frontend tests, builds and serves the GUI, then runs both
submitted prompts through the real Q8_0.

Historical interactive GUI command after 0.6B automated acceptance:

```bash
export LLAMA_CPP_BIN=/path/to/qualified/llama-completion
bash run.sh
```

The original V2 path was accepted on the target ASUS. That acceptance applies only
to the recorded legacy model, runtime, inference parameters, and adapter bytes.
