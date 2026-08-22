# Instructions for the oracle-v3 respiratory remediation re-review agent

> **Authority:** `WORKING_PLAN` · **Lifecycle:** `SUPERSEDED` · Completed oracle-v3 verification protocol retained for audit history.

## Assignment

Independently verify the remediation of `HGRR-FIND-001`, `HGRR-FIND-002`, and `HGRR-FIND-003` in the current 78-case product-level holistic golden suite. Confirm that the changes close the findings without unrelated semantic drift, then issue a technical/source readiness recommendation for the separate human/domain approval gate.

This is review-only. Do not modify clinical or policy artifacts, evaluator code, tests, generator, golden records, manifest, lifecycle flags, or prior review records.

## Target

- Branch: `main`
- Suite: `edge-imci-holistic-product-golden-v1`
- Case count: 78
- Semantic JSONL SHA-256: `e8c538ac7a82b8faae7b7e36644eb3c44751c88380621e87625d1f703c5a70a1`
- Rule set: `imci-major-sick-child-v1`
- Completeness policy: `imci-major-sick-child-holistic-completeness-v2`
- Original review decisions: `imci-major-sick-child-review-decisions-v1`
- Oxygen-referral disposition: `imci-major-sick-child-oxygen-referral-disposition-v1`
- Scope disposition: `edge-imci-holistic-golden-scope-dispositions-v1`
- Schema: `edge-imci-major-sick-child-encounter-v1`
- Oracle: `edge-imci-holistic-deterministic-oracle-v3`
- Golden record schema: `edge-imci-holistic-golden-semantic-record-v3`
- Generator: `edge-imci-holistic-golden-generator-v3`
- Validator: `edge-imci-holistic-golden-validator-v3`
- Seed: `20260822`

Stop and report drift if the hash or any pin differs.

## Required reading

Read completely:

1. `docs/README.md`
2. `docs/product_holistic_golden_domain_re_review_v1.md`
3. `docs/product_holistic_golden_domain_re_review_v1.csv`
4. `configs/information_policy/imci_major_sick_child_oxygen_referral_disposition_v1.json`
5. `configs/information_policy/imci_major_sick_child_review_decisions_v1.json`
6. `configs/information_policy/imci_major_sick_child_holistic_completeness_v2.json`
7. `data/rules/imci_major_sick_child_v1.json`
8. `src/edge_imci/evaluation/holistic.py`
9. `src/edge_imci/generation/holistic_golden.py`
10. `tests/test_holistic_major_sick_child.py`
11. `tests/test_holistic_golden_suite.py`
12. `tests/test_system_level_clinical_audit_v2.py`
13. `tests/test_holistic_artifacts.py`
14. `data/golden/holistic_product_v1/manifest.json`
15. `data/golden/holistic_product_v1/semantic_cases.jsonl`
16. `docs/product_holistic_golden_review_v1.md`
17. `docs/major_sick_child_expansion_map_v1.md`

Use `data/sources/IMCI chartbooklet 2014.pdf` for direct verification where needed. Do not use general medical knowledge to alter the pinned decisions.

## Permitted outputs

Create only:

- `docs/product_holistic_golden_domain_re_review_v2.md`
- `docs/product_holistic_golden_domain_re_review_v2.csv`

Leave `.letta/` and unrelated changes untouched. Do not commit or push unless explicitly requested.

## Baseline checks

1. Record `git status --short --branch`.
2. Verify the target hash, all pins, 78 unique IDs, manifest count and JSONL/YAML equality.
3. Run the full test suite.
4. Run both deterministic synchronization/generation scripts and confirm no diff in generated artifacts.
5. Confirm the suite remains `PROPOSED_FOR_DOMAIN_REVIEW` and ineligible for generation, teacher bake-off, product evaluation and training.

## Finding closure checks

### HGRR-FIND-001 — oxygen referral presentation

Verify `hpg-016-resp-oximeter-89-9` against the source footnote and `imci-major-sick-child-oxygen-referral-disposition-v1`:

- `REFER_FOR_OXYGEN_SATURATION_BELOW_90` is emitted;
- `urgent_action_required` is false solely from this finding;
- the referral is absent from `urgent_actions`;
- `IP-CQ-004` is not attached solely from this finding;
- applicable cough/cold actions remain in `final_actions` rather than `deferred_actions`;
- `product_policy_disposition_ids` contains exactly the oxygen disposition for this case and no others.

### HGRR-FIND-002 — false fast-breathing traces

Re-review the 15 originally affected cases: `hpg-007`, `hpg-010`, `hpg-013`–`hpg-019`, `hpg-023`–`hpg-026`, `hpg-070`, and `hpg-076`.

Confirm that an age-specific `FAST_BREATHING` derived-finding rule appears in `fired_rule_ids` and source provenance only when a valid calm, one-minute respiratory rate meets its age threshold. A below-threshold or invalid measurement must not fire that rule. Do not confuse an evaluated-but-false condition with a fired rule.

Also verify positive neighbours `hpg-008`, `hpg-009`, `hpg-011`, `hpg-012`, `hpg-020`, `hpg-021`, and `hpg-022` so the correction has not removed legitimate threshold traces.

### HGRR-FIND-003 — premature respiratory classification

Verify:

- `hpg-022` emits the bronchodilator trial/reassessment sequence and missing post-treatment evidence but no internal or final respiratory classification and no pneumonia-classification rule;
- `hpg-023` and `hpg-024` remain incomplete and emit no internal or final respiratory classification from invalid rate evidence;
- independently sufficient severe or chest-indrawing findings still classify when their own source-valid evidence is present;
- completed bronchodilator cases `hpg-020` and `hpg-021` classify from valid post-treatment findings.

## Drift boundary

Relative to reviewed hash `bba39ee0a06e9630d90996dd01e931807bf1e50f861e040355c6de165e40e8a9`, intended changes are:

- non-urgent referral/action presentation and policy provenance for `hpg-016`;
- removal of false derived-rule traces/provenance from the 15 `HGRR-FIND-002` cases;
- removal of premature respiratory classification/traces from `hpg-022`, `hpg-023`, and `hpg-024`;
- oracle/generator/validator/record-schema pins advancing to v3;
- the new oxygen disposition pin/provenance.

The earlier severe-measles correction and all other classification, completeness, action and provenance behavior must remain intact. Any unexplained change is a new finding.

## Deliverables

The CSV must contain exactly one row for each of the 78 cases, in canonical order, with these columns:

```text
golden_case_id
review_family
primary_verdict
severity
input_unknowns_review
scope_validity_review
completeness_withholding_review
classification_review
action_review
trace_provenance_review
review_decision_review
finding_ids
review_notes
```

Use `PASS_SOURCE_ALIGNED`, `DEFECT_CASE_SPEC`, `DEFECT_ORACLE_OR_SCHEMA`, `DEFECT_PROVENANCE`, or `NEEDS_HUMAN_CLINICAL_REVIEW`. Populate every review dimension.

The Markdown report must use:

- authority `REVIEW_RECORD`;
- lifecycle `CURRENT`;
- status exactly `TECHNICAL_SOURCE_REVIEW_COMPLETE` or `TECHNICAL_SOURCE_REVIEW_BLOCKED`;
- exact target hash and pins;
- a closure disposition for all three `HGRR` findings;
- any new findings with exact affected IDs and evidence;
- baseline and final verification results;
- confirmation that all 78 CSV rows were reviewed; and
- exactly one final recommendation: `READY_FOR_HUMAN_DOMAIN_APPROVAL` or `NOT_READY_FOR_HUMAN_DOMAIN_APPROVAL`.

`READY_FOR_HUMAN_DOMAIN_APPROVAL` is not clinical approval, corpus freeze, or downstream-generation authorization.
