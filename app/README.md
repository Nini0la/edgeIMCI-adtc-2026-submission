# EdgeIMCI application

This application connects the local Q8_0 model to the deterministic clinical
engine and React worker interface. The learned component performs structured
extraction only; schema validation, completeness checks, classification,
management, and rendering remain deterministic.

Run the supported source-checkout bundle from the repository root:

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
submitted runtime. The supported submission path is `llama-cpp`.
