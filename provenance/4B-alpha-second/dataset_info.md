# Enriched 2,258-Row Dataset

## Exact Training Inputs

| Item | Value |
|---|---|
| Release | `beta0_1k_multitask_enriched_2258_v1` |
| Source | EdgeIMCI private research workspace, `data/training_sources/beta0_1k_multitask_enriched_2258_v1/` |
| Manifest SHA-256 | `0820f092ed585a46182e075477f9246917629061b03a3f57d92cb1087e303706` |
| TRAIN | 2,258 records |
| TRAIN SHA-256 | `95945aa2e451f67348f4600e57c17e4a4acd278f285f2f1fbea9df4b633805f7` |
| VALIDATION | 139 records |
| VALIDATION SHA-256 | `76dc64d51f52a8ffbb7a10c5fd10a3fff770a7ee6847cf7fb62c9a00568a58c5` |
| Training run | `multitask2258-20260922-v1--qwen4-e2-lr3-s20260824` |
| Review | `AI_CURATED_CLINICAL_REVIEW_PENDING` |
| TEST used | No, according to the original training receipt |
| Public repository | `Nini0la/edgeimci-beta0-1k-multitask-enriched-2258-v1` |
| Public revision | `da8daa8efbd583d92000920366085f6dd00c3fb2` |
| Public TRAIN JSONL SHA-256 | `475934f7def41d3825f4544f7bc911588c58715a7df8946d4337607eb2cf8c78` |
| Public TRAIN Parquet SHA-256 | `f9334b24e9f440cfd21e85d7b3dcb50a404fe22390708e8ddf3ccb0320aaf670` |
| Public VALIDATION Parquet SHA-256 | `e66f04506b46ac09483c80adda95f557b8862ed69db567b46d57ca9f79327ff2` |
| Public license declaration | `other`; no general redistribution license asserted |

The frozen identities come from the original `remote_run_manifest.json`, not
filenames or a later evaluation harness. The final internal TRAIN file was not
retained in reachable repository state. The public TRAIN serialization is therefore
a deterministic message-normalized reconstruction from the hash-verified baseline
and enrichment sources, not a claim of byte identity. VALIDATION is byte-identical.

## Construction and Sources

This is project-authored synthetic multitask data: structured encounter extraction,
free-form assessment language, project self-knowledge, scope/safety, and
proposition/negation examples. It builds on the 1,831-row release documented in
[`../dataset_info.md`](../dataset_info.md), plus 427 enrichment candidates.
The surviving upstream candidate package describes 338 Alpha3, 45 Delta1, and 44
Delta2 additions. That candidate package is not a substitute for the final,
hash-pinned training release or its later research-training authorization.

Clinical source background: WHO, *Integrated Management of Childhood Illness,
Chart Booklet*, March 2014, ISBN 978 92 4 150682 3. EdgeIMCI's encoding and synthetic
examples are not WHO-authored. The WHO booklet is not redistributed here.
The research code source is `https://github.com/Nini0la/edge-imci`. The public
dataset is available at
`https://huggingface.co/datasets/Nini0la/edgeimci-beta0-1k-multitask-enriched-2258-v1/tree/da8daa8efbd583d92000920366085f6dd00c3fb2`.

The original recipe used one shuffled pass per TRAIN row per epoch, without
oversampling or task-family reweighting. Validation stayed at the same 139-row
partition. It contains structured-extraction and routing examples, not a
comprehensive free-form evaluation. No clinical effectiveness claim follows from
these validation numbers.

## Publication and Review Status

See [Dataset Source and Rights Disclosure](../dataset/source_rights.md) for the
source inventory, official rights-policy references, and the owner's 2026-09-22
confirmation of no separate permissions. Documentation is complete for those
facts; source/provider rights clearance remains unresolved. This does not change
the public dataset's license declaration or its immutable publication record.

- Public immutable dataset release: complete at revision
  `da8daa8efbd583d92000920366085f6dd00c3fb2`; anonymous loading verified.
- Consolidated dataset/source license review: pending. The public card uses
  `license: other` and does not infer permission from the base model or research
  code license.
- Independent clinical/manual fact-fidelity review: pending.
- Exact original internal TRAIN serialization: not present. The public manifest
  records both the frozen training identity and the reconstructed publication hashes.
  Original configuration, adapter, logs, and receipt are retained.

The research-training authorization hash is
`4346fea115d30a9fe9ff60a32435f31d9bf28c6ae05a35cdd62c3275be035c67`.
It is distinct from subsequent owner selection for public model hosting/profiling
and does not constitute clinical-use authorization.
