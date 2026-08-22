# Product-level holistic golden semantic suite v1 — independent technical/source re-review

> **Authority:** `REVIEW_RECORD` · **Lifecycle:** `SUPERSEDED` · Independent coding-agent technical/source review of corpus hash `bba39ee0...`; retained as the finding record that triggered respiratory remediation.

**Review status:** `TECHNICAL_SOURCE_REVIEW_COMPLETE`

**Final recommendation:** `NOT_READY_FOR_HUMAN_DOMAIN_APPROVAL`

**Suite reviewed:** `edge-imci-holistic-product-golden-v1`

**Semantic corpus SHA-256:** `bba39ee0a06e9630d90996dd01e931807bf1e50f861e040355c6de165e40e8a9`

**Review date:** 2026-08-22

**Companion verdict matrix:** [`product_holistic_golden_domain_re_review_v1.csv`](product_holistic_golden_domain_re_review_v1.csv)

## 1. Scope and authority

This review independently re-read all 78 semantic records and checked input facts, UNKNOWN handling, supported-scope validity, completeness and withholding, internal and final classifications, urgent/intermediate/deferred/final actions, rule and action traces, source and requirement provenance, and applicable review decisions.

The controlling sources were:

- `data/sources/IMCI chartbooklet 2014.pdf`;
- `data/rules/imci_major_sick_child_v1.json`;
- `configs/information_policy/imci_major_sick_child_holistic_completeness_v2.json`;
- `configs/information_policy/imci_major_sick_child_review_decisions_v1.json`;
- `configs/golden/holistic_product_golden_scope_dispositions_v1.json`;
- the holistic schema, deterministic evaluator, generator, manifest, generated review package, requirements, and focused tests.

This record can establish technical/source review completion and identify defects. It cannot grant human/domain clinical approval, freeze the corpus, authorize production clinical use, or make the suite eligible for generation, teacher selection, product evaluation, or training.

## 2. Result

| Result | Count |
| --- | ---: |
| Cases reviewed | 78 |
| `PASS_SOURCE_ALIGNED` | 62 |
| `DEFECT_ORACLE_OR_SCHEMA` | 16 |
| P1 case verdicts | 4 |
| P2 case verdicts | 12 |
| Open findings | 3 |

The current suite is **not ready** for the separate human/domain approval gate. One action-timing policy/source gap and two respiratory evaluator/trace defects remain. The corpus must stay `PROPOSED_FOR_DOMAIN_REVIEW`; its existing `DOMAIN_REVIEW_PENDING` freeze blocker must not be cleared.

## 3. Re-review of the four prior findings

| Prior finding | Re-review disposition | Evidence |
| --- | --- | --- |
| `HGR-FIND-001` — severe complicated measles immediate actions | `CLOSED` | `hpg-055-fever-severe-measles-cornea` now keeps Vitamin A, the first antibiotic dose, conditional tetracycline eye ointment, and urgent referral in both `urgent_actions` and `final_actions`; none is deferred. Focused evaluator and suite regression tests cover the contract. |
| `HGR-FIND-002` — over-inclusive or missing `review_decision_ids` | `CLOSED` | All 13 approved decisions have explicit positive and negative applicability. The exact 13-decision case matrix passes; no decision is globally attached. The 49 changed mappings match the current case semantics. |
| `HGR-FIND-003` — missing provenance for non-firing completeness/scope behavior | `CLOSED` | Record schema v2 adds typed `requirement_citations`. Every missing field is covered by an exact completeness requirement; contradictions cite evidence-validity policy; both schema rejections cite the supported age boundary; the all-negative case cites explicit-negative pathway exclusion. |
| `HGR-FIND-004` — duplicate coverage metadata | `CLOSED` | `hpg-046-fever-no-risk` no longer repeats `fever`; all 78 records have unique per-case coverage tags and the manifest tag set equals the corpus union. |

No unrelated input facts, case intent, or expected clinical result changed during remediation. Relative to the pre-remediation corpus, the only expected-result change is the intended severe-measles urgent-action correction in `hpg-055`; the only coverage change is removal of the duplicate tag in `hpg-046`. Remaining changes are schema/version pins and provenance metadata.

## 4. Open findings

### HGRR-FIND-001 — sub-90% oxygen referral is promoted to an urgent workflow without an approved disposition

- **Severity:** P1
- **Affected case:** `hpg-016-resp-oximeter-89-9`
- **Primary owner:** domain/policy review, then evaluator implementation
- **Failed dimensions:** action semantics; source/policy provenance

The WHO respiratory footnote says to determine oxygen saturation when pulse oximetry is available and to **refer if `< 90%`**. It does not label that referral `URGENTLY`, unlike the severe-pneumonia row. The canonical rule is correspondingly typed `conditional_referral`. The expansion map explicitly records that the product urgency presentation requires review.

`src/edge_imci/evaluation/holistic.py` nevertheless adds `REFER_FOR_OXYGEN_SATURATION_BELOW_90` with `urgent=True`. The generated case therefore sets `urgent_action_required=true`, applies `IP-CQ-004`, defers cough/cold home-care actions, and exposes only the referral in `final_actions`. `IP-CQ-004` governs filtering **after an urgent referral is triggered**; it does not independently establish that this conditional referral is urgent.

**Required remediation:** obtain and version an explicit human/domain or product-policy disposition for the sub-90% referral presentation. If it is urgent, pin that authority and test the immediate/deferred action contract. If it is not urgent, remove the urgent flag, restore the applicable routine actions, remove inapplicable `IP-CQ-004` provenance, regenerate the suite, and re-review the case. Do not resolve this by undocumented clinical inference.

### HGRR-FIND-002 — fast-breathing threshold rules are recorded as fired when their conditions are false

- **Severity:** P2
- **Affected cases:** `hpg-007`, `hpg-010`, `hpg-013` through `hpg-019`, `hpg-023` through `hpg-026`, `hpg-070`, and `hpg-076`
- **Primary owner:** evaluator and golden generator
- **Failed dimension:** exact rule trace/source provenance

`_evaluate_respiratory` calls `state.fire()` for the age-specific fast-breathing rule whenever age and respiratory rate are present. It does not require `_fast_breathing(...) is True`. The resulting `fired_rule_ids`, `source_rule_ids`, and source citations claim that a positive threshold rule fired for below-threshold rates such as age 2/rate 49 and age 12+/rate 35 or 39.

The classifications in these cases are generally correct, but the trace is not. A fired-rule field cannot double as an evaluated-rule field.

**Required remediation:** record the age-specific fast-breathing rule as fired only when the threshold condition is true and the measurement is source-valid. If evaluated-but-false rules are needed for audit, represent them in a separately named typed field. Add negative-boundary and invalid-measurement regression tests, regenerate every artifact, and re-review all 15 linked rows.

### HGRR-FIND-003 — respiratory classification proceeds before required source-valid evidence exists

- **Severity:** P1
- **Affected cases:** `hpg-022-resp-trial-outstanding`, `hpg-023-resp-child-not-calm`, `hpg-024-resp-count-not-one-minute`
- **Primary owner:** evaluator and focused tests
- **Failed dimensions:** internal classification; exact rule trace

The final holistic synthesis is correctly withheld in all three cases, but the internal classifications and traces are not source-aligned:

- `hpg-022` emits internal `PNEUMONIA` and fires `IMCI-MSC-RESP-PNEUMONIA-FAST-BREATHING` while the required bronchodilator trial and post-treatment reassessment are still missing. The source sequence and `MSC-CQ-RESP-001` require classification after valid reassessment.
- `hpg-023` and `hpg-024` emit internal `COUGH_OR_COLD` even though the child was not calm or breaths were not counted for one full minute. `IP-CQ-003` explicitly says invalid respiratory-rate evidence must not be used for classification.

An audit-only/internal label is still a classification and has no provisional or invalid marker in the current schema.

**Required remediation:** gate respiratory classification and classification-rule firing on source-valid evidence. When a bronchodilator trial is required but incomplete, emit the intervention and grouped missing evidence without a respiratory classification. When the rate is invalid and no independently sufficient severe/chest-indrawing condition determines the row, emit no respiratory classification. Add focused regression tests, regenerate, and re-review these three cases.

## 5. Evidence that passed

- All 78 IDs are unique and ordered from `hpg-001` through `hpg-078`.
- The corpus contains 60 complete evaluations, 16 incomplete evaluations, and 2 schema rejections.
- Every record exactly validates/recomputes against the current deterministic oracle; canonical JSONL and YAML mirror are equal.
- The manifest case count and semantic SHA-256 match the canonical JSONL.
- The suite remains ineligible for `HOLISTIC_GENERATION`, `PRODUCT_EVALUATION`, `TEACHER_BAKEOFF`, and `TRAINING`.
- Explicit negatives remain distinct from omissions; incomplete encounters expose no final classifications or final action synthesis; known urgent actions remain available through `urgent_actions`.
- Plan B/Plan C initial actions and timed reassessment follow the approved v1 product-scope disposition without introducing longitudinal treatment state.
- All 13 approved review decisions are represented with exact case applicability.
- Every missing element, contradiction, and out-of-scope age rejection has typed requirement or scope provenance.
- Severe complicated measles immediate-treatment behavior is repaired.
- Deterministic regeneration reproduced all generated artifacts byte-for-byte.
- Baseline full project verification completed with `282 passed`.

Passing mechanical tests do not override the three source/semantic findings above; the current tests encode the affected expected behavior.

## 6. Recommended remediation and re-review order

1. Obtain a versioned human/domain or product-policy decision for the `<90%` oxygen-referral urgency/presentation boundary.
2. Fix `_evaluate_respiratory` so false threshold rules never enter `fired_rule_ids` or source provenance.
3. Gate respiratory classification on valid calm/one-minute evidence and completed post-bronchodilator reassessment when required.
4. Add focused behavioral tests for the three findings.
5. Regenerate JSONL, YAML, manifest, scope mirror, and generated review package deterministically; verify that only intended records and pins change.
6. Re-review every changed row plus all urgent/incomplete and threshold-neighbor cases.
7. Only after all technical/source findings close should an independent human/domain reviewer decide approval. Only that later approval may authorize a controlled freeze.

Until then: do not freeze the suite, generate language renderings, run teacher bake-offs, create bulk synthetic data or splits, train, or use these records for product evaluation.
