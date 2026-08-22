# EdgeIMCI Experimental Campaign Map

*Critical path, parallel lanes and evidence-based branches*

**Status:** High-level roadmap for the hackathon campaign; Lundin is off the main track and the domain-expert questionnaire remains separate.

> **Critical-path question:** Can the selected EdgeIMCI checkpoint perform the whole-encounter IMCI task, preserve safe completeness behavior and run effectively on target hardware?

## Main track and parallel data lane

```text
CLINICAL APPROVAL
        |
HOLISTIC GOLDEN SET
        |
SYNTHETIC GENERATION BAKE-OFF
        |
FAST ~1K DATASET  -------------------->  LARGE AZURE BATCH
        |                                  10K / 20K / 30K
QWEN3-1.7B SFT-v1 ON MODAL                       |
        |                                  ARRIVES LATER
CORE CLINICAL EVALS  <------------------  SCALE / NEXT-TRAINING INPUT
        |
TARGET-HARDWARE PROFILE
        |
GOOD ENOUGH?  -- YES --> SELECT / SUBMIT
        | NO
IDENTIFY BOTTLENECK --> TAKE ONLY THE RELEVANT BRANCH --> RE-EVALUATE
```

## Evidence gates

| Gate | Decision point | Minimum evidence |
| ---: | --- | --- |
| 1 | Clinical approval | Semantic rules and holistic cases are approved for use. |
| 2 | Generation recipe | Teacher/prompt behavior is stable; acceptance is high; no systematic semantic corruption. |
| 3 | SFT-v1 | Qwen3-1.7B checkpoint and complete training provenance exist. |
| 4 | Core clinical evals | Holistic classification, integrated management, completeness/withholding and urgent-incomplete results are available. |
| 5 | Target profile | Latency, tok/s, peak RAM, artifact size and deployability are measured on ASUS/target proxy. |
| 6 | Branch decision | A specific bottleneck and expected value justify any additional experiment. |

## Optional branches - only when evidence points there

| Branch | Trigger | Evidence required to keep it |
| --- | --- | --- |
| SFT-v2 | SFT-v1 error analysis shows correctable data or training issues | Improved clinical metrics without new safety regressions |
| 4B SFT / capacity | 1.7B appears capacity-limited or 4B base evidence is compelling | Gain versus 1.7B justifies slower/larger deployment |
| Learning curve | Large batch is available and data-scale value is uncertain | Matched-base 1k/3k/10k comparison |
| Qwen3.5 / Tinker | Specialist branch can test a supported newer model with existing credits | Comparable clinical and deployment evidence |
| Preference / RL | SFT plateaus on a targeted, rewardable behavior | Targeted gain justifies complexity and cost |
| SVD / compression | Size/capacity trade-off warrants a research compression test | Quality-size-speed curve |
| Quantization | Target profile shows meaningful speed, memory or deployability points left on the table | Matched Q8/Q6/Q4 quality-runtime trade-off; otherwise skip |
| Lundin external eval | Time remains after hackathon evidence is secure | Optional research/generalization evidence; never blocks submission |

## Operating rhythm

- Keep the fast approximately 1k lane and large Azure Batch lane concurrent.
- Treat each training, evaluation, generation and profile as a versioned experiment with automatic provenance.
- Compare scientific outcomes alongside time, usage and cost; do not confuse cheap execution with useful evidence.
- Branch from measured bottlenecks, not from a desire to run every available technique.
- Keep Lundin off the hackathon critical path and keep the domain-expert clinical questionnaire in its separate review document.

## Current next sequence

1. Complete clinical approval and freeze the holistic golden set.
2. Run the teacher/prompt bake-off and lock the first stable generation recipe.
3. Generate approximately 500-1,000 accepted examples and launch the large Azure Batch lane in parallel.
4. Train Qwen3-1.7B SFT-v1 on Modal; run the core clinical evaluation battery.
5. Profile the selected artifact on ASUS/target proxy; select, submit or branch according to the observed bottleneck.
