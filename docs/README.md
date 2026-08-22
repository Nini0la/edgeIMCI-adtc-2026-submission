# EdgeIMCI documentation authority index

> **Authority:** `DOCUMENT_CONTROL` · **Lifecycle:** `CURRENT` · **Canonicality:** Canonical index for the role and lifecycle of repository documentation.

This index prevents planning notes, historical experiments, review evidence, and approved policy from being treated as interchangeable. Authority describes what a document is allowed to decide; lifecycle describes whether it is current.

## Precedence and interpretation

1. The WHO IMCI source is the external clinical source. Human-approved review decisions resolve how the bounded hackathon representation handles recorded ambiguities.
2. Versioned canonical clinical and policy artifacts define what repository code executes. If an artifact conflicts with its clinical source or approved review decision, that is a defect requiring review—not permission to ignore the source.
3. Approved product-policy artifacts define EdgeIMCI interaction and scope choices but must not invent or override clinical logic.
4. Review and audit records explain, test, or approve artifacts; they do not silently modify them.
5. Implementation references describe schemas and software behavior.
6. Working plans guide future work and may change as evidence develops.
7. Exploratory notes contain hypotheses and options, not decisions.
8. Historical documents preserve reproducibility and must not control current product behavior.

When JSON and YAML represent the same artifact, the relationship is about editing and synchronization—not clinical authority. The designated canonical file is edited; the generated mirror is regenerated. In the current repository, canonical structured artifacts are JSON and their YAML files are generated mirrors.

## Authority vocabulary

| Label | Meaning |
|---|---|
| `NORMATIVE_CLINICAL_ARTIFACT` | Versioned machine-readable clinical or completeness logic used by deterministic code. |
| `APPROVED_DECISION_ARTIFACT` | Approved clinical-review or product-scope decision set. |
| `APPROVED_PRODUCT_POLICY` | Current product/interaction behavior that does not create clinical rules. |
| `REVIEW_RECORD` | Domain-review, source-map, crosscheck, audit, or golden-review evidence. |
| `IMPLEMENTATION_REFERENCE` | Schema, evaluator, or operational behavior documentation. |
| `WORKING_PLAN` | Current roadmap or experiment plan; revisable and non-clinical. |
| `EXPLORATORY_NOTES` | Hypotheses and options that are not approved decisions. |
| `REFERENCE` | Terminology or navigation aid. |
| `HISTORICAL_ARCHIVE` | Reproducibility record that is ineligible to govern current product work. |
| `DOCUMENT_CONTROL` | Repository documentation-governance metadata. |

Lifecycle values are `CURRENT`, `PROPOSED_FOR_REVIEW`, `SUPERSEDED`, and `ARCHIVED`.

## Canonical structured authority

| Canonical artifact | Generated mirror | Authority | Lifecycle |
|---|---|---|---|
| `data/rules/imci_major_sick_child_v1.json` | `.yaml` sibling | `NORMATIVE_CLINICAL_ARTIFACT` | `CURRENT` |
| `configs/information_policy/imci_major_sick_child_holistic_completeness_v2.json` | `.yaml` sibling | `NORMATIVE_CLINICAL_ARTIFACT` | `CURRENT` |
| `configs/information_policy/imci_major_sick_child_review_decisions_v1.json` | `.yaml` sibling | `APPROVED_DECISION_ARTIFACT` | `CURRENT` |
| `configs/golden/holistic_product_golden_scope_dispositions_v1.json` | `.yaml` sibling | `APPROVED_DECISION_ARTIFACT` | `CURRENT` |
| `data/golden/holistic_product_v1/semantic_cases.jsonl` | `semantic_cases.yaml` | `REVIEW_RECORD` | `PROPOSED_FOR_REVIEW` |
| `data/archive/selected_v0/archive_manifest.json` | none | `HISTORICAL_ARCHIVE` | `ARCHIVED` |

The proposed holistic golden suite does not become frozen product authority until domain review is complete and its lifecycle is changed explicitly.

## Markdown document register

| Document | Authority | Lifecycle | Relationship |
|---|---|---|---|
| `README.md` | `DOCUMENT_CONTROL` | `CURRENT` | This documentation index. |
| `glossary.md` | `REFERENCE` | `CURRENT` | Terminology aid only. |
| `clinical_questions.md` | `REVIEW_RECORD` | `CURRENT` | Question/disposition index; canonical answers live in approved decision artifacts. |
| `major_sick_child_expansion_map_v1.md` | `REVIEW_RECORD` | `CURRENT` | Source-derived engineering map; read with the approved decision set. |
| `major_sick_child_domain_review_v1.md` | `REVIEW_RECORD` | `CURRENT` | Hackathon-scope domain-review record. |
| `system_level_clinical_audit_v2.md` | `REVIEW_RECORD` | `CURRENT` | Current deterministic substrate audit. |
| `product_holistic_golden_suite_requirements_v1.md` | `APPROVED_PRODUCT_POLICY` | `CURRENT` | Approved construction/review contract for product semantics. |
| `product_holistic_golden_review_v1.md` | `REVIEW_RECORD` | `PROPOSED_FOR_REVIEW` | Generated domain-review surface; not frozen semantics. |
| `interaction_design_retrieval_assessment_bundles.md` | `APPROVED_PRODUCT_POLICY` | `CURRENT` | Current interaction framing; cannot override clinical artifacts. |
| `experiment_operations_and_tracking_plan.md` | `WORKING_PLAN` | `CURRENT` | Maintained Markdown working version; corresponding DOCX is its source snapshot. |
| `experimental_campaign_map.md` | `WORKING_PLAN` | `CURRENT` | Maintained Markdown working version; corresponding DOCX is its source snapshot. |
| `synthetic_data_generation_experiment_plan.md` | `WORKING_PLAN` | `CURRENT` | Maintained Markdown working version; corresponding DOCX is its source snapshot. |
| `synthetic_data_generation_experiment_notes.md` | `EXPLORATORY_NOTES` | `CURRENT` | Generation hypotheses and options; never a clinical or product decision. |
| `information_policy_proposal.md` | `REVIEW_RECORD` | `ARCHIVED` | Selected-v0 design record. |
| `information_policy_v1.md` | `IMPLEMENTATION_REFERENCE` | `ARCHIVED` | Selected-v0 deterministic policy reference. |
| `trajectory_schema.md` | `IMPLEMENTATION_REFERENCE` | `ARCHIVED` | Selected-v0 trajectory/reference-rendering schema. |
| `golden_slice_review_v1.md` | `HISTORICAL_ARCHIVE` | `ARCHIVED` | Selected-v0 14-case review package. |
| `rendering_contract_v1.md` | `HISTORICAL_ARCHIVE` | `ARCHIVED` | Selected-v0 rendering contract. |
| `rendering_bakeoff_review_v1.md` | `HISTORICAL_ARCHIVE` | `ARCHIVED` | Selected-v0 historical experiment review. |
| `system_level_clinical_audit_v0.md` | `HISTORICAL_ARCHIVE` | `ARCHIVED` | Selected-v0 audit. |
| `cases_crosscheck.md` | `HISTORICAL_ARCHIVE` | `ARCHIVED` | Selected-v0 case crosscheck. |
| `rules_crosscheck.md` | `HISTORICAL_ARCHIVE` | `ARCHIVED` | Selected-v0 rule crosscheck. |

## Non-Markdown companions

| Files | Role |
|---|---|
| `EdgeIMCI - Experiment Operations and Tracking Plan.docx` | Original user-authored/source snapshot for the maintained Markdown working plan. |
| `EdgeIMCI - Experimental Campaign Map.docx` | Original user-authored/source snapshot for the maintained Markdown working plan. |
| `EdgeIMCI - Synthetic Data Generation Experiment Plan.docx` | Original user-authored/source snapshot for the maintained Markdown working plan. |
| `cases_crosscheck.csv`, `rules_crosscheck.csv`, `rules_crosscheck.pdf` | Generated/companion selected-v0 historical review material. |

Changes to document authority, lifecycle, canonicality, or supersession must update this index in the same commit.
