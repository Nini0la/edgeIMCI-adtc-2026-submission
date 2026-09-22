# Shortlisted Candidate Validation Evidence

## Evaluation Boundary

These are terminal-epoch results from the same 139-row unsealed VALIDATION partition used during research selection. The partition contains 115 structured-extraction cases and 24 routing cases. No TEST data was accessed. The newer 68-case free-form DEV reviewer slice was not run against these candidates because independent clinical and source-governance review is still pending.

These metrics are training-validation evidence, not laptop profiling, clinical qualification, or promotion approval.

## Results

| Metric | `qwen17-e3-lr1-s3407` | `qwen4-e2-lr3-s20260824` |
|---|---:|---:|
| Validation predictions present | 139 / 139 | 139 / 139 |
| JSON valid | 139 / 139 | 139 / 139 |
| Strict schema valid | 138 / 139 (99.28%) | 136 / 139 (97.84%) |
| Whole prediction exact match | 129 / 139 (92.81%) | 133 / 139 (95.68%) |
| Route correct | 134 / 139 (96.40%) | 135 / 139 (97.12%) |
| Original-115 extraction exact | 112 / 115 (97.39%) | 114 / 115 (99.13%) |
| Original-115 field accuracy | 99.92% | 99.13% |
| Original-115 decision equivalence | 97.39% | 99.13% |
| False rejects | 1 / 119 | 2 / 119 |
| Unsafe engine admissions | 2 / 20 | 0 / 20 |
| Urgent misses | 3 / 4 | 1 / 4 |
| Token-limit events | 0 | 0 |

On this limited validation partition, the 4B candidate has stronger exact-match, routing, decision-equivalence, unsafe-admission, and urgent-miss results. The 1.7B candidate has higher strict-schema validity and field accuracy and one fewer false reject. The urgent subset contains only four examples, so its rates are descriptive rather than stable estimates.

## Checkpoint Evidence

| Field | `qwen17-e3-lr1-s3407` | `qwen4-e2-lr3-s20260824` |
|---|---:|---:|
| Requested/completed epochs | 3 / 3 | 2 / 2 |
| Terminal exported epoch | 3 | 2 |
| Lowest validation loss | 0.013410131447017193 | 0.008947928436100483 |
| Lowest-loss epoch | 2 | 2 |
| Final reported train loss | 0.18812984095319457 | 0.12006764726146407 |
| Same-call recoveries | 0 | 0 |

The 1.7B terminal export is epoch 3 even though epoch 2 had the lowest validation loss. This is intentional under the preregistered terminal-epoch export policy.

## Restrictions

Both result receipts record:

- `status=SUCCEEDED`
- `clinical_gold_status=PENDING_CLINICAL_REVIEW`
- `clinical_use_authorized=false`
- `promotion_authorized=false`
- `test_partition_used=false`
- `review_tag=AI_CURATED_CLINICAL_REVIEW_PENDING`

Neither result should be described as clinically approved, promoted, deployed, or equivalent to a final GGUF submission artifact.
