# Legacy EdgeIMCI 0.6B GUI

**Legacy 0.6B GUI only, not a working 4B-alpha-second demo.** `setup.sh` now
downloads the selected 4B artifact, but the backend remains checksum/prompt-pinned
to 0.6B; `setup.sh` / `run.sh` do not provide 4B integration. See the
[standalone profiling runbook](../docs/PROFILING_RUNBOOK.md) for the selected model.

This application connects the local Q8_0 model to the deterministic clinical
engine and React worker interface. The learned component performs structured
extraction only; schema validation, completeness checks, classification,
management, and rendering remain deterministic.

The historical real-model interface requires the old 0.6B artifact and its
qualified runtime. The current submission downloader does not supply that model;
do not use `setup.sh` / `run.sh` as instructions for a 4B demo.

The worker enters free-form findings in the browser. The backend inserts the
frozen system instruction and does not expose it as part of the user prompt.

For model-free interface development:

```bash
EDGEIMCI_SKIP_MODEL_DOWNLOAD=1 bash setup.sh
EDGEIMCI_EXTRACTOR=stub bash run.sh
```

Stub mode displays deterministic fixture examples; it does not invoke any
trained model and is not evidence of 4B-alpha-second behavior.

The retained Modal adapter is a historical development seam and is not the
submitted runtime. The legacy local GUI backend is `llama-cpp`.
