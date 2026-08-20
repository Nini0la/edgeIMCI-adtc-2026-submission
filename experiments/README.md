# Experiment and edge-profiling guidance

This directory is the home for EdgeIMCI model experiments and their evidence. Before the project begins running many SFT, RL, quantization, and edge-deployment variants, it should add two first-class pieces of infrastructure:

1. an **experiment registry** that records every model/training configuration and links it to its evaluation results; and
2. a **profiling registry** that stores the ASUS/ADTC edge evidence separately from model-quality results.

The purpose is to make the state of the experimental program explicit and machine-readable. An experiment should be discoverable from committed artifacts rather than reconstructed from conversation, filenames, or memory.

## Planned layout

The existing experiment-category directories remain useful for their run artifacts:

```text
experiments/
├── README.md
├── registry/
│   ├── experiment_matrix.json      # canonical machine-readable registry
│   └── experiment_matrix.yaml      # generated human-readable mirror
├── profiling/
│   └── adtc/
│       ├── runs/                   # immutable official reports plus sidecars
│       ├── summaries/              # computed aggregates by edge profile
│       └── comparisons/            # participant-versus-audit verdicts
├── baselines/                           # untuned model run artifacts
├── sft/                                 # supervised fine-tuning artifacts
└── rl/                                  # later reward/RL artifacts
```

The registry is an index, not a replacement for the detailed artifacts in these directories.

## 1. Experiment registry

`experiments/registry/experiment_matrix.json` should be the canonical experiment matrix. Its YAML counterpart should be generated from the JSON and should deserialize to the same data. Do not edit the JSON and YAML independently.

Each experiment is one row/object. At minimum, it identifies the model configuration, training stage, deployed precision, evaluation artifacts, and edge profile:

```json
{
  "experiment_id": "qwen3-1.7b-base-q8",
  "base_model": "Qwen3-1.7B",
  "training": "base",
  "precision": "Q8",
  "internal_eval": null,
  "multiturn_eval": null,
  "lundin_eval": null,
  "edge_profile": "asus-qwen3-1.7b-q8-v1"
}
```

A later trained variant follows the same shape:

```json
{
  "experiment_id": "qwen3-1.7b-sft-v2-q8",
  "base_model": "Qwen3-1.7B",
  "training": "sft-v2",
  "precision": "Q8",
  "internal_eval": "experiments/sft/qwen3-1.7b-sft-v2/internal-v1/run.json",
  "multiturn_eval": "experiments/sft/qwen3-1.7b-sft-v2/multiturn-v1/run.json",
  "lundin_eval": "experiments/sft/qwen3-1.7b-sft-v2/lundin-current-strict/run.json",
  "edge_profile": "asus-qwen3-1.7b-sft-v2-q8-v1"
}
```

The evaluation fields should contain repository-relative paths or stable artifact IDs, according to the convention selected when the registry is implemented. Use one convention consistently throughout the matrix. A `null` value means that the evaluation or profile has not been run yet; it must not mean that a run failed or that its result is unknown.

### Field meanings

| Field | Meaning |
| --- | --- |
| `experiment_id` | Unique, stable identifier for this exact model/training/precision combination. |
| `base_model` | Human-readable base model family and size. The exact checkpoint revision remains in the detailed run artifact. |
| `training` | Training state, such as `base`, `sft-v1`, `sft-v2`, or a later RL variant. |
| `precision` | The representation used for this experiment, such as `BF16`, `FP16`, `Q8`, `Q6`, or `Q4_K_M`. |
| `internal_eval` | Reference to the strict internal diagnostic evaluation artifact. |
| `multiturn_eval` | Reference to the natural-language, information-gathering evaluation artifact. |
| `lundin_eval` | Reference to the pinned external Lundin evaluation artifact, including its named scoring policy. |
| `edge_profile` | Reference to an ASUS/ADTC profile summary; never an inline block of hardware metrics. |

Add fields when needed to identify an experiment unambiguously, but keep detailed per-case results, prompts, runtime metadata, and hardware measurements in their own artifacts. The matrix should remain compact enough to scan and automate against.

### Registry rules

- Create the matrix row when an experiment is planned, not only after every run is complete.
- Use a stable, unique `experiment_id`; do not reuse an ID for a materially different checkpoint, dataset mixture, training recipe, or precision.
- Fill evaluation references only after the referenced artifacts exist and have passed their relevant checks.
- Keep unavailable evaluations as `null`. Never use placeholder paths or fabricated scores.
- Keep internal, multi-turn, and Lundin results separate. Do not collapse incompatible benchmarks into one score.
- Treat JSON as canonical. Regenerate YAML after every JSON change and verify semantic equality.
- Prefer append-only history. If an experiment is superseded, record that state explicitly rather than silently turning its row into another experiment.

## 2. ASUS/ADTC profiling registry

Hardware performance is a different dimension from clinical/model quality. Do not put token rates, RAM, first-token latency, or other profiler measurements directly in the experiment matrix. The matrix should point to a structured edge-profile summary instead.

The [ADTC 2026 challenge page](https://adtc-2026.devpost.com/) defines the target as an x86-64 laptop with an Intel Core i5 10th–12th generation or AMD Ryzen 5 3000–5000 CPU, 8 GB DDR4 RAM, integrated graphics only, a 256 GB SSD, and Ubuntu 22.04 LTS. The ASUS development machine is a **participant-laptop proxy** unless its recorded specifications match that profile; an ASUS result is not itself an official audit result.

The [official ADTC profiler repository](https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler) is the source of truth for the profiling contract. It profiles local GGUF models through `llama.cpp`, requires `llama-bench` on `PATH`, and emits schema-validated JSON. Pin the profiler version and source commit used for every EdgeIMCI run because the tool and schema may change during the competition.

Conceptually:

```text
EXPERIMENT MATRIX
       |
       |-- model and training configuration
       |-- internal evaluation result
       |-- Lundin external evaluation result
       |-- multi-turn evaluation result
       `-- edge_profile ----------------------.
                                                |
                                                v
                                      ASUS / ADTC PROFILE
                                      - generation tok/s
                                      - first-token latency
                                      - peak and steady RSS
                                      - CPU utilization and thermals
                                      - environment and model metadata
                                      - accuracy entries
                                      - reproducibility metadata
```

The initial configurations worth profiling are:

```text
asus-qwen3-0.6b-fp16
asus-qwen3-0.6b-q8
asus-qwen3-1.7b-q8
asus-qwen3-1.7b-q6
asus-qwen3-4b-q4_k_m
```

These names describe configurations, not results. A trained checkpoint should include its training identifier so that it cannot be confused with the untuned base model, for example `asus-qwen3-1.7b-sft-v2-q8-v1`.

### Official report contract

The profiler's bundled [JSON Schema](https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler/blob/main/src/adtc_profiler/schema/adtc-profiler.schema.json) is strict: its objects use `additionalProperties: false`. Preserve the generated `submission.json` unchanged. Do **not** insert EdgeIMCI-only fields such as `profile_id`, `experiment_id`, `run_id`, timestamp, notes, or custom averages into that file.

The official report contains these top-level blocks:

| Official block | Relevant contents |
| --- | --- |
| `schema_version`, `profiler_version` | Versions of the report contract and profiler. |
| `submission` | Team, domain, language, test prompts, model runtime, quantization, parameter estimate, and packaging claims. EdgeIMCI's domain is `healthcare_medical`. |
| `environment` | `measured_on`, CPU model, installed RAM, GPU description, and operating system. `measured_on` is either `participant_laptop` or `audit_cloud_vm`. |
| `throughput` | Required generation tokens/second and first-token latency, plus prompt-token and generated-token counts. |
| `memory` | Required peak and steady-state resident memory in MB, with optional peak virtual memory. |
| `accuracy` | Zero or more benchmark records containing benchmark, dataset version, language, sample count, score, and optional metric. |
| `cpu_thermal` | Required p99 CPU utilization and throttling flag, plus nullable peak core temperature. |
| `reproducibility` | Git commit SHA, Docker image digest, and random seed. |
| `model_info` | GGUF-derived parameter count, context length, architecture, claimed parameter estimate, and parameter-match check. |

Use the official JSON paths in summaries, including:

```text
throughput.tokens_per_second_generation
throughput.first_token_latency_ms
memory.peak_rss_mb
memory.steady_state_rss_mb
memory.peak_vms_mb
cpu_thermal.cpu_percent_p99
cpu_thermal.core_temp_c_peak
cpu_thermal.throttled
model_info.context_length
```

The current profiler does **not** emit a prompt-tokens-per-second field or a distinct model-memory field. Do not invent either as an ADTC measurement. The profiler currently runs CPU-only `llama-bench` with a 512-token prompt and 128 generated tokens by default. Its `first_token_latency_ms` is an estimate derived from the prompt-processing rate for the whole prompt, rather than an independently timed application request. Preserve that distinction in reports and presentations.

### Submission input and profiler commands

The profiler expects a submission directory containing `metadata.json` and the GGUF model referenced by `_runtime.model_path`. All public metadata fields are required, extra public fields are rejected, and `test_prompts` must contain exactly two prompts. Use the profiler's `examples/demo-submission/` directory and canonical schema when building EdgeIMCI's submission package.

Install a pinned revision rather than silently following a moving `main` branch. The operational prerequisites are Python and `llama-bench` from `llama.cpp` on `PATH`.

Run the local participant profile with:

```bash
adtc-profiler run \
  --submission /path/to/edgeimci-submission \
  --mode participant \
  --output submission.json
```

`--skip-accuracy` is appropriate only for quick iteration. A final candidate report must come from a complete run because accuracy contributes 50% of the published score. The current CLI defaults to seed 42, `arc_easy`, and an accuracy limit of 50 for participant-side runs; record any overrides. The real audit uses hidden validation data.

Audit mode belongs to the evaluation environment. When an official audit report becomes available, compare it with the participant report and retain the verdict:

```bash
adtc-profiler compare submission.json audit.json --output verdict.json
```

The current comparison contract flags deviations beyond ±15% for peak/steady RSS and ±25% for generation throughput/first-token latency; deviations above 50%, zero or missing values, mismatched team IDs, incorrect environments, or schema violations fail comparison.

### Individual profile runs

Store every generated report as an immutable artifact together with an EdgeIMCI sidecar:

```text
experiments/profiling/adtc/runs/
└── asus-qwen3-1.7b-q8-v1-20260820T120000Z-01/
    ├── submission.json       # untouched, schema-valid profiler output
    └── edgeimci_run.json     # EdgeIMCI identity and provenance
```

The sidecar owns the fields that do not belong in the official schema:

```json
{
  "schema_version": "1.0.0",
  "profile_id": "asus-qwen3-1.7b-q8-v1",
  "run_id": "asus-qwen3-1.7b-q8-v1-20260820T120000Z-01",
  "experiment_id": "qwen3-1.7b-base-q8",
  "report_path": "experiments/profiling/adtc/runs/asus-qwen3-1.7b-q8-v1-20260820T120000Z-01/submission.json",
  "report_sha256": "...",
  "model_artifact_sha256": "...",
  "run_timestamp": "2026-08-20T12:00:00Z",
  "profiler_source_revision": "...",
  "command": [
    "adtc-profiler",
    "run",
    "--submission",
    "/path/to/edgeimci-submission",
    "--mode",
    "participant",
    "--output",
    "submission.json"
  ],
  "accuracy_skipped": false,
  "notes": ""
}
```

The ellipses above are documentation placeholders, not valid completed evidence. Populate digests and the pinned profiler source revision before registering the run. The official report contains submitter contact details, so use only contact information approved for publication before committing it to this repository.

### Immutability and summaries

Never overwrite an individual run because a later run looks cleaner. Each invocation gets a new `run_id` and directory. Failed or anomalous runs should remain available with their status and notes when they are useful evidence. A failed invocation that produces no schema-valid `submission.json` must be recorded as failed in an EdgeIMCI sidecar; never manufacture an official report to fill the gap.

A separate summary artifact should reference the included run IDs and compute aggregates such as:

- run count;
- arithmetic mean and median for generation tokens/second, first-token latency, peak RSS, and steady-state RSS;
- minimum and maximum, or another stated dispersion measure; and
- the aggregation timestamp and method/version.

Only aggregate comparable runs: same exact GGUF digest, profiler/schema revision, participant machine and OS state, runtime settings, accuracy configuration, and workload. Do not average participant and audit measurements together. The experiment matrix's `edge_profile` should normally refer to this stable summary/profile ID, not to whichever raw run happened most recently. Summaries may be regenerated when new immutable runs are deliberately admitted, but their input run IDs, official report digests, exclusions, and aggregation method must remain explicit. This prevents one unusual run from silently replacing the underlying evidence.

### ADTC scoring context

The published leaderboard formula weights accuracy at 50%, generation-throughput performance at 30%, and memory efficiency at 20%, then applies a 10-point thermal penalty when throttling occurs or temperature exceeds 85°C. The current published reference throughput is 15 generation tokens/second, and memory efficiency is measured against a 7 GB budget. An out-of-memory or sandbox crash disqualifies the submission. These competition constants are externally controlled and may change; record the rules date/version used for any derived score rather than baking the constants into raw evidence.

## 3. Workflow for each experiment

Agents and contributors should use the following sequence:

1. **Register the configuration.** Add a unique row to the canonical JSON matrix with unavailable results set to `null`.
2. **Produce detailed run artifacts.** Run the relevant baseline, training, internal, multi-turn, and external evaluation workflows in the appropriate experiment directory.
3. **Link results, do not copy them.** Update the matrix with stable references to the completed artifacts; do not paste scores or hardware metrics into the row.
4. **Profile the deployable representation.** Run the exact GGUF checkpoint and quantization intended for ASUS deployment with a pinned official profiler revision.
5. **Preserve every raw profiling run.** Keep the untouched official report and its EdgeIMCI sidecar in a new immutable run directory.
6. **Compute the profile summary.** Aggregate an explicit set of comparable runs and update the matrix's `edge_profile` reference.
7. **Regenerate the YAML mirror.** Produce it deterministically from the canonical JSON and verify that the two deserialize to identical content.
8. **Validate references.** Check that every non-null evaluation/profile reference resolves, every ID is unique, and every summary names existing immutable runs.

## 4. Separation of concerns

Keep the following boundaries intact:

- The **experiment matrix** answers: What configurations exist, and where is their evidence?
- An **evaluation artifact** answers: How did this configuration perform on one named benchmark under one policy?
- A **raw profiling artifact** answers: What happened in one edge-performance invocation?
- A **profile summary** answers: What aggregate edge performance was observed across a declared set of comparable runs?

This structure lets humans review the program as a matrix while allowing scripts and agents to fill missing cells, validate provenance, compare variants, and compute edge Pareto trade-offs without depending on conversational context.

## 5. Infrastructure gate

Before the experiment volume increases substantially, add and test:

- the canonical experiment-matrix JSON schema and initial rows;
- deterministic JSON-to-YAML synchronization;
- an EdgeIMCI run-sidecar schema and profile-summary schema without modifying the official ADTC report schema;
- uniqueness and reference-integrity validation;
- validation of every `submission.json` against the schema bundled with its pinned profiler revision;
- immutable run naming/storage; and
- deterministic summary generation with documented aggregation rules.

Until that infrastructure exists, new experiment output should still preserve exact configuration and provenance, but the project should avoid creating a large collection of loosely named runs that will later need to be reconstructed by hand.

## Sources and change control

This guidance was checked against the following primary sources on 20 August 2026:

- [Africa Deep Tech Challenge 2026 overview, requirements, hardware profile, and scoring](https://adtc-2026.devpost.com/)
- [Official ADTC profiler repository and CLI documentation](https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler)
- [Canonical ADTC profiler JSON Schema](https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler/blob/main/src/adtc_profiler/schema/adtc-profiler.schema.json)
- [Current throughput implementation](https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler/blob/main/src/adtc_profiler/throughput.py)

Recheck these sources before final profiling and submission. If they conflict with this guide, the current competition rules and the profiler schema pinned for the run take precedence; update this document and record the change.
