# Major sick-child clinical model v1 — domain-expert review package

> **Authority:** `REVIEW_RECORD` · **Lifecycle:** `CURRENT` · Hackathon-scope review evidence; canonical decisions live in the approved decision artifact.

**Review status:** The 13 recorded decisions were approved for the bounded hackathon representation on 2026-08-22. Do not use this package as production clinical guidance.

**Artifact under review:** `imci-major-sick-child-v1` with completeness policy `imci-major-sick-child-holistic-completeness-v2`.

**Scope:** children aged 2 completed months to under 5 years; general danger signs, cough/difficult breathing, diarrhoea, fever including measles, and ear problem.

**Provenance statement:** This is a **machine-readable clinical rule set derived from the WHO IMCI Chart Booklet**, not WHO-authored “IMCI Rules.”

## Approved review boundary

The canonical resolution record is `configs/information_policy/imci_major_sick_child_review_decisions_v1.json`. This package remains the source-oriented review view; the decision record controls where its earlier prompts differ.

## General danger signs

| Clinical finding | Representation | Classification | Actions | Source |
| --- | --- | --- | --- | --- |
| Unable to drink/breastfeed; vomits everything; convulsions during illness; lethargic/unconscious; convulsing now | Five separate tri-state observations | Any positive → `VERY_SEVERE_DISEASE` | Complete assessment quickly, immediate pre-referral treatment, prevent low blood sugar, keep warm, urgent referral; diazepam when convulsing now | PDF 5 / printed 1 |

**Approved:** Early urgent actions are emitted immediately; the remaining supported assessment is completed rapidly, and routine work must not delay referral (`IP-CQ-001`).

## Cough or difficult breathing

| Clinical condition | Computational representation | Classification/action | Source |
| --- | --- | --- | --- |
| Age-specific fast breathing | ≥50 at 2–11 months; ≥40 at 12–59 months | Derived `FAST_BREATHING` | PDF 6 / printed 2 |
| Wheeze plus fast breathing/chest indrawing | Bronchodilator intervention followed by post-treatment rate/chest evidence | Classification withheld until reassessment | PDF 6 / printed 2 |
| Danger sign or calm stridor | Highest-severity row | `SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE`; antibiotic and urgent referral | PDF 6 / printed 2 |
| Chest indrawing or fast breathing | Next row after any required reassessment | `PNEUMONIA`; five-day amoxicillin and home/follow-up actions | PDF 6 / printed 2 |
| No severe/pneumonia signs | Complete-assessment fallback | `COUGH_OR_COLD` | PDF 6 / printed 2 |
| Wheeze, prolonged cough/recurrent wheeze, saturation <90%, HIV with chest indrawing | Conditional action dependencies | Bronchodilator; TB/asthma referral; saturation referral; modified HIV management | PDF 6 / printed 2 |

**Approved decisions:** `MSC-CQ-RESP-001`, `MSC-CQ-RESP-002`, and `IP-CQ-003` are fixed by the versioned review-decision set.

## Diarrhoea

| Clinical condition | Computational representation | Classification/action | Source |
| --- | --- | --- | --- |
| Two severe dehydration signs | Four-sign count including lethargy | `SEVERE_DEHYDRATION`; Plan C or severe-classification referral branch | PDF 7 / printed 3 |
| Two some-dehydration signs | Four-sign count | `SOME_DEHYDRATION`; Plan B or severe-classification referral branch | PDF 7 / printed 3 |
| Insufficient signs after complete assessment | Fallback | `NO_DEHYDRATION`; Plan A | PDF 7 / printed 3 |
| Duration ≥14 days plus dehydration | Duration and dehydration cross-result | `SEVERE_PERSISTENT_DIARRHOEA`; treat dehydration unless another severe, then refer | PDF 7 / printed 3 |
| Duration ≥14 days without dehydration | Same | `PERSISTENT_DIARRHOEA`; feeding/micronutrients/follow-up | PDF 7 / printed 3 |
| Blood in stool | Independent Boolean | `DYSENTERY`; ciprofloxacin/follow-up | PDF 7 / printed 3 |
| Plan B or C selected | Initial plan plus a separate later treatment-stage reassessment | Initial holistic answer may complete; later reassessment is not inferred or auto-looped | PDF 23–24 / printed 19–20 |

**Approved decisions:** `MSC-CQ-DIARRHOEA-001`, `MSC-CQ-REASSESS-001`, and `IP-CQ-002` are fixed by the versioned review-decision set.

## Fever and measles

| Clinical condition | Computational representation | Classification/action | Source |
| --- | --- | --- | --- |
| Danger sign or stiff neck | Severe row with malaria-risk modifier | `VERY_SEVERE_FEBRILE_DISEASE`; urgent actions; severe-malaria medicine only in high/low-risk branch | PDF 8 / printed 4 |
| Positive test or source no-test fallback | Test/risk state | `MALARIA`; first-line oral antimalarial | PDF 8 / printed 4 |
| Negative test or explicitly supplied other cause | Provisional OR interpretation | `FEVER_NO_MALARIA` | PDF 8 / printed 4 |
| No malaria risk/no travel without severe signs | Separate risk branch | `FEVER` | PDF 8 / printed 4 |
| Temperature ≥38.5°C | Axillary measurement | Add paracetamol action | PDF 8 / printed 4 |
| Fever every day >7 days | Duration/history | Refer for assessment | PDF 8 / printed 4 |
| Measles now/recent plus severe, eye/mouth, or fallback conditions | Separate simultaneous sub-classification | Severe complicated, eye/mouth complications, or measles; Vitamin A and conditional local treatment | PDF 8 / printed 4 |

**Approved decisions:** `MSC-CQ-FEVER-001`, `MSC-CQ-FEVER-002`, and `MSC-CQ-FEVER-003` are fixed by the versioned review-decision set.

## Ear problem

| Clinical condition | Representation | Classification/action | Source |
| --- | --- | --- | --- |
| Tender swelling behind ear | Clinician observation | `MASTOIDITIS`; antibiotic, paracetamol, urgent referral | PDF 9 / printed 5 |
| Pain or pus with discharge <14 days | History plus observed pus | `ACUTE_EAR_INFECTION`; antibiotic, pain relief, dry wicking, follow-up | PDF 9 / printed 5 |
| Pus with discharge ≥14 days | Same with boundary | `CHRONIC_EAR_INFECTION`; dry wicking, quinolone drops, follow-up | PDF 9 / printed 5 |
| No pain and no pus | Explicit negatives | `NO_EAR_INFECTION`; no ear treatment | PDF 9 / printed 5 |

**Approved:** Observed pus with reliably reported no prior discharge maps to acute ear infection after excluding mastoiditis (`MSC-CQ-EAR-001`).

## Follow-up scope

The current artifact emits follow-up timing from the classification rows but does not execute the separate follow-up-visit algorithms on PDF pages 32–33. This initial-visit-only boundary is approved under `MSC-CQ-SCOPE-001`.

## Integrated management review

Confirm or revise these interactions:

1. danger signs drive general, respiratory, fever, and measles severe rows only when their pathways are active;
2. another severe classification switches some/severe dehydration from local rehydration to referral with ORS/breastfeeding;
3. dehydration changes persistent diarrhoea severity;
4. measles does not replace respiratory, diarrhoea, or ear classification;
5. HIV exposure/infection modifies chest-indrawing pneumonia management;
6. duplicate actions are deduplicated while provider-rule traces are retained;
7. urgent output leads with source-mandated pre-referral/transfer actions; routine home-care and scheduled follow-up are retained as deferred audit evidence under `IP-CQ-004`.

## Completeness review

Approve or revise this product rule:

```text
final_holistic_synthesis_authorized
    exactly when
supported_encounter_complete
```

A provisionally invariant partial outcome never authorizes early final synthesis. An explicit negative pathway-entry answer makes that deeper assessment not applicable; silence leaves it unknown and the encounter incomplete. Required initial-assessment intervention/reassessment evidence and any future encounter-specific unresolved question also gate completion. Plan B/C timed reassessment is a separate treatment-stage submission and does not block the initial holistic answer.

## Proposed disposition

The recorded review is complete for the bounded hackathon representation. The product-level holistic golden-slice construction may proceed against the approved decision set after verification; bulk generation and training remain separate, not-yet-started stages.
