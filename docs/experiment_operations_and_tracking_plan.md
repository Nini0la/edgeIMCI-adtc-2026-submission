# EdgeIMCI Experiment Operations & Tracking Plan

> **Authority:** `WORKING_PLAN` · **Lifecycle:** `CURRENT` · Maintained Markdown working version; the corresponding DOCX is its source snapshot.

*A lightweight operating system for reproducible, environment-aware experimental evidence*

**Status:** Working plan based on current campaign decisions; scope excludes the domain-expert clinical questionnaire.

> **Operating principle:** Running an experiment should automatically create its evidence. Capture raw usage and provenance at source; derive cost and comparative summaries later.

## 1. Scope and experiment taxonomy

The registry treats training, evaluation, generation and deployment work as experiments when each has a fixed configuration, inputs, outputs, metrics and reproducibility requirements.

- `TRAINING` - supervised fine-tuning and capacity/model-size comparisons.
- `CLINICAL_EVAL` - holistic classification, integrated management, completeness/withholding and urgent-incomplete evaluation.
- `SYNTHETIC_GENERATION` - teacher, prompt, variant and corpus-scale experiments.
- `EDGE_PROFILE` - latency, throughput, memory and deployability on target or proxy hardware.
- `COMPRESSION` - SVD or other checkpoint reduction methods, when justified.
- `ALIGNMENT` - preference or reinforcement-learning experiments, only if SFT error analysis supports them.
- `EXTERNAL_EVAL` - optional research evidence outside the hackathon critical path.

## 2. Execution environments

| Environment | Primary job | Model/provider | Telemetry that matters | Cost basis |
| --- | --- | --- | --- | --- |
| Local deterministic/dev | Rules, schemas, oracle/corpus work, smoke tests, small evals | No runtime model or local checkpoint | Versions, counts, validity, wall time, status | Effectively $0 incremental; record time only when useful |
| ASUS / target local | Deployment reality and repeated edge profiles | Exact deployable checkpoint / GGUF | tok/s, first-token and total latency, peak RAM, model size, hardware/software profile | Compute cost secondary; preserve performance evidence |
| Modal | Primary GPU lab for SFT, checkpoint evals and selected self-hosted experiments | Qwen checkpoint; GPU/provider recorded | GPU type/time, wall time, config, checkpoint, metrics, artifacts | Billable runtime x versioned machine rate |
| External API | Teacher bake-offs and synthetic language generation | Teacher provider, model and snapshot | Tokens, requests, retries, latency, accept/reject and error codes | Raw usage x versioned API rate card |
| Hybrid Modal + API | Pipelines combining hosted generation with GPU validation/training | Teacher API + student/evaluator checkpoint | Both API and infrastructure telemetry, linked by run IDs | API usage + Modal runtime; report separately and combined |
| Official ADTC | Final controlled profiling/audit and submission evidence | Submitted artifact | Official profiler outputs plus artifact identity | Externally controlled / N/A unless charges arise |

## 3. Operational matrix

This is the scan-first campaign view. Speed and cost are recorded as observed values after execution; no single telemetry schema is forced onto every environment.

| Experiment | Where | Model/provider | Scientific result | Auto-captured execution data | Cost character |
| --- | --- | --- | --- | --- | --- |
| Deterministic corpus / oracle | Local | None | Artifact validity; coverage | Versions, counts, runtime | $0 incremental |
| Golden rendering bake-off | External API | 2-3 teacher candidates | Semantic acceptance; language quality | Prompt/model/usage/retries/latency | API usage |
| Bulk synthetic generation | API / Azure Batch | Chosen teacher | Acceptance; diversity; downstream utility | Tokens, attempts, errors, throughput | $/attempt and $/accepted example |
| Self-hosted generation alternative | Modal + vLLM | Open teacher | Acceptance; diversity | GPU/runtime/throughput | GPU-hours and $/accepted example |
| Primary SFT | Modal | Qwen3-1.7B | Student clinical performance | GPU, config, data, checkpoint, runtime | $/run; $/1k examples |
| Clinical eval | Local / Modal | Base or trained checkpoint | Clinical metric suite | Checkpoint/eval versions; runtime | $0 local or Modal runtime |
| 4B / capacity branch | Modal | Qwen3-4B | Gain versus 1.7B | Same training/eval provenance | Higher GPU runtime; conditional |
| Qwen3.5 branch | Tinker | Supported Qwen3.5 model | Capacity/post-training result | Provider config, usage, checkpoint | Credits/usage; specialist branch |
| Preference / RL | Modal / specialist | Chosen checkpoint | Targeted error reduction | Reward/config/rollout/compute | Higher; only if justified |
| SVD / compression | Modal / local | Trained checkpoint | Quality-size-speed trade-off | Method/config/artifact/profile | Variable; optional |
| Edge profile | ASUS | Exact deployable artifact | tok/s, RAM, latency, deployability | Full hardware/software profile | Compute cost not decision metric |
| Quantization | Build environment + ASUS | Q8/Q6/Q4 only if triggered | Quality-runtime trade-off | Representation + matched profiles | Conditional optimization |
| Final profile | Official ADTC | Submitted GGUF | Official challenge evidence | Official output + artifact hash | N/A / externally controlled |
| Lundin external eval | Local / Modal | Selected checkpoint | Optional generalization evidence | Benchmark revision/scoring/runtime | Off critical path |

## 4. Scientific versus operational metrics

Scientific metrics answer whether a change improved the model or dataset. Operational metrics answer what it took to produce that evidence. Both belong to a run, but they should remain distinguishable.

| Class | Scientific metrics | Operational/accounting metrics |
| --- | --- | --- |
| Synthetic generation | Acceptance, semantic error codes, diversity, downstream student performance | Attempts, tokens, latency, retries, throughput, raw API usage |
| Training | Loss/learning curves and post-training clinical performance | GPU type/time, wall time, examples, checkpoint size, provider usage |
| Clinical evaluation | Classification, management, completeness/withholding, urgent-incomplete metrics | Checkpoint/eval identity, denominator, runtime, hardware |
| Edge deployment | Quality retained and deployability | tok/s, time-to-first-token, total latency, peak RAM, model size, thermal notes if useful |

## 5. Automatic provenance and run artifacts

> **Minimum rule:** Every runner writes a sidecar record at start and finalizes it on success or failure. Provider adapters add environment-specific telemetry; fields that do not apply remain absent.

| Group | Fields |
| --- | --- |
| Identity | `run_id`, `experiment_id`, `experiment_type`, `parent_run_id`, `status` |
| Model | `model_provider`, `model_id`, `revision/snapshot`, `checkpoint_id`, `checkpoint_hash` |
| Execution | `execution_provider`, `environment`, `hardware`, `started_at`, `finished_at`, `wall_time` |
| Inputs | `dataset_id/version/hash`, split, `prompt_id/version/hash`, `config_id/hash` |
| Code | `git_commit`, `dirty_worktree` flag, runner version, dependency/container identity |
| Usage | examples, requests, tokens, GPU-seconds, retries, raw provider usage |
| Outputs | metrics, error codes, artifact paths/hashes, logs and exception state |
| Accounting | `rate_card_id/date`, derived `actual_cost_usd`, estimation flag |

```text
EXPERIMENT CONFIG
        |
ONE RUNNER ENTRY POINT
        |
WORK + PROVIDER-SPECIFIC TELEMETRY
        |
RUN.JSON + CONFIG + METRICS + ARTIFACT HASHES
        |
REGISTRY / COMPARATIVE REPORTS
```

## 6. Environment-aware cost accounting

- Raw usage is evidence; dollar cost is derived. Preserve token counts, request counts, GPU-seconds and machine type even when a provider does not expose cost directly.
- Use a versioned rate card with currency, effective date, region/deployment and pricing mode. Recalculation must not overwrite the historical rate-card reference.
- For API generation report cost per attempt and cost per accepted example. For Modal report cost per run and, where helpful, per 1,000 training examples. For local and edge work prioritize runtime/performance evidence over nominal electricity cost.
- For hybrid runs retain component costs separately and provide a combined total. Mark forecasts as estimates until reconciled with provider usage or invoices.

## 7. Branch rules

### Quantization

Profile the selected unquantized/baseline deployment artifact first. Enter a Q8/Q6/Q4 comparison only when target-hardware results show meaningful speed, memory or deployability points remain available, and measure the clinical-quality trade-off.

### Lundin

Remove it from required hackathon evidence. Treat it as optional external research evaluation if time permits; do not let it block holistic clinical evaluation, edge profiling or submission.

## 8. Immediate implementation checklist

- Define a small run schema with common identity/provenance fields and typed environment-specific extensions.
- Wrap generation, training, evaluation and profiling entry points so run records are automatic.
- Version prompts, configs, datasets, checkpoints, eval suites and rate cards; store immutable hashes.
- Create a registry view that joins scientific metrics, execution telemetry and derived cost without manual re-entry.
- Run one end-to-end dry run in each active environment before the campaign expands.
