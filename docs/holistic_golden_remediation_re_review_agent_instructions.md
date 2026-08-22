# Instructions for the holistic golden remediation re-review agent

> **Authority:** `WORKING_PLAN` · **Lifecycle:** `SUPERSEDED` · Completed re-review protocol retained for audit history; use `holistic_golden_respiratory_remediation_re_review_agent_instructions.md` for the current handoff.

## Assignment

Independently re-review the remediated `edge-imci-holistic-product-golden-v1` suite. Confirm whether the four findings recorded against the earlier corpus hash have been closed without unrelated semantic drift, then repeat the technical/source-backed review across all 78 cases.

This is a review-only task. Do not modify the evaluator, generator, canonical clinical/policy artifacts, golden records, manifest, generated review package, or lifecycle flags. Do not create language renderings, datasets, prompts, splits, training artifacts, or model runs.

The prior review remains historical evidence at:

- `docs/product_holistic_golden_domain_review_v1.md`
- `docs/product_holistic_golden_domain_review_v1.csv`

It reviewed SHA-256 `6cc773cf467e69135ad29e6018b894b749c8689122e6c92d585ce5bffd3df8b9` and returned `NOT_READY_FOR_HUMAN_DOMAIN_APPROVAL`.

## Pinned remediation target

- Branch: `main`
- Suite: `edge-imci-holistic-product-golden-v1`
- Records: 78
- Target semantic JSONL SHA-256: `bba39ee0a06e9630d90996dd01e931807bf1e50f861e040355c6de165e40e8a9`
- Rule set: `imci-major-sick-child-v1`
- Completeness policy: `imci-major-sick-child-holistic-completeness-v2`
- Review-decision set: `imci-major-sick-child-review-decisions-v1`
- Scope-disposition set: `edge-imci-holistic-golden-scope-dispositions-v1`
- Schema: `edge-imci-major-sick-child-encounter-v1`
- Oracle: `edge-imci-holistic-deterministic-oracle-v2`
- Record schema: `edge-imci-holistic-golden-semantic-record-v2`
- Validator: `edge-imci-holistic-golden-validator-v2`
- Generator: `edge-imci-holistic-golden-generator-v2`
- Seed: `20260822`

If the target hash or any pin differs before review begins, stop and report repository drift. Do not review a moving target.

## Required reading

Read these files completely before reaching a verdict:

1. `docs/README.md`
2. `docs/product_holistic_golden_domain_review_v1.md`
3. `docs/product_holistic_golden_domain_review_v1.csv`
4. `data/rules/imci_major_sick_child_v1.json`
5. `configs/information_policy/imci_major_sick_child_holistic_completeness_v2.json`
6. `configs/information_policy/imci_major_sick_child_review_decisions_v1.json`
7. `configs/golden/holistic_product_golden_scope_dispositions_v1.json`
8. `src/edge_imci/schemas/holistic.py`
9. `src/edge_imci/evaluation/holistic.py`
10. `src/edge_imci/generation/holistic_golden.py`
11. `tests/test_holistic_major_sick_child.py`
12. `tests/test_holistic_golden_suite.py`
13. `data/golden/holistic_product_v1/manifest.json`
14. `data/golden/holistic_product_v1/semantic_cases.jsonl`
15. `docs/product_holistic_golden_review_v1.md`
16. `docs/major_sick_child_expansion_map_v1.md`
17. `docs/major_sick_child_domain_review_v1.md`
18. `docs/product_holistic_golden_suite_requirements_v1.md`

Use `data/sources/IMCI chartbooklet 2014.pdf` for direct source verification where present. Do not substitute general medical knowledge for the pinned source or approved decisions.

## Strict change boundary

You may create only:

- `docs/product_holistic_golden_domain_re_review_v1.md`
- `docs/product_holistic_golden_domain_re_review_v1.csv`

Leave `.letta/` and every unrelated worktree change untouched. Do not commit or push unless the user explicitly asks.

## Baseline integrity checks

1. Record `git status --short --branch`.
2. Verify that the canonical JSONL hash and all manifest pins match the target above.
3. Run the full test suite.
4. Run the deterministic generator and confirm it creates no diff in the golden suite, manifest, scope YAML mirror, or generated review package.
5. Confirm 78 unique IDs, manifest `case_count=78`, no duplicate coverage tags, and no rendering/training fields.
6. Confirm all 13 approved decision IDs have at least one positive and one negative applicability case.

If generation changes the target, stop and report drift.

## Required remediation checks

### HGR-FIND-001 — severe complicated measles

Review `hpg-055-fever-severe-measles-cornea` directly against `IMCI-MSC-MEASLES-SEVERE-COMPLICATED` and its source provenance.

Confirm that all source-required immediate actions are present in both `urgent_actions` and the completed `final_actions`, and absent from `deferred_actions`:

- `GIVE_VITAMIN_A_TREATMENT`
- `GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC`
- `APPLY_TETRACYCLINE_EYE_OINTMENT`
- `URGENT_REFERRAL`

Then re-review every case with `urgent_action_required=true`. Verify that routine home-care courses and scheduled follow-up remain deferred where `IP-CQ-004` requires that behavior, while source-mandated pre-referral/transfer treatments are not suppressed.

### HGR-FIND-002 — exact review-decision applicability

Review `provenance.review_decision_ids` for every case. The IDs must be derived from the semantic condition actually exercised, not stamped across an assessment family.

At minimum verify these exact narrow sets:

- `MSC-CQ-RESP-001`: `hpg-020`, `hpg-021`, `hpg-022`
- `MSC-CQ-RESP-002`: `hpg-014`
- `MSC-CQ-DIARRHOEA-001`: `hpg-030`, `hpg-031`, `hpg-040`
- `MSC-CQ-FEVER-002`: `hpg-052`
- `MSC-CQ-EAR-001`: `hpg-065`
- `IP-CQ-002`: `hpg-037`, `hpg-038`, `hpg-075`
- `IP-CQ-004`: `hpg-016`, `hpg-034`, `hpg-055`, `hpg-069`, `hpg-070`, `hpg-076`

Also inspect the broader pathway-entry decisions and scope decision case by case. Do not infer correctness merely from union coverage or passing tests.

### HGR-FIND-003 — non-firing requirement and scope provenance

Review `provenance.requirement_citations` independently of fired-rule provenance.

Confirm that:

- fired rules remain only in `source_rule_ids` and `source_citations`;
- each missing field in an incomplete case is covered by an exact versioned completeness-policy clause;
- invalid evidence and contradiction cases cite the corresponding completion-blocking clause;
- `hpg-001` cites the explicit-negative pathway-exclusion semantics without pretending a clinical rule fired;
- `hpg-077` and `hpg-078` cite the versioned 2–59-month scope boundary;
- no citation claims a conditional requirement that is not active for that case.

### HGR-FIND-004 — coverage uniqueness

Confirm every case has unique coverage tags. In particular, `hpg-046-fever-no-risk` must contain `fever` only once and retain `no_malaria_risk`.

## Semantic-drift audit

Compare the previous reviewed hash with the remediation target using Git history or the superseded review evidence. The only intended clinical expected-output change is the immediate action tier for `hpg-055`. The only intended coverage change is deduplication in `hpg-046`. Changes across all records to version pins, exact decision provenance, and requirement provenance are intentional metadata/schema remediation.

Any other classification, completeness, urgent-state, action, missing-element, contradiction, or fired-rule change is a new finding and must be explained before a ready recommendation.

## Full case review

Repeat all dimensions from the original review protocol for all 78 rows:

- input and unknown semantics;
- scope and evidence validity;
- completeness and withholding;
- classifications;
- integrated urgent/intermediate/deferred/final actions;
- fired-rule and action traces;
- source provenance;
- review-decision applicability; and
- non-firing requirement/scope provenance.

Mechanical equality with the evaluator is necessary but not sufficient.

## Deliverables

Create a CSV with exactly these columns and one row per case:

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

Use the original review’s verdict taxonomy: `PASS_SOURCE_ALIGNED`, `DEFECT_CASE_SPEC`, `DEFECT_ORACLE_OR_SCHEMA`, `DEFECT_PROVENANCE`, or `NEEDS_HUMAN_CLINICAL_REVIEW`. Populate every dimension with `PASS`, `FAIL`, or `NEEDS_REVIEW`.

Create a Markdown report containing:

1. `REVIEW_RECORD` authority and `TECHNICAL_SOURCE_REVIEW_COMPLETE` or `TECHNICAL_SOURCE_REVIEW_BLOCKED` status;
2. the exact reviewed hash and pins;
3. baseline/final verification results;
4. 78-row verdict and severity totals;
5. a closure verdict for each `HGR-FIND-001` through `HGR-FIND-004`;
6. any new findings with exact affected IDs and provenance;
7. confirmation of the semantic-drift audit;
8. technical-review limitations; and
9. exactly one final recommendation: `READY_FOR_HUMAN_DOMAIN_APPROVAL` or `NOT_READY_FOR_HUMAN_DOMAIN_APPROVAL`.

`READY_FOR_HUMAN_DOMAIN_APPROVAL` means only that this coding-agent/source review found the remediated suite ready for the separate human/domain gate. It does not mean clinically approved, frozen, or eligible for generation/training.

## Completion criteria

The task is complete only when all 78 rows are reviewed, all four remediation findings have an explicit closure status, the full tests and deterministic regeneration pass, `git diff --check` passes, and only the two permitted re-review deliverables have been created.
