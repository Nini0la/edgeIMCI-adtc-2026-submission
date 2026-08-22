# EdgeIMCI

EdgeIMCI is an experimental effort to test whether small, locally deployable language models can be specialized to reliably follow bounded IMCI clinical decision pathways on constrained hardware.

This repository is research software, not a production medical device or autonomous clinical decision-support application. The frozen v0 development benchmark remains intentionally limited to sick children aged 2–59 months and covers only these selected areas:

- general danger signs;
- cough or difficult breathing;
- diarrhoea dehydration classification.

The repository now also contains a separate, provisional expansion for the five major sick-child assessment areas: general danger signs, cough/difficult breathing, diarrhoea, fever including measles, and ear problem. Its final holistic synthesis is authorized only for a complete supported encounter. This expanded substrate requires domain-expert approval and is not training data or a production clinical system.

The deterministic rule engines—not a language model—construct and verify clinical semantics. Model training remains future work.

## Clinical source

`imci-selected-v0` is an EdgeIMCI machine-readable rule set derived from **WHO — Integrated Management of Childhood Illness, Chart Booklet, March 2014**. It is not a WHO-authored machine-readable rule set. Provenance records both `source_pdf_page` (PDF viewer pages 5–7) and `source_printed_page` (publisher pages 1–3 of 76). The WHO PDF is not redistributed. Obtain it separately and place it at:

```text
data/sources/IMCI chartbooklet 2014.pdf
```

See `data/sources/README.md` and `docs/clinical_questions.md`. Wheeze/bronchodilator reassessment, prolonged cough or recurrent wheeze, HIV-specific chest-indrawing handling, persistent diarrhoea, dysentery, cholera treatment, and oxygen-saturation handling are outside `imci-selected-v0`. The selected respiratory and dehydration classifications must not be described as the complete IMCI respiratory or diarrhoea algorithms.

`imci-major-sick-child-v1` is a separate expansion derived from PDF viewer pages 5–9 and the linked treatment/reassessment pages. It preserves v0 historically and is paired with `imci-major-sick-child-holistic-completeness-v2`. Open clinical and local-adaptation questions are recorded in `docs/clinical_questions.md`; until resolved, the expanded artifacts must be described as proposed and domain-review-gated.

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

## Review the `imci-selected-v0` rule set in YAML

`data/rules/imci_selected_v0.json` remains the canonical machine-readable artifact consumed by the rule loader and reference evaluator. The synchronized `data/rules/imci_selected_v0.yaml` mirror is representation-only and formatted for human review. After changing the JSON, regenerate the YAML with:

```bash
python scripts/sync_rule_yaml.py
```

The test suite fails if the committed YAML does not deserialize to the same rule set or does not match deterministic regeneration.

The expanded canonical/mirror pair is `data/rules/imci_major_sick_child_v1.json` and `.yaml`. Its source map, audit, and domain-review package are separate from the frozen v0 review artifacts.

Regenerate both expanded mirrors with:

```bash
python scripts/sync_holistic_artifacts.py
```

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

- `data/rules/imci_selected_v0.json`: canonical `imci-selected-v0` machine-readable rule set and provenance, derived from the WHO IMCI Chart Booklet.
- `data/rules/imci_selected_v0.yaml`: generated human-readable mirror of the canonical JSON.
- `data/rules/imci_major_sick_child_v1.json` and `.yaml`: proposed five-area major sick-child clinical model and generated review mirror; domain approval required.
- `configs/information_policy/imci_major_sick_child_holistic_completeness_v2.json` and `.yaml`: completeness-gated final-synthesis policy; v1 information-policy artifacts remain historical and unchanged.
- `src/edge_imci/schemas/holistic.py` and `evaluation/holistic.py`: separate whole-encounter schema and deterministic expanded evaluator.
- `docs/major_sick_child_expansion_map_v1.md`: source-derived expansion map and computational interpretations.
- `docs/major_sick_child_domain_review_v1.md`: compact clinical review package.
- `docs/system_level_clinical_audit_v2.md`: expanded system-level verification and readiness decision.
- `docs/product_holistic_golden_suite_requirements_v1.md`: requirements for the next reviewed product-level golden suite; no suite or corpus is generated here.
- `data/generated/split_demo_v1.jsonl` and `split_manifest_v1.json`: deterministic split-machinery demonstration and leakage manifest, not final benchmark data.
- `configs/external_benchmarks.json`: immutable Lundin revision, integrity, license, and paper pins.
- `configs/model_baselines.json`: immutable Qwen/runtime matrix and sampling settings.
- `src/edge_imci/schemas/`: typed case and result representations.
- `src/edge_imci/schemas/trajectory.py`: separate latent-truth, partial-state, model-visible interaction, and structured assistant-target contracts.
- `data/fixtures/trajectories/`: two illustrative schema fixtures; not training, golden-slice, or final benchmark data.
- `docs/trajectory_schema.md`: trajectory-layer boundaries, invariants, and unresolved policy dependencies.
- `configs/information_policy/`: canonical approved v1 information-policy and valid-completion JSON artifacts with generated YAML review mirrors.
- `src/edge_imci/information_policy/`: artifact validation plus deterministic valid-completion information-policy evaluation above the frozen clinical oracle.
- `docs/information_policy_v1.md`: executable policy contract, unresolved-question handling, and golden-slice handoff.
- `docs/interaction_design_retrieval_assessment_bundles.md`: current holistic-assessment product framing; guided questions, bundles, and cards are secondary modes.
- `docs/synthetic_data_generation_experiment_notes.md`: structured-first generation experiments updated for whole encounters, omissions, and urgent incomplete cases.
- `src/edge_imci/generation/golden.py`: deterministic structured-first factory and conservative renderer for the 14-record `GOLDEN_CONVERSION_SLICE`; no paraphrase sampling.
- `src/edge_imci/validation/golden.py`: isolated controlled-language semantic round-trip validator; not a clinical oracle.
- `data/golden/golden_conversion_slice_v1.jsonl` and `.yaml`: tiny equivalent machine-readable validation slices; explicitly not training data, not a benchmark, and not a bulk corpus.
- `docs/golden_slice_review_v1.md`: per-record human/domain-expert review package, deterministic validation results, and flags.
- `docs/rendering_contract_v1.md`: proposed frontline-PHC language contract, acquisition-mode rules, and deterministic rejection gates.
- `data/golden/golden_reference_renderings_v1.jsonl`: 14 proposed natural reference renderings over the unchanged golden semantics; human review required.
- `configs/rendering/rendering_bakeoff_v1.json`: pinned three-teacher/two-prompt local rendering experiment.
- `experiments/rendering_bakeoff_v1/`: 96 fixed-case teacher candidates plus configuration-level semantic and runtime metrics; not a benchmark or corpus.
- `docs/rendering_bakeoff_review_v1.md`: compact side-by-side reference/teacher review surface.
- `src/edge_imci/evaluation/reference.py`: deterministic benchmark oracle.
- `src/edge_imci/evaluation/parsing.py` and `scoring.py`: strict typed internal model-output handling.
- `src/edge_imci/evaluation/external.py`: pinned fetch and separated strict/upstream-compatible external scoring.
- `src/edge_imci/evaluation/reporting.py`: result indexing without cross-benchmark score merging.
- `src/edge_imci/generation/cases.py` and `splits.py`: controlled cases, group-aware splits, and leakage detectors.
- `src/edge_imci/inference/adapters.py` and `mlx_adapter.py`: thin adapter protocol, mock, and real local MLX inference.
- `scripts/`: benchmark, policy-mirror, golden-slice, and baseline entry points.
- `tests/`: clinical boundaries, missing information, provenance, and pipeline behavior.
