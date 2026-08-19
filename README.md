# EdgeIMCI

EdgeIMCI is an experimental effort to test whether small, locally deployable language models can be specialized to reliably follow bounded IMCI clinical decision pathways on constrained hardware.

This repository is research software, not a production medical device or autonomous clinical decision-support application. The initial benchmark is intentionally limited to sick children aged 2 months up to 5 years and covers only:

- general danger signs;
- cough or difficult breathing;
- diarrhoea dehydration classification.

The deterministic rule engine—not a language model—constructs and verifies the current benchmark ground truth. Model training is future work.

## Clinical source

Rules are traced to **WHO — Integrated Management of Childhood Illness, Chart Booklet, March 2014**, PDF pages 5–7 (printed chart pages 1–3 of 76). The WHO PDF is not redistributed. Obtain it separately and place it at:

```text
data/sources/IMCI chartbooklet 2014.pdf
```

See `data/sources/README.md` and `docs/clinical_questions.md`. Wheezing cases remain excluded pending a domain-expert decision about representing the chart's required post-bronchodilator reassessment. Persistent diarrhoea, dysentery, oxygen-saturation handling, HIV-specific modifiers, and prolonged-cough referral are outside this first benchmark.

## Install

Python 3.10 or newer is required.

```bash
python -m pip install -e ".[dev]"
```

## Test

```bash
python -m pytest
```

## Generate the development benchmark

Generation is deterministic; the default fixed seed is `20240301`.

```bash
python scripts/generate_benchmark.py \
  --output data/benchmark/imci_v0.jsonl \
  --seed 20240301
```

## Run the mock baseline

The mock adapter exercises serialization, prompting, structured scoring, and run-artifact generation without downloading or invoking a model.

```bash
python scripts/run_baseline.py \
  --benchmark data/benchmark/imci_v0.jsonl \
  --output experiments/baselines/mock-run/
```

The runner writes `run.json` with per-case outputs, competency scores, aggregate scores, latency, failure fields, and nullable token-throughput fields for adapters that do not expose token counts.

## Repository components

- `data/rules/imci_selected_v0.json`: inspectable rules and source provenance.
- `src/edge_imci/schemas/`: typed case and result representations.
- `src/edge_imci/evaluation/reference.py`: deterministic benchmark oracle.
- `src/edge_imci/generation/cases.py`: controlled case generation.
- `src/edge_imci/inference/adapters.py`: thin model adapter protocol and mock.
- `scripts/`: benchmark generation and baseline entry points.
- `tests/`: clinical boundaries, missing information, provenance, and pipeline behavior.
