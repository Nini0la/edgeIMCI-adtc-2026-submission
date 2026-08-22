# Major sick-child IMCI expansion map v1

> **Authority:** `REVIEW_RECORD` · **Lifecycle:** `CURRENT` · Source/provenance map read together with the approved decision set.

**Status:** Source-derived engineering map with provisional computational interpretations. Domain-expert approval is required before product-level golden data.

**Clinical source:** [WHO *Integrated Management of Childhood Illness, Chart Booklet*, March 2014](../data/sources/IMCI%20chartbooklet%202014.pdf).

**Encoding statement:** This repository contains a **machine-readable clinical rule set derived from the WHO IMCI Chart Booklet**. It is not a WHO-authored machine-readable rule set.

## Supported scope

The expanded scope is the major sick-child assessment for:

```text
2 <= age_months < 60
```

It contains exactly these five assessment areas:

1. general danger signs;
2. cough or difficult breathing;
3. diarrhoea;
4. fever, including the measles sub-classification;
5. ear problem.

It does not add the young-infant pathway or claim coverage of nutrition, anaemia, immunization, feeding, HIV assessment, well-child care, or every other IMCI activity. HIV status is represented only where it changes chest-indrawing pneumonia management.

The current representation is an initial-encounter model. It emits source-defined follow-up timing, but does not execute the separate return-visit algorithms on PDF pages 32–33; this boundary is approved under `MSC-CQ-SCOPE-001`.

## Provenance categories

| Category | Meaning |
| --- | --- |
| `DIRECT_SOURCE_DERIVED` | The chart supplies the observation, condition, classification, or action directly. |
| `COMPUTATIONAL_REPRESENTATION` | The source logic is encoded in a typed state or deterministic operation; the representation itself is EdgeIMCI-authored. |
| `UNRESOLVED_CLINICAL_INTERPRETATION` | The source does not determine a safe software behavior without expert or local-protocol input. |

## General danger signs

**Source:** PDF page 5, printed page 1 of 76.

| Source element | Computational representation | Classification/action effect | Basis |
| --- | --- | --- | --- |
| Able to drink or breastfeed | `danger_signs.unable_to_drink_or_breastfeed` | Positive contributes `VERY_SEVERE_DISEASE` and urgent/pre-referral actions | Direct |
| Vomits everything | `danger_signs.vomits_everything` | Same | Direct |
| Convulsions during illness | `danger_signs.had_convulsions` | Same | Direct |
| Lethargic or unconscious | `danger_signs.lethargic_or_unconscious` | Same; also a severe-dehydration sign | Direct |
| Convulsing now | `danger_signs.convulsing_now` | Same plus diazepam action | Direct |
| Any danger sign | Five independent rules; pathway classification is shared while sign/rule trace remains multi-valued | Complete assessment quickly, pre-referral treatment, prevent low blood sugar, keep warm, urgent referral | Direct + computational aggregation |

Completeness requires all five observations even when one known sign has already established urgency. Known urgent actions are emitted immediately; final holistic synthesis remains withheld until the whole supported encounter is complete.

## Cough or difficult breathing

**Assessment/classification source:** PDF page 6, printed page 2 of 76.
**Treatment support:** PDF pages 16–17 and 19, printed pages 12–13 and 15 of 76.

### Required and conditional observations

| Observation | Requirement | Purpose |
| --- | --- | --- |
| `has_cough_or_difficult_breathing` | Always required entry status | Explicit negative makes the deeper pathway not applicable |
| `cough_duration_days` | Required when active | Referral for cough longer than 14 days |
| `respiratory_rate` | Required when active | Age-specific fast-breathing derived finding |
| `chest_indrawing` | Required when active | Pneumonia and bronchodilator-trial trigger |
| `stridor_when_calm` | Required when active | Severe classification |
| `wheezing` | Required when active | Reassessment sequence and five-day bronchodilator action |
| `recurrent_wheeze` | Required when active | TB/asthma assessment referral |
| calm and one-minute validity flags | Required when active | Source-valid respiratory evidence |
| pulse-oximeter availability | Required when active | Saturation is required when available; refer below 90% |
| post-bronchodilator rate/chest/validity | Conditional | Required after wheeze with initial fast breathing or chest indrawing |
| HIV exposed/infected status | Conditional | Required when effective chest indrawing is present because management changes |

### Logic map

| Source condition | Classification/action | Precedence or stage | Review state |
| --- | --- | --- | --- |
| Age 2–11 months and rate ≥50 | `FAST_BREATHING` | Derived finding | Direct |
| Age 12–59 months and rate ≥40 | `FAST_BREATHING` | Derived finding | Direct |
| Wheeze plus fast breathing/chest indrawing | Bronchodilator trial, then repeat rate and chest assessment before classification | Intervention → reassessment | Source sequence direct; state contract under `MSC-CQ-RESP-001` |
| Any danger sign or stridor while calm | `SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE` | Dominates lower rows | Direct |
| Chest indrawing or fast breathing | `PNEUMONIA` | After required reassessment | Direct |
| No severe/pneumonia sign | `COUGH_OR_COLD` | Fallback after complete valid assessment | Direct |
| Wheeze now or before trial | Inhaled bronchodilator for 5 days | Conditional action | Direct |
| Cough >14 days or recurrent wheeze | Refer for possible TB/asthma assessment | Conditional action | Direct |
| Saturation <90%, when oximetry available | Refer without independently activating urgent pre-referral workflow | Conditional action | Direct source + `imci-major-sick-child-oxygen-referral-disposition-v1` |
| Chest indrawing with HIV exposure/infection | First dose amoxicillin and refer | Changes routine pneumonia management | `MSC-CQ-RESP-002` |

The three-day amoxicillin footnote and unavailable-referral behavior require local/national or Pocket Book policy not supplied by the generic chart. V1 uses the main five-day row and does not invent unavailable-referral management.

## Diarrhoea

**Assessment/classification source:** PDF page 7, printed page 3 of 76.
**Treatment/reassessment source:** PDF pages 16, 23–24, printed pages 12 and 19–20 of 76.

### Required observations

- explicit diarrhoea entry status;
- duration in days;
- blood in stool;
- general condition: lethargic/unconscious and restless/irritable;
- sunken eyes;
- observed drinking response after offering fluid;
- abdominal skin-pinch return;
- cholera-locality status when age is at least 24 months and severe dehydration is classified;
- post-rehydration dehydration observations when Plan B or C requires reassessment.

### Simultaneous classification families

The diarrhoea assessment can produce up to three simultaneous classification families:

| Family | Rules | Source behavior |
| --- | --- | --- |
| Dehydration | `SEVERE_DEHYDRATION`, `SOME_DEHYDRATION`, `NO_DEHYDRATION` | Highest applicable dehydration row |
| Duration | `SEVERE_PERSISTENT_DIARRHOEA`, `PERSISTENT_DIARRHOEA`, or none | Evaluated when duration ≥14 days |
| Blood | `DYSENTERY` or none | Evaluated independently when blood is present |

### Treatment and interaction map

| Condition | Action behavior | Cross-pathway/stage effect |
| --- | --- | --- |
| Severe dehydration without another severe classification | Plan C | Reassessment required before supported encounter completion |
| Severe dehydration with another severe classification | Urgent referral with frequent ORS sips and continued breastfeeding | Replaces local Plan C branch |
| Some dehydration without another severe classification | Plan B, return/follow-up advice | Four-hour reassessment required |
| Some dehydration with another severe classification | Urgent referral with ORS/breastfeeding | Replaces local Plan B branch |
| No dehydration | Plan A | No in-clinic reassessment stage |
| Severe persistent diarrhoea | Treat dehydration before referral unless another severe classification; refer | Severity interaction |
| Persistent diarrhoea without dehydration | Feeding advice; multivitamins/minerals including zinc for 14 days; follow-up | Independent duration classification |
| Dysentery | Ciprofloxacin for 3 days; follow-up | Independent blood classification |
| Severe dehydration, age ≥2 years, cholera locally | Add generic locally recommended cholera-antibiotic action | Hackathon v1 does not invent drug/dose/duration (`MSC-CQ-DIARRHOEA-001`) |

Plan B and Plan C are emitted in the initial holistic answer. Timed reassessment is represented as a separate later treatment-stage submission under `MSC-CQ-REASSESS-001`; hackathon v1 does not execute full Plan C facility-resource branching or automatic loops.

## Fever and measles

**Assessment/classification source:** PDF page 8, printed page 4 of 76.
**Treatment support:** PDF pages 17, 20–22, printed pages 13 and 16–18 of 76.

### Fever observations

- explicit fever entry status;
- axillary temperature for the ≥38.5°C action threshold;
- versioned malaria-risk state: high, low, or no risk/no travel;
- duration and, when over seven days, whether present every day;
- stiff neck;
- runny nose;
- obvious cause of fever and identified bacterial cause as separate provisional fields;
- malaria-test availability/result when the source requires testing;
- measles history/current-sign observations.

### Fever classification map

| Context | Condition | Classification | Principal action differences |
| --- | --- | --- | --- |
| High or low malaria risk | Any danger sign or stiff neck | `VERY_SEVERE_FEBRILE_DISEASE` | Severe-malaria pre-referral treatment, antibiotic, low-blood-sugar prevention, urgent referral |
| No malaria risk/no travel | Any danger sign or stiff neck | Same | Same except no severe-malaria medicine |
| High/low risk | Positive test, or source fallback when required test unavailable | `MALARIA` | First-line oral antimalarial |
| High/low risk | Negative test or explicit other/obvious cause | `FEVER_NO_MALARIA` | Cause-specific treatment and three-day fever follow-up |
| No malaria risk/no travel | No danger sign and no stiff neck | `FEVER` | Two-day fever follow-up |

The `FEVER: NO MALARIA` routes, malaria-risk context acquisition, and generic identified-bacterial-cause action are fixed by `MSC-CQ-FEVER-001..003`. The worker/app supplies the area's risk category; the model does not infer it. No drug, dose, or regimen is invented for a generic bacterial cause.

### Measles sub-classification

Measles is active when explicitly reported within the last three months or when generalized rash plus cough, runny nose, or red eyes establishes current measles.

| Condition | Classification | Actions |
| --- | --- | --- |
| Danger sign, clouded cornea, or deep/extensive mouth ulcers | `SEVERE_COMPLICATED_MEASLES` | Vitamin A, antibiotic, conditional eye ointment, urgent referral |
| Pus from eye or mouth ulcers | `MEASLES_WITH_EYE_OR_MOUTH_COMPLICATIONS` | Vitamin A, appropriate local treatment, follow-up |
| Measles without those complications | `MEASLES` | Vitamin A |

Measles does not suppress pneumonia, diarrhoea, or ear classifications; the source explicitly says those complications are classified in their other tables.

## Ear problem

**Assessment/classification source:** PDF page 9, printed page 5 of 76.
**Local treatment source:** PDF pages 16–17 and 19, printed pages 12–13 and 15 of 76.

| Condition | Classification | Actions |
| --- | --- | --- |
| Tender swelling behind ear | `MASTOIDITIS` | First antibiotic dose, paracetamol for pain, urgent referral |
| Ear pain, or pus plus reported discharge under 14 days | `ACUTE_EAR_INFECTION` | Antibiotic 5 days, paracetamol, dry wicking, follow-up |
| Pus plus reported discharge for at least 14 days | `CHRONIC_EAR_INFECTION` | Dry wicking, topical quinolone drops 14 days, follow-up |
| No pain and no pus | `NO_EAR_INFECTION` | No ear treatment |

Pus observed with reliably reported no previous discharge establishes a current episode under 14 days and maps to acute ear infection after mastoiditis is excluded (`MSC-CQ-EAR-001`).

## Cross-pathway dependencies and precedence

| Dependency | Current deterministic representation | Status |
| --- | --- | --- |
| Danger signs → respiratory severe row | Danger sign classification also activates severe respiratory classification when cough/breathing pathway is active | Source-derived |
| Danger signs → fever severe row | Danger sign activates very severe febrile disease when fever is active | Source-derived |
| Danger signs → severe measles row | Danger sign activates severe complicated measles when measles is active | Source-derived |
| Other severe classification → dehydration actions | Select referral/ORS/breastfeeding instead of local Plan B/C | Source-derived |
| Dehydration → persistent diarrhoea severity | Any dehydration changes persistent to severe persistent | Source-derived |
| HIV exposure/infection → chest-indrawing management | Modifies pneumonia action block | Unresolved integration detail |
| Measles complications → other tables | Respiratory, diarrhoea, and ear classifications remain independently active | Source-derived |
| Duplicate/shared actions | Deduplicated by action identity while provider rules remain traced | Computational representation |
| Routine actions alongside urgent referral | Immediate output retains pre-referral/transfer actions; routine home care/follow-up remains deferred and auditable | `IP-CQ-004` approved |

## Reassessment stages

| Trigger | Intermediate action | Required new evidence | Final-synthesis gate |
| --- | --- | --- | --- |
| Wheeze with fast breathing/chest indrawing | Bronchodilator trial | Valid post-trial rate and chest-indrawing observation | Incomplete until supplied |
| Some dehydration without other severe classification | Plan B | Complete post-Plan-B dehydration assessment | Incomplete until supplied |
| Severe dehydration without other severe classification | Plan C | Complete post-Plan-C dehydration assessment | Incomplete until supplied |

## Readiness statement

The source map and all 13 review decisions now support deterministic hackathon engineering. This is **not production-approved clinical logic**. The product-level holistic golden slice may now be constructed and reviewed against the pinned decision set; bulk generation and training remain later stages.
