# Beta0-1K Multitask Dataset Provenance

**Historical 1,831-row dataset, not the selected 2,258-row 4B-alpha-second
release.** See the [selected artifact packet](4B-alpha-second/README.md) and its
[dataset provenance](4B-alpha-second/dataset_info.md) for the selected release.

## Identity

| Field | Value |
|---|---|
| Release ID | `beta0_1k_multitask_v1` |
| Manifest SHA-256 | `f326d23a8d9ffa4017b510e13933e8a8db08db9ccfb11e5f3a8a36f148987a7a` |
| TRAIN rows | 1,831 |
| TRAIN SHA-256 | `952a785b478654097bff3d643ca743d2d5a078de4f2c2e5b125f87b47dbab367` |
| VALIDATION rows | 139 |
| VALIDATION SHA-256 | `76dc64d51f52a8ffbb7a10c5fd10a3fff770a7ee6847cf7fb62c9a00568a58c5` |
| Sampling | Unique rows, no oversampling or task-family reweighting |
| Review tag | `AI_CURATED_CLINICAL_REVIEW_PENDING` |
| TEST accessed | No |
| TEST overlap checked | No |

Both shortlisted candidates used these exact bytes. The validation partition contains 115 legacy structured-extraction cases and 24 provisional routing cases. It contains no free-form validation cases.

## TRAIN Composition

| Component | Rows |
|---|---:|
| Retained Beta0-1K extraction backbone | 1,074 |
| Legacy Alpha 3 free-form | 58 |
| Granular Alpha 3 v2 free-form | 280 |
| Delta 1 self-knowledge | 15 |
| Delta 2 v2 scope/safety | 44 |
| Delta 3 proposition/negation | 21 |
| Paired granular extraction-v2 controls | 280 |
| Tagged routing companions | 59 |
| **Total** | **1,831** |

The full release is not called Beta0. Only the retained 1,074-row extraction backbone is Beta0-1K; the other 757 rows are additions.

TRAIN mode counts are 1,434 `EXTRACTION` and 397 `FREE_FORM` records. Base reconciliation retained 1,074 rows, removed 159 normalized duplicates, and excluded six known quarantine IDs before the additions were applied.

## Leakage And Split Controls

The release compared all 1,831 TRAIN rows with all 139 VALIDATION rows using transitive lineage, leakage-group, normalized-prompt, normalized-target, and normalized-evidence checks. It reported `PASS_NO_DETECTED_OVERLAP`, no quarantined retained row, and no removed validation row.

This is a bounded statement, not proof of arbitrary semantic independence. Shared route labels are class-label reuse rather than parent identity. No sealed TEST data was accessed or compared.

## Authorization Boundary

The dataset manifest predates training and records construction-only authorization. Research training was authorized separately by `edge-imci-beta0-1k-backbone-multitask-matrix-authorization-20260922-v1`, SHA-256 `387b19fa0b363b4a7451aa9ad09d419ac032598a8ed74c544c29f397cd4ffe30`.

That later authorization permits the eight-cell paid research campaign only. It does not authorize promotion, deployment, TEST access, clinical signoff, or production clinical use.

## Source Availability

The authoritative source paths are in the private research workspace:

```text
data/training_sources/beta0_1k_multitask_v1/manifest.json
data/training_sources/beta0_1k_multitask_v1/train.jsonl
data/training_sources/beta0_1k_multitask_v1/validation.jsonl
configs/review/beta0_1k_matrix_authorization_20260922_v1.json
```

At the time of this historical candidate packet, a public immutable dataset URL and a consolidated dataset-license record had not yet been added to this submission repository. The selected release's later public reconstruction is documented in the linked selected packet; consolidated dataset-license review remains pending.
