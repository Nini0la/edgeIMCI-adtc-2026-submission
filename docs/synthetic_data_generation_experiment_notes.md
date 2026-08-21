# EdgeIMCI Synthetic Data Generation — Experiment Notes

## Purpose

This document records practical guidance, teacher-model options, and experimental hypotheses for generating the natural-language portion of the EdgeIMCI training corpus.

EdgeIMCI separates:

- **deterministic clinical semantics** — clinical truth, information state, required acquisitions, classifications, actions, and trajectory logic;
- **LLM-generated language** — realistic user presentations, PHC-worker phrasing, questions, measurements, observations, multi-turn dialogue, and final assistant responses.

The language-generation layer is therefore a **core part of the dataset factory** and should be treated as an experimental component of model training.

---

## 1. Core generation principle

Do not ask an LLM to invent the medicine.

Generate in this direction:

```text
structured clinical truth
        ↓
partial-reveal / trajectory logic
        ↓
deterministic information-policy result
        ↓
structured expected assistant semantics
        ↓
teacher LLM
        ↓
natural-language realization
```

The structured semantic trajectory is the durable asset. Natural-language realizations can be regenerated with different teachers, prompts, styles, and sampling settings without changing the underlying clinical truth.

---

## 2. Treat rendering strategy as an experimental variable

The teacher should perform **controlled semantic-to-language transformation**, not generic paraphrasing.

Useful rendering modes may include:

- caregiver-style initial presentation;
- concise PHC-worker presentation;
- clinical shorthand;
- measurement-acquisition interaction;
- clinician-observation interaction;
- incomplete multi-turn dialogue;
- urgent-escalation dialogue;
- final classification/action response.

The rendering prompt itself may matter as much as, or more than, simply choosing a larger teacher model once the teacher is capable enough.

---

## 3. Teacher size should not be assumed to determine quality

Do not assume:

```text
largest teacher = best dataset
```

Teacher selection should be empirical.

A smaller or mid-tier model may be better suited to constrained rewriting than a much larger model, especially if it:

- preserves semantics more reliably;
- follows the rendering contract more closely;
- is cheaper;
- produces more accepted samples per unit cost.

The relevant metric is not model prestige. It is downstream usefulness.

---

## 4. Judge synthetic data by what the student learns

Generation-level quality is necessary but not sufficient.

Track generation-level metrics such as:

- semantic fidelity;
- naturalness;
- acquisition-mode fidelity;
- diversity;
- rejection rate;
- retry rate;
- latency / throughput;
- cost per accepted sample.

But ultimately compare teacher/rendering choices by the resulting student model:

- final classification accuracy;
- premature-classification rate;
- required-acquisition recall;
- unnecessary-acquisition rate;
- danger-sign omission;
- referral/action correctness;
- multi-turn completion;
- turn efficiency.

A dataset that sounds better is not automatically a dataset that trains better.

---

## 5. Measure cost per accepted trajectory

Do not optimize only for:

```text
$/million tokens
```

Prefer:

```text
$/accepted semantically valid trajectory
```

Track at minimum:

- teacher provider;
- teacher model/version;
- input tokens;
- output tokens;
- requested variants;
- valid outputs;
- rejected outputs;
- retries;
- total generation cost;
- cost per accepted output.

A cheap teacher with high semantic-failure rates may be more expensive in practice than a stronger teacher.

---

## 6. Generate semantic trajectories once; render them many ways

A canonical semantic trajectory should be reusable.

Example:

```text
semantic trajectory #1842
        ↓
renderer A → concise PHC English
renderer B → conversational PHC English
renderer C → caregiver-heavy presentation
renderer D → terse worker shorthand
```

This means later fine-tuning experiments can change the language distribution without regenerating the clinical substrate.

---

## 7. Multiple variants are a useful experimental axis

For each semantic trajectory, test values such as:

```text
N = 1
N = 2
N = 4
```

Possible strategies:

- keep every semantically valid variant;
- select the best valid variant;
- retain a small diverse subset;
- use several variants only for difficult/important trajectories.

Because EdgeIMCI has deterministic structured truth, generated variants can be checked against a strong semantic reference instead of being accepted blindly.

Whether more variants improve the student should be tested rather than assumed.

---

## 8. Diversity should be clinically meaningful

Useful diversity includes:

- different caregiver wording for the same fact;
- concise vs verbose worker input;
- different ordering of supplied facts;
- measured values vs qualitative reports;
- partial information;
- realistic distractors;
- different conversational lengths;
- different levels of clinical shorthand.

Avoid lexical variation that adds no meaningful robustness.

Do not allow stylistic variation to change acquisition mode or clinical meaning.

For example:

```text
"She seems to be breathing fast."
```

must not silently become equivalent to:

```text
"Respiratory rate measured at 52 breaths/minute."
```

---

# 9. Teacher / inference implementation options

## Option A — Azure / Foundry API

Likely the easiest first production route.

Use normal programmatic API calls while developing and validating the renderer.

Advantages:

- existing Azure access;
- minimal serving infrastructure;
- straightforward Python integration;
- easy teacher bake-offs;
- easy prompt iteration.

Before large-scale use, verify which models are covered by available Azure credits versus separately billed Marketplace models.

---

## Option B — Azure batch generation

Once the renderer contract is stable, batch inference is a natural large-scale route.

Conceptually:

```text
semantic trajectories
        ↓
JSONL generation requests
        ↓
Azure batch job
        ↓
raw teacher outputs
        ↓
EdgeIMCI semantic validation
        ↓
accepted / rejected corpus
```

Codex or another coding agent should **build the pipeline**, not sit inside the generation loop.

The actual generation run should be a normal programmatic batch workload.

---

## Option C — Other hosted model APIs

Keep the rendering interface provider-neutral.

Other hosted APIs may become preferable because of:

- lower token cost;
- better batch pricing;
- strong open-model availability;
- higher throughput;
- a particular model performing unusually well on constrained clinical rendering.

Provider choice should remain an experimental decision, not an architectural dependency.

---

## Option D — Self-host an open teacher on Modal

This is the main alternative if API economics become unattractive or if an open teacher performs especially well.

Conceptually:

```text
semantic trajectories
        ↓
generation script
        ↓
Modal GPU
        ↓
vLLM-hosted open teacher
        ↓
natural-language variants
        ↓
semantic validators
        ↓
accepted dataset
```

Modal can provide the GPU/runtime layer while vLLM handles high-throughput inference.

A typical implementation would:

- choose a strong open instruct model;
- cache model weights;
- launch vLLM on a Modal GPU;
- expose or call the model programmatically;
- issue many concurrent generation requests;
- persist raw responses;
- validate and write accepted/rejected records.

For dataset generation, the main goal is not low-latency serving. It is:

> **keep the GPU saturated and maximize accepted trajectories per GPU-hour.**

The relevant cost metric becomes:

```text
GPU $/hour
÷ accepted trajectories/hour
=
$/accepted trajectory
```

Compare that directly with API/batch alternatives.

This option is operationally heavier than using an API, so it should be selected because of measured cost/quality/throughput advantages rather than by default.

---

# 10. Initial teacher bake-off

Use the very small golden semantic slice as the first teacher benchmark.

Hold the clinical semantics constant.

Example:

| Teacher | Provider | Renderer | Variants | Semantic pass rate | Naturalness | Cost / accepted | Student result |
|---|---|---|---:|---:|---:|---:|---:|
| Teacher A | Azure | v1 | 1 | ? | ? | ? | ? |
| Teacher A | Azure | v2 | 4 | ? | ? | ? | ? |
| Teacher B | Azure | v1 | 1 | ? | ? | ? | ? |
| Teacher C | Modal/vLLM | v1 | 1 | ? | ? | ? | ? |

Do not select the final teacher solely by inspecting prose.

---

# 11. Scale the dataset empirically

Do not immediately generate the maximum affordable corpus.

Prefer an approximate learning curve such as:

```text
1k
3k
10k
30k
...
```

Run comparable SFT experiments and measure where additional synthetic data stops producing useful gains.

This answers:

> **How much synthetic language does this bounded clinical specialization actually need?**

If 10k examples saturate performance, generating 100k or 500k may be wasteful.

---

# 12. Generation configuration should be versioned

Each generation run should record at least:

```text
semantic_dataset_version
rule_set_id
information_policy_id
teacher_provider
teacher_model
teacher_version
render_prompt_version
sampling_temperature
top_p
variants_per_trajectory
max_output_tokens
validation_version
generation_seed
generation_cost
accepted_count
rejected_count
```

This makes synthetic-data generation reproducible and comparable across experiments.

---

# 13. Working EdgeIMCI hypotheses

These are hypotheses to test, not assumptions:

1. A capable mid-tier teacher may generate EdgeIMCI language as effectively as a much larger frontier model.
2. Rendering-prompt design may matter more than teacher size after a capability threshold.
3. Multiple controlled variants per semantic trajectory may improve robustness.
4. Deterministic semantic truth may make filtering / Best-of-N unusually valuable for EdgeIMCI.
5. Teacher quality should ultimately be judged by student-model improvement.
6. The optimal corpus size may be relatively modest because the current clinical scope is bounded.
7. Once the generation pipeline is stable, new IMCI areas such as **fever** should reuse substantially the same language-generation infrastructure.

---

# 14. Bottom line

Treat synthetic language generation as an experiment over:

```text
semantic truth
× rendering strategy
× teacher model
× inference source
× sampling strategy
× variants per trajectory
× corpus size
→ student performance
```

The objective is not to generate the largest dataset possible.

The objective is to find the **cheapest, fastest, semantically faithful generation setup that produces the best student model**.

---

## References

- FinePhrase — Hugging Face: https://huggingface.co/spaces/HuggingFaceFW/finephrase#whats-next
- Modal vLLM inference example: https://modal.com/docs/examples/vllm_inference
