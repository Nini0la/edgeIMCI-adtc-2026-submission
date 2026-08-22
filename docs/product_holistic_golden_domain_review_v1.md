# EdgeIMCI holistic product golden semantic suite v1 — technical source review

**Authority:** `REVIEW_RECORD`
**Lifecycle:** `SUPERSEDED`
**Review status:** `TECHNICAL_SOURCE_REVIEW_COMPLETE`
**Final recommendation:** `NOT_READY_FOR_HUMAN_DOMAIN_APPROVAL`
**Suite reviewed:** `edge-imci-holistic-product-golden-v1`
**Semantic corpus SHA-256:** `6cc773cf467e69135ad29e6018b894b749c8689122e6c92d585ce5bffd3df8b9`
**Review date:** 2026-08-22

## 1. Disposition

The case-by-case technical/source review is complete for all 78 proposed records at the pinned pre-remediation corpus hash above. This record has been superseded by remediation work and remains the historical finding record until an independent re-review is completed. It does **not** grant human clinical approval, production clinical authorization, corpus freeze, teacher selection, prompt bake-off, bulk generation, training, or product-evaluation eligibility.

The suite is **not ready to freeze**. One P1 oracle/withholding defect changes the immediate management target for severe complicated measles. Three additional findings affect review-decision provenance, non-firing requirement provenance, and one duplicated coverage tag. The clinical input/classification expectations otherwise align with the bounded approved substrate in this review.

Primary verdict totals:

| Primary verdict | Count |
|---|---:|
| `PASS_SOURCE_ALIGNED` | 33 |
| `DEFECT_CASE_SPEC` | 44 |
| `DEFECT_ORACLE_OR_SCHEMA` | 1 |
| `NEEDS_HUMAN_CLINICAL_REVIEW` | 0 |
| **Total** | **78** |

Severity totals:

| Severity | Count |
|---|---:|
| P0 | 0 |
| P1 | 1 |
| P2 | 44 |
| P3 | 0 as a primary row severity; `HGR-FIND-004` is a P3 secondary finding on a P2 row |
| None | 33 |

Per-dimension totals:

| Review dimension | Pass | Fail |
|---|---:|---:|
| Input fields and unknown semantics | 78 | 0 |
| Scope validity | 77 | 1 |
| Completeness and withholding | 77 | 1 |
| Classifications | 78 | 0 |
| Actions | 77 | 1 |
| Trace and provenance | 33 | 45 |
| Review-decision applicability | 39 | 39 |

The authoritative per-case results are in `docs/product_holistic_golden_domain_review_v1.csv`. Every proposed `golden_case_id` has exactly one row and every non-pass row names at least one finding below.

## 2. Review basis and method

The review used the documented precedence order:

1. WHO *Integrated Management of Childhood Illness, Chart Booklet*, March 2014 (`data/sources/IMCI chartbooklet 2014.pdf`), especially the major sick-child assessment/classification charts on source PDF pages 5–9 and the corresponding treatment instructions.
2. `configs/information_policy/imci_major_sick_child_review_decisions_v1.json` for the 13 approved bounded-representation decisions.
3. `data/rules/imci_major_sick_child_v1.json`, `configs/information_policy/imci_major_sick_child_holistic_completeness_v2.json`, and `configs/golden/holistic_product_golden_scope_dispositions_v1.json` for the current canonical execution, completeness, withholding, and Plan B/C scope contracts.
4. `src/edge_imci/schemas/holistic.py` and `src/edge_imci/evaluation/holistic.py` for schema/oracle behavior.
5. `data/golden/holistic_product_v1/semantic_cases.jsonl`, its generated YAML mirror, manifest, and `docs/product_holistic_golden_review_v1.md` for the proposed review surface.

For each row, the review independently checked supplied versus omitted facts, explicit negatives versus unknowns, pathway applicability, age bounds, respiratory validity, classification boundaries, simultaneous classifications, urgent/intermediate/deferred/final action behavior, grouped missing elements, contradictions, action traces, fired rules, source citations, approved decision applicability, and scope dispositions. Deterministic recomputation was used only as an integrity cross-check; equality with the evaluator was not treated as source approval.

Pinned identities reviewed:

- rule set: `imci-major-sick-child-v1`
- completeness policy: `imci-major-sick-child-holistic-completeness-v2`
- review decision set: `imci-major-sick-child-review-decisions-v1`
- scope disposition set: `edge-imci-holistic-golden-scope-dispositions-v1`
- holistic schema: `edge-imci-major-sick-child-encounter-v1`
- deterministic oracle: `edge-imci-holistic-deterministic-oracle-v1`
- validator: `edge-imci-holistic-golden-validator-v1`
- generator: `edge-imci-holistic-golden-generator-v1`
- seed: `20260822`

## 3. Coverage reviewed

The manifest and semantic records contain 78 unique cases: 60 complete encounters, 16 intentional incomplete encounters, and 2 intentional schema rejections. The review covered all 21 `HolisticClassification` enum values used by the approved evaluator, all five supported assessment areas, all 40 canonical clinical rules represented by the suite, and every emitted urgent, intermediate, deferred, and final action family.

| Area | Cases | Source/policy checks | Result |
|---|---|---|---|
| Low-severity whole encounter | `hpg-001` | Explicit negatives, no invented pathways, authorized empty synthesis | Semantics pass; requirement-citation finding |
| General danger signs | `hpg-002`–`hpg-006` | Each danger sign, immediate urgency, convulsing-now action, positive drinking reuse | Source/policy aligned |
| Respiratory | `hpg-007`–`hpg-026` | 2/12/60-month bounds, 50/40 thresholds, calm/one-minute validity, chest indrawing/HIV modifier, stridor, pulse oximetry, prolonged cough, recurrent wheeze, bronchodilator reassessment, incomplete conditions | Clinical expectations aligned; decision-provenance defects on five rows |
| Diarrhoea | `hpg-027`–`hpg-040` | Dehydration sign counts, Plan A/B/C, age-gated cholera context, 14-day persistence, dysentery, positive/negative drinking reuse, incomplete duration/context | Clinical expectations aligned; decision-provenance defects on nine rows |
| Fever and measles | `hpg-041`–`hpg-060` | Malaria risk/test routes, obvious and identified causes, 37.5/38.5 temperature behavior, >7-day fever, measles and complications, simultaneous classifications, missing context/test result | One P1 action-withholding defect; systematic decision provenance; two requirement-citation gaps |
| Ear problem | `hpg-061`–`hpg-067` | No infection, pain/pus acute infection, 13/14-day boundary, observed-pus negative history, mastoiditis, missing duration | Clinical expectations aligned; decision provenance and one requirement-citation gap |
| Whole-encounter integration | `hpg-068`–`hpg-076` | All pathways, cross-pathway urgency, action deduplication with trace retention, grouped omissions, urgent-incomplete behavior, internal withholding, contradictions | Clinical expectations aligned; decision/requirement provenance defects on two rows |
| Scope rejection | `hpg-077`–`hpg-078` | Lower and upper age exclusions (`2 <= age_months < 60`) | Rejections correct; scope-requirement citation gap |

The Plan B/C disposition was applied as approved: the suite emits initial dehydration classification and management plus a timed reassessment instruction, but it does not execute longitudinal treatment state, infer reassessment findings, or automatically repeat a plan. Those excluded behaviors remain outside v1.

## 4. Findings

### HGR-FIND-001 — P1 — severe-complicated-measles treatment is incorrectly deferred

**Verdict class:** `DEFECT_ORACLE_OR_SCHEMA`
**Affected case:** `hpg-055-fever-severe-measles-cornea`
**Owner:** holistic evaluator/oracle owner, followed by human clinical/domain reviewer

The source-backed severe-complicated-measles rule lists `GIVE_VITAMIN_A_TREATMENT`, `GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC`, `URGENT_REFERRAL`, and the indicated corneal/eye treatment. The canonical rule preserves those obligations in `data/rules/imci_major_sick_child_v1.json` under `IMCI-MSC-MEASLES-SEVERE-COMPLICATED`.

The evaluator records Vitamin A and tetracycline eye ointment as ordinary actions, then its global urgent filter keeps only `state.urgent` plus the single allowlisted dehydration intermediate action. In the committed expectation for `hpg-055`, Vitamin A and tetracycline eye ointment therefore appear in `deferred_actions` and are absent from `final_actions`, despite the same source classification requiring them alongside urgent referral. This is not a mere golden-row transcription issue: deterministic regeneration reproduces the evaluator defect.

**Risk:** a trained or evaluated response could learn to omit or postpone source-mandated severe-measles treatment in the immediate referral workflow.

**Required correction:** classify the severe-measles Vitamin A action and indicated eye treatment as source-mandated immediate/pre-referral actions for this classification, or replace the global action-tier model with an equally explicit source-backed mechanism. Regenerate the suite and re-review every urgent case after the oracle change. Do not weaken `IP-CQ-004`; routine home care and scheduled follow-up must still be deferred.

### HGR-FIND-002 — P2 — `review_decision_ids` are generated by broad case families, not exact applicability

**Verdict class:** `DEFECT_CASE_SPEC`
**Affected rows:** 39
**Owner:** golden generator/review-package owner

The records attach decision IDs too broadly and, in several action-deferral cases, omit the decision that actually controls the expected result.

Evidence:

- `MSC-CQ-FEVER-002` is attached to every complete fever case `hpg-041`–`hpg-058`, although the decision is specifically about a supplied identified bacterial cause; only `hpg-052` exercises that condition. The affected set for this over-attachment is `hpg-041`–`hpg-051` and `hpg-053`–`hpg-058`.
- `MSC-CQ-DIARRHOEA-001` and/or `MSC-CQ-REASSESS-001` are attached where neither the age-gated cholera branch nor Plan B/C reassessment governs the case: `hpg-027`–`hpg-029`, `hpg-032`–`hpg-036`, and `hpg-039`.
- `MSC-CQ-RESP-001` is attached to non-bronchodilator incomplete cases `hpg-023`–`hpg-026`.
- `MSC-CQ-EAR-001` is attached across the ear family rather than only where observed-pus/negative-history semantics govern the result: `hpg-061`–`hpg-064` and `hpg-066`–`hpg-067` are affected; `hpg-065` is the direct decision case.
- `IP-CQ-004` is missing from deferral cases `hpg-016`, `hpg-034`, and `hpg-055`, but is attached to non-urgent `hpg-068`.
- `IP-CQ-001` is attached to `hpg-072`, which has an unknown danger-sign field but no detected danger sign.

Exact affected IDs are the rows carrying `HGR-FIND-002` in the CSV.

**Risk:** a reviewer cannot tell which approved decision genuinely determines a case. Broad tagging can mask missing decision coverage and falsely imply that a decision was exercised.

**Required correction:** make decision applicability an explicit per-case derivation from the actual semantic factor and expected behavior. Add generator tests that assert positive and negative applicability for each of the 13 decision IDs; do not satisfy coverage by family-wide stamping.

### HGR-FIND-003 — P2 — non-firing requirements and scope boundaries lack exact provenance

**Verdict class:** `DEFECT_CASE_SPEC`
**Affected cases:** `hpg-001`, `hpg-059`, `hpg-060`, `hpg-067`, `hpg-071`, `hpg-072`, `hpg-077`, `hpg-078`
**Owner:** golden schema/generator owner

These cases have correct expected semantics, but `source_citations` and `source_rule_ids` are empty where the reviewed claim is precisely that a source-required assessment/context field is absent or that an input is outside the supported age scope. The current provenance shape primarily describes fired rules. A non-firing requirement therefore has no exact requirement-level citation.

Examples include missing malaria-risk context (`hpg-059`), missing available-test result (`hpg-060`), missing reported-discharge duration (`hpg-067`), missing pathway-entry facts (`hpg-071`/`hpg-072`), the all-explicit-negative assessment (`hpg-001`), and the two age boundaries (`hpg-077`/`hpg-078`). `hpg-038` is not included: its behavior is a decision-only cross-evidence rule and is explicitly supported by `IP-CQ-002`.

**Risk:** a future reviewer can verify what fired but not why a missing field blocks completion or why a scope rejection is authoritative.

**Required correction:** add a distinct requirement/scope provenance field rather than pretending a rule fired. It should pin the source section or approved schema/policy clause that makes the field required or defines the age bound. Populate it for all negative, incomplete, contradiction, and schema-rejection cases as applicable.

### HGR-FIND-004 — P3 — duplicated coverage tag

**Verdict class:** `DEFECT_CASE_SPEC`
**Affected case:** `hpg-046-fever-no-risk`
**Owner:** golden generator owner

`hpg-046` contains `fever` twice in its `coverage` array. The expected clinical result is correct, but coverage metadata must be normalized before freeze because manifest coverage is derived from these values.

**Required correction:** deduplicate coverage tags during case construction and assert per-case uniqueness in the generator/validator.

## 5. What passed

Subject to the findings above, the review found no case-specific defect in:

- the supported age interval and 2/12/60-month respiratory boundaries;
- explicit-negative versus unknown semantics;
- all five general danger signs and known urgent/incomplete behavior;
- calm and one-minute respiratory-rate validity;
- chest-indrawing/HIV modifier handling, stridor, pulse-oximetry threshold, prolonged cough, recurrent wheeze, and bronchodilator reassessment;
- dehydration sign counting, Plan A/B/C selection, the age-gated cholera context, persistence and dysentery combinations, and drinking-evidence reuse/contradiction behavior;
- malaria risk/test routes, separate obvious and identified fever causes, fever duration, high-temperature action boundary, measles classification, and simultaneous malaria/measles behavior;
- ear 13/14-day duration boundaries, observed-pus/negative-history behavior, and mastoiditis classification;
- simultaneous whole-encounter classifications, action-trace retention, action deduplication, grouped missing elements, withholding of final synthesis for incomplete encounters, and preservation of known urgent actions;
- lower/upper age schema rejection behavior.

`PASS_SOURCE_ALIGNED` here means no defect was found in the bounded technical/source review. It does not mean clinical-expert approval or production fitness.

## 6. Integrity evidence

Observed during baseline and final verification:

- final full repository suite in the project environment: `272 passed` (the initial pre-review baseline was `246 passed` before unrelated experiment-registry tests appeared in the working tree);
- deterministic golden generator completed with `wrote 78 holistic semantic cases`;
- regeneration produced no semantic diff in the canonical JSONL, generated YAML mirror, manifest, scope-disposition mirror, or generated review package;
- 78 case IDs are unique and match the manifest count;
- the manifest pins the rule set, completeness policy, decision set, scope disposition, schema, oracle, validator, generator, and seed listed above;
- all 13 approved decision IDs and all 21 classification enum values occur somewhere in the suite;
- no forbidden rendering/training keys occur in the semantic records;
- the manifest remains `PROPOSED_FOR_DOMAIN_REVIEW`, with `DOMAIN_REVIEW_PENDING`, `HOLISTIC_GENERATION: false`, `PRODUCT_EVALUATION: false`, `TEACHER_BAKEOFF: false`, and `TRAINING: false`.

These checks establish mechanical integrity only. They do not negate the findings.

## 7. Required next actions

1. Fix `HGR-FIND-001` in the evaluator/oracle and add a focused regression covering severe complicated measles with corneal involvement under urgent referral.
2. Regenerate the canonical suite and all generated mirrors; verify no unrelated semantic drift.
3. Fix decision applicability generation under `HGR-FIND-002` and add positive/negative applicability tests for every approved decision.
4. Add requirement/scope provenance under `HGR-FIND-003`; do not overload fired-rule provenance.
5. Deduplicate coverage metadata and validate uniqueness under `HGR-FIND-004`.
6. Repeat this technical/source review for every changed row and every urgent-action case affected by the oracle correction.
7. Only after technical findings are closed, obtain the independent human/domain review required by `DOMAIN_REVIEW_PENDING`. That reviewer, not this record, decides whether the suite is ready for a controlled freeze.

Until those steps are complete, bulk generation, teacher selection, training, product evaluation, and freeze remain unauthorized.

**Final recommendation:** `NOT_READY_FOR_HUMAN_DOMAIN_APPROVAL`
