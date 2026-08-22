# Product-level holistic golden semantic suite v1 — oracle-v3 technical/source re-review

> **Authority:** `REVIEW_RECORD` · **Lifecycle:** `CURRENT` · Same-agent technical/source verification; not independent human/domain approval and not production clinical authorization.

**Review status:** `TECHNICAL_SOURCE_REVIEW_COMPLETE`

**Final recommendation:** `READY_FOR_HUMAN_DOMAIN_APPROVAL`

**Suite reviewed:** `edge-imci-holistic-product-golden-v1`

**Semantic corpus SHA-256:** `e8c538ac7a82b8faae7b7e36644eb3c44751c88380621e87625d1f703c5a70a1`

**Review date:** 2026-08-22

**Companion verdict matrix:** [`product_holistic_golden_domain_re_review_v2.csv`](product_holistic_golden_domain_re_review_v2.csv)

## 1. Scope and limitation

All 78 semantic records were revalidated after the oracle-v3 respiratory remediation. The review covered structured inputs and UNKNOWN behavior, scope, completeness and withholding, internal and final classifications, urgent/intermediate/deferred/final actions, rule and action traces, source and requirement provenance, review-decision applicability, and the new oxygen-referral product-policy provenance.

The same coding agent that implemented the remediation performed this verification at the user's request. It is therefore a rigorous same-agent technical/source re-review, not an organizationally independent review. That limitation does not change the mechanical evidence below, but it must remain visible to the human/domain approver.

This record does not itself provide human clinical approval, freeze the corpus, authorize production clinical use, or make the suite eligible for language generation, teacher selection, product evaluation, or training.

## 2. Pinned target

| Artifact | Pinned identity |
| --- | --- |
| Clinical rule set | `imci-major-sick-child-v1` |
| Holistic completeness policy | `imci-major-sick-child-holistic-completeness-v2` |
| Original review decisions | `imci-major-sick-child-review-decisions-v1` |
| Oxygen-referral disposition | `imci-major-sick-child-oxygen-referral-disposition-v1` |
| Plan B/C scope disposition | `edge-imci-holistic-golden-scope-dispositions-v1` |
| Whole-encounter schema | `edge-imci-major-sick-child-encounter-v1` |
| Deterministic oracle | `edge-imci-holistic-deterministic-oracle-v3` |
| Golden record schema | `edge-imci-holistic-golden-semantic-record-v3` |
| Generator | `edge-imci-holistic-golden-generator-v3` |
| Validator | `edge-imci-holistic-golden-validator-v3` |
| Generation seed | `20260822` |

The canonical JSONL hash matches the manifest, and the YAML suite is an exact data mirror.

## 3. Result

| Result | Count |
| --- | ---: |
| Cases reviewed | 78 |
| `PASS_SOURCE_ALIGNED` | 78 |
| Non-pass cases | 0 |
| P0–P3 findings | 0 |
| Open findings | 0 |

Every CSV row contains a populated verdict and all review dimensions. No new technical/source defect was found in the pinned v3 target.

## 4. Finding closure

### HGRR-FIND-001 — oxygen-referral presentation: `CLOSED`

For `hpg-016-resp-oximeter-89-9`:

- `REFER_FOR_OXYGEN_SATURATION_BELOW_90` is present in `final_actions`;
- `urgent_action_required` is false and `urgent_actions` is empty;
- `IP-CQ-004` is not attached solely from the oxygen finding;
- cough/cold home-management actions remain in `final_actions` and nothing is deferred;
- `product_policy_disposition_ids` contains exactly `imci-major-sick-child-oxygen-referral-disposition-v1`;
- no other case claims that disposition.

This matches the source-literal, human-approved hackathon disposition: “refer” is not strengthened to “refer urgently.”

### HGRR-FIND-002 — false fast-breathing traces: `CLOSED`

The 15 previously affected cases were checked individually: `hpg-007`, `hpg-010`, `hpg-013`–`hpg-019`, `hpg-023`–`hpg-026`, `hpg-070`, and `hpg-076`.

An age-specific fast-breathing derived rule now appears in `fired_rule_ids` and source provenance only when a calm, one-minute rate meets the correct age threshold. Below-threshold and invalid measurements no longer claim that the rule fired. Positive boundary and bronchodilator-neighbour cases retain their legitimate threshold traces.

### HGRR-FIND-003 — premature respiratory classification: `CLOSED`

- `hpg-022` emits the required bronchodilator trial/reassessment and missing post-treatment evidence, but no respiratory classification or pneumonia-classification rule.
- `hpg-023` and `hpg-024` remain incomplete and expose no internal or final respiratory classification from invalid rate evidence.
- `hpg-020` and `hpg-021` continue to classify from valid post-bronchodilator findings.
- Independently sufficient danger-sign, stridor, and chest-indrawing branches remain represented in their applicable cases.

This matches `IP-CQ-003`, `MSC-CQ-RESP-001`, and the canonical respiratory rule conditions.

## 5. Whole-suite checks

- 78 unique case IDs were present in canonical order.
- All 78 records passed the v3 validator and deterministic recomputation.
- JSONL SHA-256 matched the manifest exactly.
- JSONL and YAML contained equal structured records.
- Every coverage array contained unique tags.
- Exact review-decision applicability and non-firing requirement/scope provenance remained valid.
- The oxygen disposition was attached to exactly one applicable case.
- Severe-complicated-measles immediate treatments remained repaired.
- Incomplete encounters continued to withhold final classifications and final action synthesis while retaining known urgent/intermediate actions where supported.
- All downstream eligibility flags remained false for holistic generation, product evaluation, teacher bake-off and training.
- No conversational rendering or training records were introduced.

## 6. Determinism and verification

The clinical/policy synchronization and golden-suite generator were run twice around the review. SHA-256 values for the canonical JSONL, YAML mirror, manifest, generated review package and oxygen-disposition YAML were unchanged.

Verification results:

- full repository test suite: `288 passed`;
- focused 78-record semantic audit: `78/78 records validated`;
- all three HGRR closure invariant groups passed;
- `git diff --check`: passed.

## 7. Recommendation and next gate

The oracle-v3 semantic suite is technically/source-aligned within the approved bounded hackathon representation and is ready to be presented for human/domain approval.

The human/domain approver should review the current hash and this record, explicitly approve or reject the 78 semantic targets, and authorize a controlled freeze only if satisfied. Until that approval and lifecycle change occur, golden-language rendering, teacher bake-off, bulk generation, training and product evaluation remain blocked.

**Final recommendation:** `READY_FOR_HUMAN_DOMAIN_APPROVAL`
