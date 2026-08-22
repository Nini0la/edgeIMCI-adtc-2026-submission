# Clinical questions

This file records source-dependent questions that must not be resolved from general medical knowledge. The 13 questions that blocked the expanded major sick-child hackathon substrate were resolved on 2026-08-22 and are canonically recorded in `configs/information_policy/imci_major_sick_child_review_decisions_v1.json` (with a generated YAML mirror).

Each question must identify the proposed rule ID, source location, a faithful summary of the source wording, the exact ambiguity, the expert decision required, and the blocked implementation.

## Resolution status

All 13 expanded-scope questions are **approved for the bounded hackathon representation**: `IP-CQ-001` through `IP-CQ-004`, `MSC-CQ-SCOPE-001`, `MSC-CQ-RESP-001`, `MSC-CQ-RESP-002`, `MSC-CQ-DIARRHOEA-001`, `MSC-CQ-REASSESS-001`, `MSC-CQ-FEVER-001`, `MSC-CQ-FEVER-002`, `MSC-CQ-FEVER-003`, and `MSC-CQ-EAR-001`.

This approval does not authorize production clinical use. The question detail below is retained as the audit trail that led to the versioned decision set; its former “decision needed” and “blocked implementation” wording is historical and superseded by that decision set.

## Resolved expanded-scope review prompts

### MSC-CQ-SCOPE-001 — Initial encounter versus follow-up-visit algorithms

- **Proposed scope:** `imci-major-sick-child-v1`.
- **Source:** WHO chart booklet; initial/follow-up visit instruction on `source_pdf_page: 5`, printed page 1; acute-condition follow-up algorithms on `source_pdf_pages: 32–33`, printed pages 28–29 of 76.
- **Source wording, summarized:** Initial visits use the assessment chart; follow-up visits use condition-specific follow-up instructions and assess new problems through the assessment chart.
- **Exact ambiguity:** The requested “major sick-child encounter” can mean the initial holistic assessment only or a versioned family that also executes follow-up-visit algorithms. The current v2 schema models initial encounters and emits follow-up timing, but does not execute return-visit algorithms.
- **Decision needed:** Confirm initial-encounter-only scope for this version or require a separate follow-up encounter/state machine before approval.
- **Blocked implementation:** Claiming complete computational coverage of follow-up care.

### MSC-CQ-RESP-001 — Bronchodilator trial and reassessment state contract

- **Proposed rule ID:** `IMCI-MSC-RESP-WHEEZE-BRONCHODILATOR-REASSESS`
- **Source:** WHO *Integrated Management of Childhood Illness, Chart Booklet*, March 2014; “Cough or difficult breathing”; `source_pdf_page: 6`; `source_printed_page: 2 of 76`.
- **Source wording, summarized:** Wheeze with fast breathing or chest indrawing requires a rapid-acting inhaled bronchodilator trial up to three times 15–20 minutes apart, followed by another breath count and chest-indrawing assessment before classification.
- **Exact ambiguity:** The clinical sequence is clear, but the source does not define a machine state for partial trials, the number of administrations actually completed, failed delivery, or repeated post-treatment evidence validity.
- **Decision needed:** Approve or revise the provisional v2 representation of one completed trial marker plus valid post-trial respiratory rate and chest-indrawing observations.
- **Blocked implementation:** The staged evaluator is implemented for review, but product-level semantic approval and golden-case construction remain blocked.

### MSC-CQ-RESP-002 — HIV-dependent chest-indrawing pneumonia management

- **Proposed rule ID:** `IMCI-MSC-RESP-HIV-CHEST-INDRAWING`
- **Source:** WHO chart booklet; “Cough or difficult breathing”; `source_pdf_page: 6`; `source_printed_page: 2 of 76`.
- **Source wording, summarized:** For chest indrawing in an HIV-exposed or infected child, give the first dose of amoxicillin and refer.
- **Exact ambiguity:** The chart does not label the referral as urgent in this yellow row and does not explicitly state how this instruction combines with or replaces the ordinary five-day pneumonia action block.
- **Decision needed:** Confirm the provisional treatment modification, referral urgency, and whether routine pneumonia actions remain, are deferred, or are suppressed.
- **Blocked implementation:** Final integrated action-synthesis approval for this combination.

### MSC-CQ-DIARRHOEA-001 — Cholera antibiotic is locally specified

- **Proposed rule ID:** `IMCI-MSC-DIARRHOEA-CHOLERA-CONTEXT`
- **Source:** WHO chart booklet; “Diarrhoea — severe dehydration” and oral-antibiotic table; `source_pdf_pages: 7, 16`; `source_printed_pages: 3 and 12 of 76`.
- **Source wording, summarized:** A child aged 2 years or older with severe dehydration should receive a cholera antibiotic when cholera is present locally, but the first- and second-line choices are blank local-adaptation fields.
- **Exact ambiguity:** The generic source does not supply the authoritative local drug choices.
- **Decision needed:** Supply and version the deployment-specific cholera protocol or explicitly exclude drug-level cholera treatment.
- **Blocked implementation:** The evaluator emits only `GIVE_CHOLERA_ANTIBIOTIC_PER_LOCAL_PROTOCOL`; drug-specific synthesis is not approved.

### MSC-CQ-REASSESS-001 — Rehydration completion and repeated-plan semantics

- **Proposed rule IDs:** `IMCI-MSC-DIARRHOEA-PLAN-B-REASSESS`, `IMCI-MSC-DIARRHOEA-PLAN-C-REASSESS`
- **Source:** WHO chart booklet; Plans B and C; `source_pdf_pages: 23–24`; `source_printed_pages: 19–20 of 76`.
- **Source wording, summarized:** Plan B requires reassessment after four hours; Plan C has resource- and age-dependent treatment paths followed by reassessment and selection of Plan A, B, or C.
- **Exact ambiguity:** A single encounter representation can loop into another treatment plan, while Plan C also depends on facility capabilities. The source does not define where a software encounter should terminate or how repeated cycles should be serialized.
- **Decision needed:** Confirm or revise the provisional one-reassessment-stage contract and define the required facility-capability branches.
- **Blocked implementation:** Product-level approval of post-rehydration completeness and full Plan C execution.

### MSC-CQ-FEVER-001 — “Malaria test negative” versus “other cause present” condition

- **Proposed rule ID:** `IMCI-MSC-FEVER-NO-MALARIA`
- **Source:** WHO chart booklet; “Fever”; `source_pdf_page: 8`; `source_printed_page: 4 of 76`.
- **Source wording, summarized:** The green `FEVER: NO MALARIA` row lists a negative malaria test and another cause of fever present; low-risk testing is performed only when no obvious cause is present.
- **Exact ambiguity:** The visual row supports an OR-like operational reading, but does not formally define the Boolean relationship or the exact boundary of “obvious cause.”
- **Decision needed:** Confirm the Boolean condition and define the evidence contract for an obvious cause of fever.
- **Blocked implementation:** The provisional evaluator uses negative test **or** explicitly supplied obvious cause; domain approval is required.

### MSC-CQ-FEVER-002 — Identified bacterial cause treatment representation

- **Proposed rule ID:** `IMCI-MSC-FEVER-IDENTIFIED-BACTERIAL-CAUSE`
- **Source:** WHO chart booklet; “Fever” and footnote listing example local bacterial findings; `source_pdf_page: 8`; `source_printed_page: 4 of 76`.
- **Source wording, summarized:** Give appropriate antibiotic treatment for an identified bacterial cause of fever.
- **Exact ambiguity:** A Boolean “bacterial cause present” cannot select a specific appropriate treatment or safely reconcile it with antibiotics already selected by another supported pathway.
- **Decision needed:** Define the supported bacterial-cause vocabulary and its treatment/action interaction table.
- **Blocked implementation:** The evaluator emits a generic action and cannot be approved as a complete drug-level integrated oracle.

### MSC-CQ-FEVER-003 — Malaria-risk deployment configuration

- **Proposed rule IDs:** all `IMCI-MSC-FEVER-*` classification rules.
- **Source:** WHO chart booklet; “Fever”; `source_pdf_page: 8`; `source_printed_page: 4 of 76`.
- **Source wording, summarized:** The worker decides high or low malaria risk; a separate branch applies where there is no malaria risk and no travel to a risk area.
- **Exact ambiguity:** The generic chart does not define the geographic/epidemiologic mapping for a deployment, nor whether risk is encounter-entered or fixed by a versioned local adaptation.
- **Decision needed:** Supply the authoritative deployment-specific malaria-risk configuration and travel interpretation.
- **Blocked implementation:** Final approval of fever completeness and malaria actions for a real deployment.

### MSC-CQ-EAR-001 — Observed pus with explicitly denied discharge history

- **Proposed rule IDs:** `IMCI-MSC-EAR-ACUTE-INFECTION`, `IMCI-MSC-EAR-CHRONIC-INFECTION`, `IMCI-MSC-EAR-NO-INFECTION`.
- **Source:** WHO chart booklet; “Ear problem”; `source_pdf_page: 9`; `source_printed_page: 5 of 76`.
- **Source wording, summarized:** Acute and chronic infection rows combine pus seen with reported discharge duration; no infection requires no pain and no pus.
- **Exact ambiguity:** The chart does not explicitly classify the contradictory state where pus is seen but the caregiver denies discharge and there is no ear pain.
- **Decision needed:** Define whether this is treated as contradictory evidence requiring clarification or mapped to a classification.
- **Blocked implementation:** V2 currently blocks completion and reports this question ID.

### CQ-001 — Wheeze reassessment before respiratory classification

- **Proposed rule ID:** `IMCI-RESP-WHEEZE-REASSESS`
- **Source:** WHO *Integrated Management of Childhood Illness, Chart Booklet*, March 2014; “Cough or difficult breathing”; `source_pdf_page: 6`; `source_printed_page: 2 of 76`.
- **Source wording, summarized:** When wheeze occurs with either fast breathing or chest indrawing, the chart directs a trial of rapid-acting inhaled bronchodilator up to three times, followed by another breath count and chest-indrawing assessment before classification.
- **Exact ambiguity:** The source is clear about the clinical sequence but does not define how a static benchmark case should represent the repeated observations, an incomplete bronchodilator trial, or a setting where reassessment is unavailable.
- **Decision needed:** A domain expert must define the admissible pre-treatment/post-treatment observation states and when the benchmark should require reassessment rather than emit a respiratory classification.
- **Blocked implementation:** Wheezing cases and bronchodilator-response rules are excluded from `imci-selected-v0`. Respiratory cases in this version do not assert wheeze.

## Separate legacy selected-scope question

`CQ-001` belongs to the frozen `imci-selected-v0` boundary. The expanded substrate resolves its practical bronchodilator representation through `MSC-CQ-RESP-001`; the frozen v0 artifact itself remains unchanged.
