# Instructions for the holistic golden semantic domain-review agent

> **Authority:** `WORKING_PLAN` · **Lifecycle:** `CURRENT` · Operational protocol for a source-backed technical review; it does not itself approve clinical semantics.

## Assignment

Perform a case-by-case, source-backed semantic audit of all 78 proposed records in `edge-imci-holistic-product-golden-v1`.

Your job is to determine whether each proposed record faithfully represents the currently approved, bounded EdgeIMCI hackathon substrate. You must independently inspect the structured input, completeness result, classifications, management actions, missing elements, rule/action traces, source provenance, and applicable review decisions.

Do not merely confirm that the committed expected output equals the deterministic evaluator. That mechanical equality is already tested. The review must determine whether the case specification and evaluator output agree with the canonical encoded rules, approved policy, and recorded review decisions.

This is a technical/source-backed review by a coding agent. It may produce `READY_FOR_HUMAN_DOMAIN_APPROVAL`, but it must not claim to be clinical-expert approval.

## Current checkpoint

- Branch: `main`.
- Proposed suite: 78 records.
- Complete cases: 60.
- Intentional incomplete cases: 16.
- Intentional schema rejections: 2.
- Corpus role: `HOLISTIC_PRODUCT_GOLDEN`.
- Lifecycle: `PROPOSED_FOR_DOMAIN_REVIEW`.
- Open construction gaps: none.
- Remaining freeze blocker: `DOMAIN_REVIEW_PENDING`.
- Current automated checkpoint: 246 passing tests before this review protocol was added.
- Bulk generation, language rendering, teacher selection, training, and product evaluation are not authorized by this task.

## Authority and required reading

Read these files completely before reviewing any case:

1. `docs/README.md` — documentation authority and lifecycle precedence.
2. `data/rules/imci_major_sick_child_v1.json` — canonical encoded clinical rules and provenance.
3. `configs/information_policy/imci_major_sick_child_holistic_completeness_v2.json` — canonical completeness and withholding policy.
4. `configs/information_policy/imci_major_sick_child_review_decisions_v1.json` — all 13 approved hackathon-scope decisions.
5. `configs/golden/holistic_product_golden_scope_dispositions_v1.json` — resolved product-scope disposition for later Plan B/C treatment execution.
6. `src/edge_imci/schemas/holistic.py` — whole-encounter schema and result invariants.
7. `src/edge_imci/evaluation/holistic.py` — deterministic integrated evaluator.
8. `docs/major_sick_child_expansion_map_v1.md` — source/provenance map.
9. `docs/major_sick_child_domain_review_v1.md` — existing bounded-scope review record.
10. `docs/product_holistic_golden_suite_requirements_v1.md` — suite requirements and review gates.
11. `data/golden/holistic_product_v1/manifest.json` — lifecycle, pins, hash, eligibility, and coverage.
12. `data/golden/holistic_product_v1/semantic_cases.jsonl` — canonical proposed cases.
13. `docs/product_holistic_golden_review_v1.md` — generated human-readable case surface.

The YAML files are generated mirrors. Use the canonical JSON/JSONL for comparisons and the YAML only as a reading aid.

If `data/sources/IMCI chartbooklet 2014.pdf` is present, use the cited pages to verify source wording where necessary. If it is absent, do not silently claim direct PDF verification. State that the review used the canonical encoded rule provenance and existing approved review records. Do not use general medical knowledge to fill gaps, and do not browse for replacement clinical rules unless the user separately authorizes it.

## Strict change boundary

This is a review-only pass.

You may create only:

- `docs/product_holistic_golden_domain_review_v1.md`
- `docs/product_holistic_golden_domain_review_v1.csv`

Do not modify during the review:

- clinical rule JSON or YAML;
- completeness-policy or review-decision artifacts;
- the HPG scope-disposition artifact;
- schemas or evaluator code;
- the 78 golden records, manifest, generator, or validator;
- lifecycle status, eligibility flags, hashes, or freeze blockers;
- historical selected-v0 material;
- language renderings, prompts, datasets, splits, or training artifacts.

Do not fix a defect in the same pass that discovers it. Record it with evidence so correction and re-review remain independent. Do not commit or push unless the user explicitly asks.

Preserve unrelated worktree changes and leave `.letta/` untouched.

## Baseline verification

Before reviewing cases:

1. Run `git status --short --branch` and record whether the worktree was clean apart from known unrelated files.
2. Run the full test suite:

   ```bash
   PYTHONPATH=src python3 -m pytest -q
   ```

3. Run the suite generator and confirm that it creates no semantic diff:

   ```bash
   PYTHONPATH=src python3 scripts/generate_holistic_golden_suite.py
   git diff -- data/golden/holistic_product_v1 configs/golden/holistic_product_golden_scope_dispositions_v1.yaml docs/product_holistic_golden_review_v1.md
   ```

4. Verify:

   - exactly 78 unique `golden_case_id` values;
   - manifest `case_count=78`;
   - the JSONL SHA-256 equals `semantic_cases_sha256` in the manifest;
   - every record pins the same rule set, completeness policy, review-decision set, scope-disposition set, oracle, validator, and schema version;
   - all 13 approved review-decision IDs appear across the suite;
   - every encoded `HolisticClassification` appears in at least one internal classification trace;
   - no record contains conversational rendering or training data.

If the generator changes canonical semantics before you have reviewed anything, stop and report repository drift. Do not review a moving target.

## Review all 78 cases

Review every record. Sampling is not sufficient.

Use these groups to organize the work:

| Cases | Review family |
|---|---|
| `hpg-001` | Complete all-negative encounter and explicit pathway exclusion. |
| `hpg-002`–`hpg-006` | General danger signs and urgent action behavior. |
| `hpg-007`–`hpg-026` | Respiratory thresholds, chest indrawing/HIV, stridor, oxygen saturation, wheeze, bronchodilator reassessment, invalid evidence, and conditional omissions. |
| `hpg-027`–`hpg-040` | Dehydration, Plan A/B/C, persistence, dysentery, cholera context, and one-way drinking-evidence reuse. |
| `hpg-041`–`hpg-060` | Fever, malaria risk/testing, temperature and duration boundaries, bacterial-cause action, measles, and missing context/results. |
| `hpg-061`–`hpg-067` | No/acute/chronic ear infection, mastoiditis, observed pus, duration boundaries, and omission behavior. |
| `hpg-068`–`hpg-076` | Multi-pathway integration, urgent action precedence, action deduplication/deferment, grouped omissions, internal withholding, and contradiction handling. |
| `hpg-077`–`hpg-078` | Out-of-scope age schema rejection. |

## Per-case review dimensions

For every case, explicitly assess all of the following.

### 1. Input and unknown semantics

- Are all supplied values represented accurately?
- Does every omitted value remain `null`/`UNKNOWN` rather than becoming negative?
- Are explicit negatives distinguished from omissions?
- Are pathway-entry values present when required?
- Are conditionally irrelevant pathway objects harmless and non-authorizing?
- Are acquisition/context distinctions preserved where represented, especially malaria-area risk versus patient findings?

### 2. Scope and evidence validity

- Is age within 2–59 months for evaluable cases?
- Are ages 1 and 60 rejected without clinical synthesis?
- Is respiratory rate used only when the child is calm and breaths were counted for one minute?
- Does invalid evidence block completion?
- Are contradictions identified and completion-blocking?

### 3. Completeness and withholding

- Does the case meet every always-required and applicable conditional requirement?
- Are missing fields grouped under the correct assessment?
- Is final synthesis authorized exactly when the supported encounter is complete?
- Do incomplete cases expose no final classifications or final actions?
- Can known urgent actions still surface when the encounter is incomplete?
- Does a known internal classification remain withheld when overall completion is false?

### 4. Classification semantics

- Are all applicable simultaneous classifications retained?
- Is priority/precedence correct within each pathway?
- Are threshold boundaries exact?
- Are bronchodilator cases classified from valid post-treatment findings when required?
- Is chest indrawing plus HIV exposure/infection still `PNEUMONIA`, without automatic severe reclassification?
- Are malaria result and obvious/identified fever cause treated as separate findings?
- Does observed ear pus override negative prior-discharge history only in the approved direction?

### 5. Integrated action semantics

- Does each classification produce the source-backed action set at the encoded abstraction?
- Are exact duplicate actions deduplicated without suppressing distinct indications or traces?
- When urgent referral exists, are urgent/pre-referral and transfer actions front-facing while routine courses and scheduled follow-up are deferred?
- Is an ordinary medication course never converted into a first dose unless an explicit source-backed rule requires it?
- Are Plan B/C initial actions and reassessment instructions emitted without pretending the reassessment occurred?
- Is the cholera action generic and local-protocol-based without invented drug details?
- Is the bacterial-fever antibiotic action generic without invented diagnosis, drug, dose, or regimen?

### 6. Trace and provenance

- Does every internal classification have the correct rule ID?
- Does every action trace identify the rule that added, modified, suppressed, or overrode it?
- Do `fired_rule_ids` match the classifications/actions actually present?
- Does every fired rule exist in the canonical rule artifact?
- Do source citations match that rule’s section and pages?
- Are the listed review-decision IDs genuinely applicable?
- Is the product-scope disposition used only for the Plan B/C longitudinal-execution boundary?

## High-risk invariants

Treat violations of these invariants as serious findings:

1. Unknown is never negative.
2. Incomplete encounters never expose final holistic classifications or final management synthesis.
3. Known urgent actions are not withheld merely because the encounter is incomplete.
4. Urgency does not make the assessment complete.
5. The remaining assessment is completed rapidly without delaying urgent referral or pre-referral treatment.
6. Routine actions are deferred during urgent referral unless explicitly required before or during transfer.
7. Positive inability-to-drink evidence may be reused for dehydration only in the approved one-way direction.
8. Respiratory classification uses valid calm, one-minute evidence and valid post-bronchodilator findings where required.
9. Malaria-area risk is supplied context, not inferred from geography or model knowledge.
10. Generic antibiotic instructions remain generic where the source/local adaptation does not specify a regimen.
11. Ear-discharge duration uses the 14-day boundary exactly, including the approved observed-pus/no-history case.
12. Out-of-scope ages receive no unsupported synthesis.
13. `HPG-GAP-REASSESS-001` remains resolved as product scope: initial Plan B/C semantics are required; longitudinal execution is not implemented.

## Verdict taxonomy

Assign exactly one primary verdict to every case:

| Verdict | Meaning |
|---|---|
| `PASS_SOURCE_ALIGNED` | No semantic, trace, provenance, or policy defect found within the approved substrate. |
| `DEFECT_CASE_SPEC` | The constructed input, coverage labels, expected record, or applicable-decision metadata is wrong while the underlying oracle/rules appear correct. |
| `DEFECT_ORACLE_OR_SCHEMA` | Evaluator/schema behavior conflicts with the canonical rules or approved decisions. |
| `DEFECT_PROVENANCE` | Rule/action trace or source citation is missing, mismatched, or misleading. |
| `NEEDS_HUMAN_CLINICAL_REVIEW` | The current approved substrate does not cleanly determine the answer or direct source interpretation is required. |

Do not use `PASS_SOURCE_ALIGNED` merely because tests pass.

For every non-pass verdict, assign severity:

| Severity | Meaning |
|---|---|
| `P0` | Could invert or suppress urgent/referral behavior or put an out-of-scope case through clinical synthesis. |
| `P1` | Incorrect classification, treatment/action, completeness, withholding, or major cross-pathway behavior. |
| `P2` | Incorrect trace, provenance, coverage metadata, or non-urgent boundary behavior. |
| `P3` | Review-package clarity or other non-semantic issue. |

## Required CSV deliverable

Create `docs/product_holistic_golden_domain_review_v1.csv` with exactly one row per case and these columns:

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

Use `PASS`/`FAIL`/`NEEDS_REVIEW` for each dimension column. `finding_ids` may contain semicolon-separated IDs. Do not leave a reviewed row’s dimension fields blank.

## Required Markdown deliverable

Create `docs/product_holistic_golden_domain_review_v1.md` with:

1. authority label: `REVIEW_RECORD`;
2. status: `TECHNICAL_SOURCE_REVIEW_COMPLETE` or `TECHNICAL_SOURCE_REVIEW_BLOCKED`;
3. exact artifact pins and reviewed JSONL hash;
4. source material actually available and consulted;
5. baseline and final test results;
6. verdict counts totaling 78;
7. severity counts;
8. coverage-family findings;
9. one section for every defect or human-review item;
10. confirmation that all 78 CSV rows were completed;
11. explicit limitations of a coding-agent review;
12. one final recommendation:
    - `READY_FOR_HUMAN_DOMAIN_APPROVAL`, or
    - `NOT_READY_FOR_HUMAN_DOMAIN_APPROVAL`.

The recommendation must not be `CLINICALLY_APPROVED`, `FROZEN`, or equivalent.

Each finding must include:

- finding ID (`HGR-FIND-###`);
- affected case IDs;
- severity and verdict category;
- observed behavior;
- expected behavior under the cited artifact/rule/decision;
- exact supporting rule IDs and source pages where available;
- whether the likely defect is in the case, oracle/schema, provenance, or approved substrate;
- the smallest recommended follow-up action;
- whether re-review is required after correction.

## Completion criteria

The review is complete only when:

- all required files were read;
- baseline integrity checks passed or drift was reported;
- all 78 cases have one CSV row and primary verdict;
- every review dimension is populated;
- every non-pass case has a finding or explicit human-review rationale;
- verdict counts equal 78;
- all classification/action/completeness/provenance families were reviewed;
- the full test suite was rerun;
- `git diff --check` passes;
- only the two permitted review deliverables were created;
- the final report clearly distinguishes technical source alignment from human clinical approval.

If a blocker prevents completion, stop, preserve partial review evidence, and report the exact blocker. Never resolve a clinical ambiguity using general knowledge or by weakening a golden expectation.
