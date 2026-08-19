# EdgeIMCI

EdgeIMCI is an experimental effort to test whether small, locally deployable language models can be specialized to reliably follow bounded IMCI clinical decision pathways on constrained hardware.

This repository is research software, not a production medical device or autonomous clinical decision-support application. The initial benchmark is intentionally limited to sick children aged 2 months up to 5 years and covers only:

- general danger signs;
- cough or difficult breathing;
- diarrhoea dehydration classification.

The deterministic rule engine—not a language model—constructs and verifies the current benchmark ground truth. Model training is future work.

## Clinical source

Rules are traced to **WHO — Integrated Management of Childhood Illness, Chart Booklet, March 2014**. Provenance records both `source_pdf_page` (PDF viewer pages 5–7) and `source_printed_page` (publisher pages 1–3 of 76). The WHO PDF is not redistributed. Obtain it separately and place it at:

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

## Generate the v0 development/regression benchmark

`data/benchmark/imci_v0.jsonl` is the 82-case `clinical-rules-v0` development regression and diagnostic set. It is deliberately exposed, is not an untouched final benchmark, and must never be used as future training data. Generation is deterministic; the default fixed seed is `20240301`.

```bash
python scripts/generate_benchmark.py \
  --output data/benchmark/imci_v0.jsonl \
  --seed 20240301
```

All 82 labels are recomputed by the deterministic oracle. The latent metadata (`rule_family`, `logic_signature`, `template_family`, `counterfactual_group_id`, and `seed`) supports contamination analysis without adding clinical logic.

## Demonstrate leakage-resistant split generation

The committed `data/generated/split_demo_v1.jsonl` and `split_manifest_v1.json` prove the split machinery; they are explicitly **not** the eventual large post-training or final evaluation corpus. Regenerate them with:

```bash
python scripts/generate_splits.py
```

The versioned manifest separates:

- IID held-out latent case groups;
- template-family holdouts, labelled as wording robustness rather than IID;
- compositional holdouts whose constituent fired rules remain in training;
- whole counterfactual/boundary challenge groups.

Every regime assigns atomic case groups rather than randomly splitting rows. Automated checks reject case-ID overlap, exact normalized structured duplicates, normalized presentation duplicates, shared counterfactual groups, held-out template families in training, held-out logic signatures in training, and held-out challenge groups in training.

The usage boundary is fixed: `training` is for future post-training only; `validation` is for future hyperparameter/checkpoint selection; `benchmark` is evaluation-only and cannot select checkpoints. The exposed 82-case v0 regression set remains separate from all of these roles.

## External Lundin IMCI benchmark

`configs/external_benchmarks.json` pins, but does not redistribute, two upstream artifacts from [jessicalundin/graph_testing_harness](https://github.com/jessicalundin/graph_testing_harness):

- `lundin_current_07c6f0f`: 432 committed questions at `07c6f0fe54a21c9861cee89499ebbf286520ee67`, corresponding to the current arXiv v3-era repository.
- `lundin_arxiv_v1_d153120`: 438 committed questions at `d1531204bb29f4e9305910b395c3c28906dfb698`, the closest identifiable pre-submission revision for arXiv v1. It is not a tagged paper artifact.

Fetch and verify exact byte size, SHA-256, question count, schema, and the upstream MIT license into a local cache:

```bash
python scripts/fetch_external_benchmark.py lundin_current_07c6f0f
python scripts/fetch_external_benchmark.py lundin_arxiv_v1_d153120
```

The paper is CC BY 4.0 and the repository code carries an MIT license. Upstream does not separately establish relicensing terms for WHO-derived text inside the graph/questions, so EdgeIMCI uses fetch-with-attribution and keeps all external assets out of the repository.

External results always name one of two incompatible policies. `edge_imci_strict_external_eval` accepts only an exact uppercase `A`–`D`, counts malformed answers and provider failures as incorrect, and keeps every scheduled question in the denominator. `lundin_upstream_compat_eval` reproduces the repository's permissive first-A/B/C/D-anywhere, fallback-to-A parser and omission of provider failures from its denominator. The latter is labelled compatibility only: the paper's raw responses, model digest/runtime, seed, and table-analysis code are unavailable, so the historical Qwen3-1.7B result of 44.9 ± 9.2% is a cited comparator, not an exactly reproducible result.

## Review the rule set in YAML

`data/rules/imci_selected_v0.json` remains the canonical machine artifact consumed by the rule loader and reference evaluator. The synchronized `data/rules/imci_selected_v0.yaml` mirror is representation-only and formatted for human review. After changing the JSON, regenerate the YAML with:

```bash
python scripts/sync_rule_yaml.py
```

The test suite fails if the committed YAML does not deserialize to the same rule set or does not match deterministic regeneration.

## Run the mock baseline

The mock adapter exercises serialization, prompting, structured scoring, and run-artifact generation without downloading or invoking a model.

```bash
python scripts/run_baseline.py \
  --benchmark data/benchmark/imci_v0.jsonl \
  --output experiments/baselines/mock-run/
```

The runner writes `run.json` with the exact prompt and raw output, typed parsed prediction, expected oracle result, parse status/error, every component score, overall pass/fail, latency, and nullable token-count/throughput fields. Parse and generation failures remain in the aggregate denominator.

## Run pinned untuned local Qwen baselines

Install the Apple Silicon inference extra:

```bash
python -m pip install -e ".[models]"
```

`configs/model_baselines.json` pins official post-trained Qwen3 0.6B and 1.7B revisions plus a pinned `mlx-community` 4-bit, group-size-64 conversion of the official Qwen3 4B checkpoint. It also pins MLX-LM 0.31.3, bfloat16 compute, greedy decoding, disabled thinking, batch size one, maximum lengths, and the fixed generation seed. Each model uses the same internal prompt/config or the same external prompt/config; prompts are not tuned per model.

```bash
python scripts/run_model_baseline.py qwen3-0.6b \
  --output experiments/baselines/qwen3-0.6b/internal-v0

python scripts/run_external_model_baseline.py \
  qwen3-0.6b lundin_current_07c6f0f \
  --output experiments/baselines/qwen3-0.6b/external-lundin-current-strict
```

Runs are local MLX inference only. No checkpoint is selected from evaluation results, no model weights are modified, and no SFT, LoRA/QLoRA, RL, or other training occurs. Each artifact records exact model/tokenizer revisions, decoding configuration, CPU/GPU model, RAM, operating system, runtime versions, batch size, per-case latency, and available token metrics.

## Repository components

- `data/rules/imci_selected_v0.json`: canonical machine-readable rules and provenance.
- `data/rules/imci_selected_v0.yaml`: generated human-readable mirror of the canonical JSON.
- `data/generated/split_demo_v1.jsonl` and `split_manifest_v1.json`: deterministic split-machinery demonstration and leakage manifest, not final benchmark data.
- `configs/external_benchmarks.json`: immutable Lundin revision, integrity, license, and paper pins.
- `configs/model_baselines.json`: immutable Qwen/runtime matrix and sampling settings.
- `src/edge_imci/schemas/`: typed case and result representations.
- `src/edge_imci/evaluation/reference.py`: deterministic benchmark oracle.
- `src/edge_imci/evaluation/parsing.py` and `scoring.py`: strict typed internal model-output handling.
- `src/edge_imci/evaluation/external.py`: pinned fetch and separated strict/upstream-compatible external scoring.
- `src/edge_imci/evaluation/reporting.py`: result indexing without cross-benchmark score merging.
- `src/edge_imci/generation/cases.py` and `splits.py`: controlled cases, group-aware splits, and leakage detectors.
- `src/edge_imci/inference/adapters.py` and `mlx_adapter.py`: thin adapter protocol, mock, and real local MLX inference.
- `scripts/`: benchmark generation and baseline entry points.
- `tests/`: clinical boundaries, missing information, provenance, and pipeline behavior.
