# EdgeIMCI application

**Legacy 0.6B GUI only, not a working 4B-alpha-second demo.** `setup.sh` now
downloads the selected 4B artifact, but the backend remains checksum/prompt-pinned
to 0.6B; `setup.sh` / `run.sh` do not provide 4B integration. See the
[standalone profiling runbook](../docs/PROFILING_RUNBOOK.md) for the selected model.

This application connects the local Q8_0 model to the deterministic clinical
engine and React worker interface. The learned component performs structured
extraction only; schema validation, completeness checks, classification,
management, and rendering remain deterministic.

Historical 0.6B source-checkout commands (not a current 4B setup/run path):

```bash
bash setup.sh
export LLAMA_CPP_BIN=/path/to/qualified/llama-completion
bash run.sh
```

The worker enters free-form findings in the browser. The backend inserts the
frozen system instruction and does not expose it as part of the user prompt.

For model-free interface development:

```bash
EDGEIMCI_SKIP_MODEL_DOWNLOAD=1 bash setup.sh
EDGEIMCI_EXTRACTOR=stub bash run.sh
```

The retained Modal adapter is a historical development seam and is not the
submitted runtime. The legacy local GUI backend is `llama-cpp`.
