# EdgeIMCI information policy proposal

**Status:** Approved v1 design record. This is interaction-policy logic, not new clinical logic.

**Recorded review decisions:** `IP-RQ-001` and `IP-RQ-002` are approved for v1. `IP-CQ-001` through `IP-CQ-004` remain unresolved and must not be implemented by assumption.

**Implementation:** Canonical artifacts live in `configs/information_policy/`; the deterministic evaluator and execution contract are documented in [`docs/information_policy_v1.md`](information_policy_v1.md).

This document proposes how EdgeIMCI should decide whether the information currently known about a child is sufficient to emit a classification or urgent action, and which observation should be acquired next when it is not. It is deliberately limited to `imci-selected-v0`: children aged 2 months to under 5 years, general danger signs, cough or difficult breathing, and diarrhoea dehydration classification.

It does not add clinical rules, expand the supported IMCI pathways, generate conversational data, or change the frozen rule set.

## Evidence reviewed

The proposal was derived from:

- [`data/rules/imci_selected_v0.json`](../data/rules/imci_selected_v0.json), the canonical frozen rule artifact;
- [`src/edge_imci/evaluation/reference.py`](../src/edge_imci/evaluation/reference.py), the deterministic evaluator;
- [`src/edge_imci/schemas/case.py`](../src/edge_imci/schemas/case.py) and [`prediction.py`](../src/edge_imci/schemas/prediction.py), the current typed contracts;
- [`data/benchmark/imci_v0.jsonl`](../data/benchmark/imci_v0.jsonl), including its ten missing-information cases;
- the danger-sign, respiratory, dehydration, parsing, and generation tests; and
- WHO *Integrated Management of Childhood Illness, Chart Booklet*, March 2014, PDF viewer pages 5-7, printed pages 1-3 of 76.

The source pages say to check general danger signs before the main symptoms; define any general danger sign as requiring urgent attention; instruct the worker to complete the assessment and pre-referral treatment immediately so referral is not delayed; gate respiratory assessment on cough or difficult breathing; and gate diarrhoea assessment on diarrhoea. The same pages supply the currently encoded classification conditions and actions.

## 1. Conceptual framework

### 1.1 Unknown is a real state

Every observation used by the information policy has at least three knowledge states:

```text
KNOWN_PRESENT / KNOWN_VALUE
KNOWN_ABSENT
UNKNOWN
```

`UNKNOWN` must never be converted to a negative value. Absence is usable evidence only when it was explicitly reported, observed, or measured as absent/normal.

The current observation dataclasses already allow `None` for most clinical observations. The two pathway-entry fields, `has_cough_or_difficult_breathing` and `has_diarrhoea`, are plain booleans and therefore cannot represent `UNKNOWN`. A future partial-case schema must correct that without weakening the existing frozen benchmark schema.

### 1.2 Four separate questions

The policy must answer four questions independently:

| State | Meaning |
| --- | --- |
| `DECISION_SUFFICIENT` | All valid completions of the remaining unknowns produce the same classification for the stated pathway/scope. |
| `ACTION_SET_SUFFICIENT` | All valid completions produce the same source-backed action set for the stated pathway/scope. |
| `ASSESSMENT_COMPLETE` | Every encoded observation designated for the active supported assessment has been acquired validly, even if some became irrelevant to classification. This means the EdgeIMCI-supported subset, not the full IMCI assessment. |
| `URGENT_ACTION_REQUIRED` | Known evidence already fires an encoded urgent action. It must be surfaced immediately and must not wait for `ASSESSMENT_COMPLETE`. |

These flags are not mutually exclusive. A general danger sign can make `DECISION_SUFFICIENT=true` and `URGENT_ACTION_REQUIRED=true` while `ASSESSMENT_COMPLETE=false`.

The current `ModelPrediction.sufficient_information` boolean cannot represent these distinctions: it is forced to be true exactly when the evaluator's single global missing-observation list is empty. It should be retained only for compatibility until a richer policy result is introduced.

### 1.3 Decision sufficiency by outcome invariance

For a partial case, the proposed policy should:

1. preserve every unknown;
2. enumerate or symbolically represent all valid completions of only the relevant unknown observations;
3. apply the unchanged frozen evaluator/rules to each completion;
4. project results to the requested target, such as respiratory classification, urgent referral, or the full action set; and
5. declare that target sufficient only when the projected result is identical across every valid completion.

An unknown observation is **currently decision-relevant** only if at least two valid values for it lead to different projected outcomes. Such observations belong in `decision_directed_acquisitions`. Unknowns that cannot change the current projection but are still part of the active supported assessment belong separately in `assessment_completion_acquisitions`. An observation must not appear in both lists at the same evaluation step. This prevents every `None` from becoming an automatic question while preserving unfinished assessment work.

The projection must be explicit. Classification sufficiency, exact fired-rule sufficiency, detected-danger-sign completeness, and action-set sufficiency can differ. For example, fast breathing and chest indrawing both produce the same encoded `PNEUMONIA` classification/actions, but an unknown chest-indrawing value prevents identification of the exact rule that would have priority. Per approved `IP-RQ-001`, classification/action sufficiency may be true in that state while exact-rule sufficiency remains false.

### 1.4 Versioned valid-completion constraints

Outcome invariance is meaningful only relative to an explicit completion domain. V1 must use a separately versioned constraint set:

```text
constraint_set_id: imci-selected-v0-valid-completions-v1
rule_set_id: imci-selected-v0
```

The constraint set is part of the policy's reproducibility identity. Every policy evaluation and generated trajectory must record its `constraint_set_id`; changing a value domain, coherence rule, pathway-entry interpretation, or inference permission requires a new constraint-set version.

The v1 constraints are:

| Constraint ID | Explicit rule | Completion use | Basis/provenance |
| --- | --- | --- | --- |
| `VC-SCOPE-001` | Only integer ages 2-59 months are passed to the frozen evaluator. Unknown age branches to `IN_SCOPE` versus `OUT_OF_SCOPE`; an out-of-scope branch stops without clinical evaluation. | Scope gate | `DIRECT_SOURCE_DERIVED`; rule-set population and chart heading, pages 5-7 / printed 1-3 |
| `VC-DOMAIN-001` | All danger, entry, chest-indrawing, stridor, restless/irritable, and sunken-eyes observations complete to explicit booleans. | Enumerated domain | `INTERACTION_POLICY`, constrained by current typed schemas |
| `VC-DOMAIN-002` | `drinking_status` completes to exactly `NORMAL`, `EAGER_OR_THIRSTY`, `POORLY`, or `UNABLE`; `skin_pinch` completes to exactly `NORMAL`, `SLOWLY`, or `VERY_SLOWLY`. | Enumerated domain | `DIRECT_SOURCE_DERIVED` value meanings through the dehydration rules; page 7 / printed 3 |
| `VC-DOMAIN-003` | Respiratory rate completes to a non-negative integer. For classification invariance it need only be partitioned into below-threshold versus at/above-threshold values for the known age band. | Symbolic domain partition | `DIRECT_SOURCE_DERIVED` threshold partition plus current non-negative schema validation; page 6 / printed 2 |
| `VC-ENTRY-001` | Entry `true` activates its pathway; entry `false` produces `NOT_APPLICABLE`; entry `UNKNOWN` creates both branches. Existing respiratory/dehydration values do not imply pathway entry. | Branching and projection | `DIRECT_SOURCE_DERIVED` pathway questions/evaluator gates; pages 6-7 / printed 2-3 |
| `VC-CONTAINER-001` | For an active pathway, an absent observation group means that every field in that group is `UNKNOWN`, not negative. For an inactive pathway, its observation group is irrelevant to that pathway projection. | Partial-state normalization | `INTERACTION_POLICY`; corrects the current container-before-short-circuit artifact without changing rules |
| `VC-COHERENCE-001` | `lethargic_or_unconscious=true` and `restless_or_irritable=true` cannot coexist in one completion. | Invalid completion is removed | `INTERACTION_POLICY` mirroring the existing `ClinicalObservations` invariant |
| `VC-COHERENCE-002` | An explicitly supplied `drinking_status=UNABLE` together with explicitly supplied `danger_signs.unable_to_drink_or_breastfeed=false` is invalid input. When either field is unknown, do not copy or infer the other. | Input validation only; **not** completion pruning/inference in v1 | `INTERACTION_POLICY` mirroring the current schema while leaving `IP-CQ-002` unresolved |
| `VC-EVIDENCE-001` | Values are treated as known under the same evidence assumptions as the frozen benchmark. V1 does not invent a calm-state/measurement-validity inference rule. | No additional pruning | `UNRESOLVED_CLINICAL_AMBIGUITY`; `IP-CQ-003` remains open |
| `VC-UNKNOWN-001` | No unknown is completed from omission, prose silence, a default constructor value, or an unrelated observation. | Global completion rule | `INTERACTION_POLICY`; unknown-is-not-negative requirement |

`VC-COHERENCE-002` deliberately distinguishes validation from inference. It can reject an explicit contradictory pair, but it cannot make an unknown danger-sign answer positive merely because the dehydration drinking assessment says `UNABLE`. The policy must keep that acquisition unresolved until `IP-CQ-002` is resolved.

The completion engine must output the constraint IDs used to exclude candidate states. If a partial case cannot be represented without relying on a constraint marked input-only or unresolved, return `BLOCKED`/unresolved rather than manufacturing a completion.

### 1.5 Pathway and encounter scope

The policy must calculate sufficiency at several scopes:

```text
general_danger_signs
respiratory
dehydration
supported_encounter
```

`supported_encounter` means only the three currently encoded areas. It must never be labelled a complete IMCI encounter because other main symptoms and source-page branches are out of scope.

For the supported encounter, age/scope, both pathway-entry observations, general danger-sign state, each active pathway decision, and every action-changing cross-pathway dependency must be resolved before the overall decision/action set is final. Known urgent actions remain immediately actionable even when this overall state is incomplete.

## 2. Observation catalog and acquisition mode

`HISTORY_OR_RECORD` is added as a justified acquisition mode for demographic/scope facts that may come from a caregiver or an existing record. It must not be used for clinician findings or measurements. The chart's explicit **Ask** versus **Look/observe/count/offer/pinch** distinctions support the caregiver, clinician-observation, and measurement assignments below. Choosing `HISTORY_OR_RECORD` and packaging those source activities as machine enums are `INTERACTION_POLICY` decisions, not WHO terminology.

| Observation | Value domain | Acquisition mode | Encoded use | Provenance |
| --- | --- | --- | --- | --- |
| `patient_facts.age_months` | Integer; supported range 2-59 | `HISTORY_OR_RECORD` | Scope gate; selects respiratory-rate threshold | Rule-set population; `IMCI-RESP-FAST-BREATHING-2-12M`, `IMCI-RESP-FAST-BREATHING-12-60M`; pages 5-6 / printed 1-2 |
| `patient_facts.has_cough_or_difficult_breathing` | `true`, `false`, `UNKNOWN` in future partial state | `CAREGIVER_QUESTION` | Respiratory pathway entry | Respiratory chart question; page 6 / printed 2; evaluator pathway gate |
| `patient_facts.has_diarrhoea` | `true`, `false`, `UNKNOWN` in future partial state | `CAREGIVER_QUESTION` | Dehydration pathway entry | Diarrhoea chart question; page 7 / printed 3; evaluator pathway gate |
| `danger_signs.unable_to_drink_or_breastfeed` | Boolean/`UNKNOWN` | `CAREGIVER_QUESTION` | General danger sign; respiratory severe condition | `IMCI-GDS-UNABLE-TO-DRINK`, `IMCI-RESP-SEVERE-DANGER-SIGN`; pages 5-6 / printed 1-2 |
| `danger_signs.vomits_everything` | Boolean/`UNKNOWN` | `CAREGIVER_QUESTION` | General danger sign; respiratory severe condition | `IMCI-GDS-VOMITS-EVERYTHING`, `IMCI-RESP-SEVERE-DANGER-SIGN`; pages 5-6 / printed 1-2 |
| `danger_signs.had_convulsions` | Boolean/`UNKNOWN` | `CAREGIVER_QUESTION` | General danger sign; respiratory severe condition | `IMCI-GDS-CONVULSIONS-HISTORY`, `IMCI-RESP-SEVERE-DANGER-SIGN`; pages 5-6 / printed 1-2 |
| `danger_signs.lethargic_or_unconscious` | Boolean/`UNKNOWN` | `CLINICIAN_OBSERVATION` | General danger sign; respiratory severe condition; one severe-dehydration sign | `IMCI-GDS-LETHARGIC-OR-UNCONSCIOUS`, `IMCI-RESP-SEVERE-DANGER-SIGN`, `IMCI-DIARRHOEA-SEVERE-DEHYDRATION`; pages 5-7 / printed 1-3 |
| `danger_signs.convulsing_now` | Boolean/`UNKNOWN` | `CLINICIAN_OBSERVATION` | General danger sign; adds diazepam action when present | `IMCI-GDS-CONVULSING-NOW`, `IMCI-RESP-SEVERE-DANGER-SIGN`; pages 5-6 / printed 1-2 |
| `respiratory.stridor_when_calm` | Boolean/`UNKNOWN` | `CLINICIAN_OBSERVATION` | Severe respiratory classification | `IMCI-RESP-SEVERE-STRIDOR`; page 6 / printed 2 |
| `respiratory.chest_indrawing` | Boolean/`UNKNOWN` | `CLINICIAN_OBSERVATION` | Pneumonia classification | `IMCI-RESP-PNEUMONIA-CHEST-INDRAWING`; page 6 / printed 2 |
| `respiratory.respiratory_rate` | Non-negative integer/`UNKNOWN` | `MEASUREMENT` | Fast-breathing threshold and pneumonia classification | Both fast-breathing rules and `IMCI-RESP-PNEUMONIA-FAST-BREATHING`; page 6 / printed 2 |
| `dehydration.restless_or_irritable` | Boolean/`UNKNOWN` | `CLINICIAN_OBSERVATION` | One some-dehydration sign | `IMCI-DIARRHOEA-SOME-DEHYDRATION`; page 7 / printed 3 |
| `dehydration.sunken_eyes` | Boolean/`UNKNOWN` | `CLINICIAN_OBSERVATION` | One sign in both dehydration severity sets | Both dehydration count rules; page 7 / printed 3 |
| `dehydration.drinking_status` | `NORMAL`, `EAGER_OR_THIRSTY`, `POORLY`, `UNABLE`, `UNKNOWN` | `CLINICIAN_OBSERVATION` after offering fluid | One sign in severe or some dehydration depending on value | Both dehydration count rules; page 7 / printed 3 |
| `dehydration.skin_pinch` | `NORMAL`, `SLOWLY`, `VERY_SLOWLY`, `UNKNOWN` | `CLINICIAN_OBSERVATION` after abdominal skin pinch | One sign in severe or some dehydration depending on value | Both dehydration count rules; page 7 / printed 3 |

Respiratory rate, chest indrawing, and stridor are valid only for the source-described calm-child assessment. The current schema does not represent whether the child was calm or whether the rate was counted for one minute. A future observation record needs validity/method metadata; the policy must not silently accept an invalid measurement as equivalent evidence.

The source also asks about cough duration, diarrhoea duration, blood in stool, wheeze, and other observations, but those branches are not in `imci-selected-v0`. They must not be requested or used by this policy. Wheeze remains separately blocked by `CQ-001` in [`docs/clinical_questions.md`](clinical_questions.md).

## 3. Pathway-by-pathway sufficiency

### 3.1 General danger signs

The five danger signs form an any-of rule. There is no source-backed negative clinical classification; a completed all-negative assessment means only that no general danger-sign rule fired.

| Decision state | Required now | Conditionally required | No longer required for this decision | Assessment/action caveat |
| --- | --- | --- | --- | --- |
| `VERY_SEVERE_DISEASE` / urgent referral | Any one of the five signs known positive | `convulsing_now` remains action-relevant if unknown because it can add diazepam | Other signs cannot change the already-determined classification or referral | Remaining signs are still required for `ASSESSMENT_COMPLETE` and a complete detected-sign inventory. Source says complete assessment quickly without delaying referral. |
| No general danger sign detected | All five signs explicitly negative | None | None | Unknown is not negative; no general classification is emitted. |
| Unresolved | No known positive and at least one unknown that could be positive | Every such unknown sign | Explicitly negative signs | Ask/observe the remaining danger-sign items before claiming no danger sign. |

### 3.2 Respiratory pathway

Entry requires known `has_cough_or_difficult_breathing=true`. A known false value makes the pathway `NOT_APPLICABLE`. An unknown entry value makes respiratory pathway state unresolved. Age must be known and in scope for the encounter; it becomes a direct classifier dependency when respiratory rate is used.

The table below is for **classification and configured respiratory actions**, not exact fired-rule identity or assessment completion.

| Classification | Required observations | Conditional observations | Not required once decision is invariant | Provenance |
| --- | --- | --- | --- | --- |
| `SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE` from a danger sign | Respiratory entry true; any general danger sign known positive | `convulsing_now` and other danger items may change the overall action/sign inventory | Stridor, chest indrawing, and respiratory rate cannot change the respiratory class/actions | `IMCI-RESP-SEVERE-DANGER-SIGN`, priority 1; page 6 / printed 2. General danger actions: page 5 / printed 1. |
| `SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE` from stridor | Respiratory entry true; `stridor_when_calm=true` | General danger signs remain relevant to overall classification/actions, but not to the already invariant respiratory class/actions | Chest indrawing and respiratory rate | `IMCI-RESP-SEVERE-STRIDOR`, priority 2; page 6 / printed 2 |
| `PNEUMONIA` from chest indrawing | Respiratory entry true; all general danger signs negative; stridor negative; chest indrawing positive | None for respiratory class/actions | Respiratory rate | `IMCI-RESP-PNEUMONIA-CHEST-INDRAWING`, priority 3; page 6 / printed 2 |
| `PNEUMONIA` from fast breathing | Respiratory entry true; age known/in scope; all general danger signs negative; stridor negative; respiratory rate at/above the age threshold | Chest indrawing is required for exact fired-rule identity and assessment completion, but not for class/actions because both values produce the same configured result | Chest indrawing for the class/action projection only | Both threshold rules and `IMCI-RESP-PNEUMONIA-FAST-BREATHING`, priority 4; page 6 / printed 2 |
| `COUGH_OR_COLD` | Respiratory entry true; age known/in scope; all danger signs negative; stridor negative; chest indrawing negative; respiratory rate below the age threshold | None | None | `IMCI-RESP-COUGH-OR-COLD`, priority 5; page 6 / printed 2 |

The current evaluator is more procedurally strict than this proposed class/action policy in several partial states. It checks for a respiratory observation object before danger-sign short-circuiting, requires every danger sign to be resolved before considering known stridor, and checks chest indrawing before a known fast respiratory rate. The proposed outcome-invariance rule would allow the earlier classifications described above while keeping `ASSESSMENT_COMPLETE=false`. This is an interaction-policy proposal and requires explicit approval and compatibility tests; it is not a clinical-rule change.

### 3.3 Diarrhoea dehydration pathway

Entry requires known `has_diarrhoea=true`. Known false makes the pathway `NOT_APPLICABLE`; unknown makes it unresolved.

Define the severe-sign predicates as:

```text
lethargic_or_unconscious == true
sunken_eyes == true
drinking_status in {UNABLE, POORLY}
skin_pinch == VERY_SLOWLY
```

Define the some-dehydration predicates as:

```text
restless_or_irritable == true
sunken_eyes == true
drinking_status == EAGER_OR_THIRSTY
skin_pinch == SLOWLY
```

| Classification | Required observations at the current state | Conditionally required | No longer required once decision is invariant | Action caveat | Provenance |
| --- | --- | --- | --- | --- | --- |
| `SEVERE_DEHYDRATION` | Any two severe predicates known true | Other-severe-classification status is required to select Plan C versus referral/ORS/breastfeeding actions | Remaining dehydration observations cannot lower the classification | If another severe classification is unresolved, classification can be sufficient while the dehydration action set is not | `IMCI-DIARRHOEA-SEVERE-DEHYDRATION`, priority 1; page 7 / printed 3 |
| `SOME_DEHYDRATION` | At least two some predicates known true **and** severe dehydration proven impossible under every completion | Unknown fields that could still make two severe signs; other-severe-classification status for the action branch | Fields that can no longer create severe or change the some-dehydration result | Another severe classification replaces the non-referral Plan B action branch in the frozen rule | `IMCI-DIARRHOEA-SOME-DEHYDRATION`, priority 2; page 7 / printed 3 |
| `NO_DEHYDRATION` | Both severe and some dehydration proven impossible under every valid completion | Only unknowns still capable of making either count reach two | Unknowns that can contribute at most one sign when every other qualifying predicate is already false | Configured no-dehydration actions do not branch on another severe classification, though overall encounter actions may still be incomplete | `IMCI-DIARRHOEA-NO-DEHYDRATION`, priority 3; page 7 / printed 3 |

This count logic is state-dependent. No individual dehydration observation is unconditionally required in every partially known case. For example, if every severe and some predicate except an unknown skin pinch is known false, the skin-pinch answer cannot create the required count of two; `NO_DEHYDRATION` is already decision-sufficient, while the supported dehydration assessment remains incomplete.

For severe and some dehydration, `other_severe_classification` is an action dependency. The frozen evaluator defines it as any detected general danger sign or a severe respiratory classification. If that dependency can still change across valid completions, the policy must not present Plan B/Plan C or the referral branch as the final complete dehydration action set.

## 4. Proposed decision and priority rules

Every rule below declares its basis. `DIRECT_SOURCE_DERIVED` means that the clinical condition/order/action comes directly through the frozen rules and cited source. `INTERACTION_POLICY` means that the proposal controls information acquisition without claiming to be a WHO rule. `UNRESOLVED_CLINICAL_AMBIGUITY` means no implementation should decide it without review.

| Policy ID | Proposed rule | Basis | Supporting rules/source |
| --- | --- | --- | --- |
| `IP-SCOPE-001` | Establish age in the supported 2-59 month range before claiming an EdgeIMCI-supported encounter result. | `DIRECT_SOURCE_DERIVED` | Rule-set population; chart heading; both fast-breathing rules; pages 5-6 / printed 1-2 |
| `IP-UNKNOWN-001` | Preserve unprovided observations as `UNKNOWN`; do not treat them as absent. | `INTERACTION_POLICY` | Nullable observation schema; required to avoid unsupported fallback classifications |
| `IP-GDS-001` | Assess general danger signs before main-symptom pathways. Any known positive sign immediately establishes urgent attention/referral. | `DIRECT_SOURCE_DERIVED` | All five `IMCI-GDS-*` rules; page 5 / printed 1 |
| `IP-GDS-002` | A known danger sign makes the urgent decision sufficient but not the supported assessment complete. Surface urgent actions immediately and represent remaining assessment separately. | `DIRECT_SOURCE_DERIVED` | All five `IMCI-GDS-*` actions include `COMPLETE_ASSESSMENT_QUICKLY`, pre-referral treatment, and urgent referral; page 5 / printed 1 |
| `IP-ENTRY-001` | After the danger-sign check, acquire cough/difficult-breathing and diarrhoea entry states. Do not activate a pathway on an unknown or inferred-negative entry. | `DIRECT_SOURCE_DERIVED` | Source sequence and pathway questions; evaluator gates; pages 6-7 / printed 2-3 |
| `IP-RESP-001` | Within an active respiratory pathway, prioritize observations capable of an urgent severe classification before non-urgent pneumonia/cold discriminators. | `DIRECT_SOURCE_DERIVED` for severity precedence; `INTERACTION_POLICY` for question scheduling | Respiratory priorities 1-5; page 6 / printed 2 |
| `IP-DEHYD-001` | Evaluate severe-dehydration possibility before some-dehydration and fallback; stop requesting fields that cannot change the count outcome. | `DIRECT_SOURCE_DERIVED` for rule priority/counts; `INTERACTION_POLICY` for adaptive stopping | Dehydration priorities 1-3; page 7 / printed 3 |
| `IP-CROSS-001` | Resolve another-severe-classification status before calling severe/some dehydration actions final. | `DIRECT_SOURCE_DERIVED` | Action branches in both counted dehydration rules; page 7 / printed 3 |
| `IP-NEXT-001` | Schedule v1 acquisitions deterministically by declared priority band and canonical observation order. Do not score or estimate information gain. | `INTERACTION_POLICY` | Uses but does not alter source severity order |
| `IP-NEXT-002` | Never put an observation that cannot change the requested classification/action target in `decision_directed_acquisitions`; put it in `assessment_completion_acquisitions` only when it remains part of the supported assessment. | `INTERACTION_POLICY` | Outcome-invariance definition |
| `IP-ACTION-001` | Do not delay a known urgent action while collecting information for assessment completion or another non-urgent target. | `DIRECT_SOURCE_DERIVED` | Urgent-attention instruction on page 5 / printed 1; urgent respiratory/dehydration actions on pages 6-7 / printed 2-3 |

### Priority bands

1. **Known urgent action:** emit it immediately. This is output priority, not another question.
2. **General danger-sign assessment:** the source places this before main symptoms and any positive result can change urgent status.
3. **Pathway entry:** acquire cough/difficult-breathing and diarrhoea status so active pathways are known.
4. **Urgent pathway discriminators:** for respiratory disease, stridor when calm; for dehydration, observations that can still complete the severe-dehydration count; and any unresolved cross-pathway severe status that changes dehydration actions.
5. **Non-urgent classification discriminators:** chest indrawing, respiratory rate/age threshold, and observations that distinguish some from no dehydration.
6. **Assessment-only observations:** fields no longer capable of changing the current decision/action projection.

The source does not define a clinical order among the five general danger signs or among the individual dehydration signs. Any within-band ordering is an interaction design decision and must be labelled as such.

### Deterministic v1 scheduler

V1 must not rank questions with a learned score, estimated information gain, or dynamic cost function. It should use this deterministic procedure:

1. Emit all known urgent actions before scheduling another acquisition.
2. Recompute `decision_directed_acquisitions` from the chosen outcome projection.
3. Assign each acquisition the fixed priority band above.
4. Sort by `(priority_band, canonical_observation_index)` using the versioned order below.
5. Form a batch only from acquisitions in the same priority band that satisfy the batching rules in section 5. Preserve acquisition modes within the batch so caregiver questions, clinician observations, and measurements remain distinguishable.
6. Return the first batch. After its results arrive, evaluate the policy again from the beginning.
7. Schedule `assessment_completion_acquisitions` only when the decision-directed list is empty, or alongside urgent workflow when an approved source/expert decision explicitly permits it. `IP-CQ-001` currently prevents inventing that urgent-workflow sequencing.

The canonical v1 observation order is a tie-breaker, not a claim of clinical precedence within a source-defined group:

```text
patient_facts.age_months
danger_signs.convulsing_now
danger_signs.lethargic_or_unconscious
danger_signs.unable_to_drink_or_breastfeed
danger_signs.vomits_everything
danger_signs.had_convulsions
patient_facts.has_cough_or_difficult_breathing
patient_facts.has_diarrhoea
respiratory.stridor_when_calm
respiratory.chest_indrawing
respiratory.respiratory_rate
dehydration.restless_or_irritable
dehydration.sunken_eyes
dehydration.drinking_status
dehydration.skin_pinch
```

This order and the scheduler algorithm belong to the versioned information-policy artifact. Changing either requires a policy version change, even when the frozen clinical rules do not change.

## 5. One question versus batching

The policy should operate on **acquisition requests**, not assume every missing item is a caregiver question.

Each evaluation returns two disjoint channels:

- `decision_directed_acquisitions`: observations that can still change the selected classification/action projection or add an immediate action; and
- `assessment_completion_acquisitions`: observations that cannot change that projection but remain uncompleted items in the active supported assessment.

Only the first channel controls `DECISION_SUFFICIENT`. The second controls `ASSESSMENT_COMPLETE`. UI text may present both when permitted, but it must preserve the channel label so assessment-only work is never misrepresented as a prerequisite for an already-sufficient decision.

### Batch related observations when

- they have the same acquisition mode and intended respondent/operator;
- they are in the same priority band;
- each is currently relevant or part of a source-required rapid assessment bundle;
- receiving them together avoids a needless conversational turn; and
- batching cannot delay a known urgent action.

Recommended batches:

- the three caregiver-reported danger items: ability to drink/breastfeed, vomiting everything, and history of convulsions;
- the two clinician-observed danger items: lethargic/unconscious and convulsing now;
- cough/difficult-breathing and diarrhoea pathway-entry questions;
- when the child is calm, the respiratory clinician bundle: count respiratory rate for one minute, observe chest indrawing, and observe stridor; and
- the dehydration clinician bundle: general condition, sunken eyes, response when offered fluid, and abdominal skin-pinch return.

These batches are proposed UX units, not new clinical rules.

### Request one observation when

- only one unknown can still change the current decision;
- it is a measurement or procedure that needs a distinct instruction;
- its answer can trigger immediate urgent action, after which the policy must re-evaluate before asking anything lower priority;
- different people must supply the remaining observations; or
- previous answers have made the rest of a proposed batch irrelevant.

After every response or assessment result, recompute sufficiency and the next-observation set. Do not continue a prewritten questionnaire blindly.

## 6. Stop conditions

### Stop waiting and emit urgent action when

- any encoded general danger sign is known positive;
- active respiratory assessment has a known general danger sign or stridor when calm; or
- a dehydration action branch is known to require urgent referral because another severe classification is already established.

Emit only actions already supported by known evidence. Mark `URGENT_ACTION_REQUIRED=true`. If the source calls for rapid completion of assessment, keep `ASSESSMENT_COMPLETE=false` and list remaining assessment work separately; do not represent that work as a prerequisite to the urgent action.

### Stop decision-directed information gathering for one pathway when

- its classification is invariant across all valid completions; and
- any pathway-specific action branch requested by the caller is also invariant.

Do not request observations that can only alter the exact fired-rule trace when the requested target is classification/actions. If exact trace or full assessment is requested, retain them under that separate target.

### Stop the supported encounter decision loop when

- age/scope is established;
- both pathway-entry states are known;
- general danger status is decision-sufficient;
- every active supported pathway is decision-sufficient;
- the combined action set is invariant; and
- there is no unresolved observation capable of adding a time-critical action such as diazepam.

`ASSESSMENT_COMPLETE` may still be false. Conversely, do not output `ASSESSMENT_COMPLETE=true` merely because classification is sufficient.

### Stop without classifying when

- age is outside the frozen 2-59 month population (`OUT_OF_SCOPE`);
- the requested pathway is known inactive (`NOT_APPLICABLE`); or
- a required observation cannot be obtained (`BLOCKED`), in which case report the unresolved outcome set and acquisition failure rather than guessing.

The action for an unavailable clinically required observation is not defined by the frozen rules and requires review before deployment.

## 7. Worked examples

These are policy examples, not new corpus records.

### Complete respiratory case

Known: age 18 months; cough/difficult breathing present; all five danger signs negative; no stridor when calm; no chest indrawing; respiratory rate 34/min while calm.

Result: respiratory `COUGH_OR_COLD`; `DECISION_SUFFICIENT=true`; respiratory `ASSESSMENT_COMPLETE=true`; no urgent action. The 40/min threshold comes from `IMCI-RESP-FAST-BREATHING-12-60M`, and the fallback is `IMCI-RESP-COUGH-OR-COLD`.

### Incomplete respiratory case

Known: age 18 months; cough present; all danger signs negative; stridor negative; chest indrawing negative; respiratory rate unknown.

Result: possible respiratory outcomes are `PNEUMONIA` and `COUGH_OR_COLD`; `DECISION_SUFFICIENT=false`. Next acquisition: `respiratory.respiratory_rate` via `MEASUREMENT`. Do not ask dehydration observations for this pathway decision.

### Danger-sign short circuit with incomplete assessment

Known: cough present; `vomits_everything=true`; other danger signs and all respiratory observations unknown.

Result: general `VERY_SEVERE_DISEASE`, respiratory `SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE`, and urgent referral are decision-sufficient from `IMCI-GDS-VOMITS-EVERYTHING` and `IMCI-RESP-SEVERE-DANGER-SIGN`. Respiratory rate, chest indrawing, and stridor cannot change the respiratory class/actions. `URGENT_ACTION_REQUIRED=true`, while `ASSESSMENT_COMPLETE=false`. `convulsing_now` remains action-relevant because a positive result adds diazepam; it must not delay the already-known urgent referral.

### Stridor short circuit with danger assessment unresolved

Known: cough/difficult breathing present; stridor when calm present; general danger-sign answers unknown.

Result: the respiratory class and its antibiotic/urgent-referral actions are invariant under `IMCI-RESP-SEVERE-STRIDOR`; chest indrawing and respiratory rate are not needed for that target. General danger assessment remains incomplete and can add general-danger actions or diazepam. The current evaluator does not yet express this split and would need an information-policy wrapper.

### Pneumonia decision with exact rule unresolved

Known: age 18 months; respiratory pathway active; all danger signs negative; stridor negative; respiratory rate 45/min; chest indrawing unknown.

Result: the respiratory classification/action projection is always `PNEUMONIA`, because either chest indrawing or fast breathing produces the same configured result. `DECISION_SUFFICIENT=true`, `ASSESSMENT_COMPLETE=false`, and exact fired-rule identity is unresolved between the chest-indrawing and fast-breathing rules.

### Dehydration with one decisive missing observation

Known: diarrhoea present; lethargic false; restless false; sunken eyes true; skin pinch normal; drinking status unknown.

Result: `UNABLE/POORLY` would produce severe dehydration, `EAGER_OR_THIRSTY` would produce some dehydration, and `NORMAL` would produce no dehydration. `DECISION_SUFFICIENT=false`. Request only `dehydration.drinking_status` by instructing the clinician to offer fluid and observe the response. This mirrors `dehyd_missing_severe_drinking`.

### Dehydration classification sufficient but actions unresolved

Known: diarrhoea present; sunken eyes true; drinking poorly; other dehydration observations unknown; general danger and respiratory severe status unresolved.

Result: two severe signs make `SEVERE_DEHYDRATION` invariant. The remaining dehydration signs are not needed for that classification. The dehydration action set is not sufficient because another severe classification selects referral/ORS/breastfeeding instead of Plan C.

### Unknown that is not currently required

Known: diarrhoea present; lethargic false; restless false; sunken eyes false; drinking normal; skin pinch unknown.

Result: an isolated skin-pinch value can contribute at most one severe or one some-dehydration sign, so neither count can reach two. `NO_DEHYDRATION` is decision-sufficient, but the supported dehydration assessment is incomplete. Do not request skin pinch for the classification target; retain it only as assessment work.

### Supported encounter versus one pathway

Known: respiratory pathway is complete and classified, but diarrhoea entry is unknown.

Result: respiratory `DECISION_SUFFICIENT=true`; supported-encounter `DECISION_SUFFICIENT=false`. Ask whether the child has diarrhoea, not for dehydration signs yet. A single-pathway result must not be presented as the overall supported encounter result.

## 8. Ambiguities and review questions

No `IP-CQ-*` item below should be resolved from general medical knowledge. All four remain `UNRESOLVED`; v1 must expose the relevant unresolved question ID rather than fill the gap.

### IP-CQ-001 - Extent and sequencing of rapid assessment after a danger sign

- **Source:** all `IMCI-GDS-*` rules; page 5 / printed 1: urgent attention, complete assessment and pre-referral treatment immediately so referral is not delayed.
- **Ambiguity:** The source establishes both urgency and continued assessment, but the frozen subset does not specify exactly which remaining supported observations must be obtained before departure, which may be obtained during pre-referral preparation, or when further questioning would delay referral.
- **Decision needed:** Define the operational boundary between immediate action and rapid continued assessment for the conversational workflow.
- **Classification:** `UNRESOLVED_CLINICAL_AMBIGUITY`.

### IP-CQ-002 - Reuse of drinking evidence across two assessments

- **Source:** `IMCI-GDS-UNABLE-TO-DRINK` on page 5 / printed 1 asks the caregiver about ability to drink/breastfeed; `IMCI-DIARRHOEA-SEVERE-DEHYDRATION` on page 7 / printed 3 observes response after offering fluid.
- **Ambiguity:** The current schema stores these as separate observations, while also rejecting `drinking_status=UNABLE` paired with an explicitly negative unable-to-drink danger sign. It does not define when one observation can populate or imply the other.
- **Decision needed:** Determine whether and in which direction evidence may be reused, or require both acquisition procedures.
- **Classification:** `UNRESOLVED_CLINICAL_AMBIGUITY`.

### IP-CQ-003 - Validity representation for the calm respiratory assessment

- **Source:** respiratory chart, page 6 / printed 2, requires the child to be calm while counting breaths and assessing chest indrawing/stridor.
- **Ambiguity:** The current schema stores values but no calm-state, one-minute-count, observer, or validity metadata.
- **Decision needed:** Decide the minimum evidence metadata needed before the policy may treat a respiratory observation as valid.
- **Classification:** `UNRESOLVED_CLINICAL_AMBIGUITY` for the acceptable evidence contract; adding metadata is an implementation task after review.

### IP-CQ-004 - Home-care actions alongside an unrelated urgent referral

- **Source:** `IMCI-DIARRHOEA-NO-DEHYDRATION` has unconditional Plan A/home-care actions on page 7 / printed 3; general danger and severe respiratory rules separately require urgent referral.
- **Ambiguity:** The frozen evaluator unions these actions, so a child can receive urgent-referral actions and no-dehydration home-care actions together. The frozen rules do not define conversational ordering, suppression, or deferral of the home-care instructions in this combination.
- **Decision needed:** Decide how to present multiple valid action blocks without delaying or obscuring urgency. Do not suppress an encoded action without clinical approval.
- **Classification:** `UNRESOLVED_CLINICAL_AMBIGUITY`.

### Approved interaction decisions

#### IP-RQ-001 - Classification sufficiency versus exact-rule sufficiency

- **Source:** respiratory priorities and equal configured results for the two pneumonia rules; page 6 / printed 2.
- **Decision:** **APPROVED for v1.** Outcome-invariance may establish classification/action sufficiency when those projections are fixed but the highest-priority fired rule remains unknown, as in fast breathing with chest indrawing unknown.
- **Required representation:** Keep `exact_rule_sufficient=false` and expose the possible fired rule IDs; do not claim the rule trace is complete.
- **Classification:** `INTERACTION_POLICY`, not a clinical-rule change.

#### IP-RQ-002 - Compatibility with the current evaluator's procedural missing list

- **Source:** current evaluator implementation, not WHO logic.
- **Decision:** **APPROVED for v1.** The separate information-policy evaluator's `decision_directed_acquisitions` may be a strict subset of `EvaluationResult.missing_required_observations`.
- **Required compatibility behavior:** Retain the frozen evaluator as the complete-case clinical oracle; do not silently redefine or overwrite its legacy missing list. Record policy-versus-legacy differences with reason codes.
- **Classification:** `INTERACTION_POLICY` and software compatibility decision.

### Explicitly unresolved/out of scope

- Wheeze and bronchodilator reassessment remain under existing `CQ-001`.
- Oxygen saturation, cough duration/prolonged cough, HIV modifiers, persistent diarrhoea, dysentery, and cholera logic are visible in the source but absent from `imci-selected-v0`.
- Unavailable-referral behavior is not encoded.
- Follow-up-visit workflow and all other IMCI main symptoms are not encoded.

The information policy must neither ask for these items as if it could use them nor emit classifications/actions from their source branches.

## 9. Proposed machine-readable policy schema

The policy should become a versioned canonical JSON artifact with a generated YAML mirror, separate from the clinical rule set:

```text
configs/information_policy/
├── imci_selected_v0_information_policy.json          # canonical policy
├── imci_selected_v0_information_policy.yaml          # generated policy mirror
├── valid_completion_constraints_v1.json              # canonical constraint set
└── valid_completion_constraints_v1.yaml              # generated constraint mirror
```

Both JSON artifacts are canonical, independently versioned inputs. Their YAML files are generated review mirrors. The policy must pin `constraint_set_id`; summaries, evaluations, and later trajectories must record both IDs.

The constraint artifact must encode every row in section 1.4, including whether a constraint is used for completion pruning, input validation only, or remains disabled pending review. A condensed shape is:

```json
{
  "constraint_set_id": "imci-selected-v0-valid-completions-v1",
  "rule_set_id": "imci-selected-v0",
  "constraints": [
    {
      "constraint_id": "VC-COHERENCE-002",
      "kind": "FORBIDDEN_EXPLICIT_COMBINATION",
      "when": {
        "dehydration.drinking_status": "UNABLE",
        "danger_signs.unable_to_drink_or_breastfeed": false
      },
      "enforcement": "INPUT_VALIDATION_ONLY",
      "completion_pruning": false,
      "basis": "INTERACTION_POLICY",
      "unresolved_question_id": "IP-CQ-002"
    }
  ]
}
```

The policy artifact should reference clinical rules rather than duplicate their results. A condensed illustrative shape is:

```json
{
  "policy_id": "imci-selected-v0-information-policy-v1",
  "rule_set_id": "imci-selected-v0",
  "constraint_set_id": "imci-selected-v0-valid-completions-v1",
  "status": "proposed",
  "knowledge_states": ["KNOWN", "UNKNOWN"],
  "acquisition_modes": [
    "CAREGIVER_QUESTION",
    "CLINICIAN_OBSERVATION",
    "MEASUREMENT",
    "HISTORY_OR_RECORD"
  ],
  "basis_types": [
    "DIRECT_SOURCE_DERIVED",
    "INTERACTION_POLICY",
    "UNRESOLVED_CLINICAL_AMBIGUITY"
  ],
  "observations": {
    "respiratory.respiratory_rate": {
      "value_type": "integer",
      "acquisition_mode": "MEASUREMENT",
      "validity_requirements": ["CHILD_CALM", "COUNTED_FOR_ONE_MINUTE"],
      "source_rule_ids": [
        "IMCI-RESP-FAST-BREATHING-2-12M",
        "IMCI-RESP-FAST-BREATHING-12-60M",
        "IMCI-RESP-PNEUMONIA-FAST-BREATHING"
      ],
      "source": {
        "source_pdf_page": 6,
        "source_printed_page": "2 of 76"
      },
      "basis": "DIRECT_SOURCE_DERIVED"
    }
  },
  "pathways": {
    "respiratory": {
      "entry_observation": "patient_facts.has_cough_or_difficult_breathing",
      "classification_projection": "classifications.respiratory",
      "rule_priority": [
        "IMCI-RESP-SEVERE-DANGER-SIGN",
        "IMCI-RESP-SEVERE-STRIDOR",
        "IMCI-RESP-PNEUMONIA-CHEST-INDRAWING",
        "IMCI-RESP-PNEUMONIA-FAST-BREATHING",
        "IMCI-RESP-COUGH-OR-COLD"
      ],
      "sufficiency_method": "VALID_COMPLETION_OUTCOME_INVARIANCE",
      "assessment_observations": [
        "respiratory.stridor_when_calm",
        "respiratory.chest_indrawing",
        "respiratory.respiratory_rate"
      ]
    }
  },
  "priority_rules": [
    {
      "policy_rule_id": "IP-GDS-001",
      "priority": 1,
      "basis": "DIRECT_SOURCE_DERIVED",
      "source_rule_ids": [
        "IMCI-GDS-UNABLE-TO-DRINK",
        "IMCI-GDS-VOMITS-EVERYTHING",
        "IMCI-GDS-CONVULSIONS-HISTORY",
        "IMCI-GDS-LETHARGIC-OR-UNCONSCIOUS",
        "IMCI-GDS-CONVULSING-NOW"
      ]
    }
  ],
  "scheduler": {
    "algorithm": "DETERMINISTIC_PRIORITY_THEN_CANONICAL_ORDER",
    "policy_version": 1,
    "uses_information_gain": false,
    "canonical_observation_order": [
      "patient_facts.age_months",
      "danger_signs.convulsing_now",
      "danger_signs.lethargic_or_unconscious",
      "danger_signs.unable_to_drink_or_breastfeed",
      "danger_signs.vomits_everything",
      "danger_signs.had_convulsions",
      "patient_facts.has_cough_or_difficult_breathing",
      "patient_facts.has_diarrhoea",
      "respiratory.stridor_when_calm",
      "respiratory.chest_indrawing",
      "respiratory.respiratory_rate",
      "dehydration.restless_or_irritable",
      "dehydration.sunken_eyes",
      "dehydration.drinking_status",
      "dehydration.skin_pinch"
    ]
  },
  "approved_decisions": ["IP-RQ-001", "IP-RQ-002"],
  "open_questions": ["IP-CQ-001", "IP-CQ-002", "IP-CQ-003", "IP-CQ-004"]
}
```

The runtime result should be a separate typed object. Proposed shape:

```json
{
  "policy_id": "imci-selected-v0-information-policy-v1",
  "constraint_set_id": "imci-selected-v0-valid-completions-v1",
  "scope_status": "IN_SCOPE",
  "pathway_states": {
    "general_danger_signs": {
      "entry_status": "ACTIVE",
      "possible_classifications": ["VERY_SEVERE_DISEASE"],
      "decision_sufficient": true,
      "action_set_sufficient": false,
      "assessment_complete": false
    },
    "respiratory": {
      "entry_status": "ACTIVE",
      "possible_classifications": ["SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE"],
      "decision_sufficient": true,
      "action_set_sufficient": true,
      "exact_rule_sufficient": true,
      "possible_fired_rule_ids": ["IMCI-RESP-SEVERE-DANGER-SIGN"],
      "assessment_complete": false
    },
    "dehydration": {
      "entry_status": "UNKNOWN",
      "possible_classifications": [
        "NOT_APPLICABLE",
        "SEVERE_DEHYDRATION",
        "SOME_DEHYDRATION",
        "NO_DEHYDRATION"
      ],
      "decision_sufficient": false,
      "action_set_sufficient": false,
      "assessment_complete": false
    }
  },
  "supported_encounter_decision_sufficient": false,
  "supported_encounter_action_set_sufficient": false,
  "supported_encounter_assessment_complete": false,
  "urgent_action_required": true,
  "known_actions": [
    "COMPLETE_ASSESSMENT_QUICKLY",
    "GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC",
    "GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY",
    "KEEP_WARM",
    "PREVENT_LOW_BLOOD_SUGAR",
    "URGENT_REFERRAL"
  ],
  "possible_additional_actions": ["GIVE_DIAZEPAM_IF_CONVULSING_NOW"],
  "decision_directed_acquisitions": [
    {
      "observation_id": "danger_signs.convulsing_now",
      "acquisition_mode": "CLINICIAN_OBSERVATION",
      "reason": "CAN_ADD_IMMEDIATE_ACTION",
      "priority_band": 2,
      "source_rule_ids": ["IMCI-GDS-CONVULSING-NOW"]
    }
  ],
  "assessment_completion_acquisitions": [
    {
      "observation_id": "danger_signs.unable_to_drink_or_breastfeed",
      "acquisition_mode": "CAREGIVER_QUESTION",
      "reason": "ASSESSMENT_COMPLETION_ONLY",
      "priority_band": 6,
      "source_rule_ids": ["IMCI-GDS-UNABLE-TO-DRINK"]
    },
    {
      "observation_id": "respiratory.respiratory_rate",
      "acquisition_mode": "MEASUREMENT",
      "reason": "ASSESSMENT_COMPLETION_ONLY",
      "priority_band": 6,
      "source_rule_ids": [
        "IMCI-RESP-FAST-BREATHING-2-12M",
        "IMCI-RESP-FAST-BREATHING-12-60M"
      ]
    }
  ],
  "applied_constraint_ids": ["VC-SCOPE-001", "VC-ENTRY-001", "VC-UNKNOWN-001"],
  "unresolved_question_ids": ["IP-CQ-001"]
}
```

Required enums should include:

```text
scope_status: IN_SCOPE | OUT_OF_SCOPE | UNKNOWN
entry_status: ACTIVE | NOT_APPLICABLE | UNKNOWN
decision status: SUFFICIENT | INSUFFICIENT | BLOCKED
next-observation reason:
  CAN_TRIGGER_URGENT_ACTION
  CAN_CHANGE_CLASSIFICATION
  CAN_CHANGE_ACTION_BRANCH
  CAN_ADD_IMMEDIATE_ACTION
assessment-completion reason:
  ASSESSMENT_COMPLETION_ONLY
```

Every policy rule and acquisition reason must carry `source_rule_ids`, page provenance where available, and one of the three basis types. Interaction rules with no clinical source must say so explicitly rather than borrowing a clinical citation. Runtime validation must require the decision-directed and assessment-completion observation ID sets to be disjoint.

## 10. Recommended implementation plan

Do not start trajectory or SFT-corpus generation until steps 1-6 are approved and tested.

1. **Preserve the recorded review state.** Treat `IP-RQ-001` and `IP-RQ-002` as approved. Leave `IP-CQ-001` through `IP-CQ-004` unresolved unless source or expert review supplies a documented resolution; do not implement an assumed answer.
2. **Freeze versioned policy and constraint artifacts.** Add the canonical JSON and generated YAML pairs, schemas, deterministic synchronization, provenance validation, and explicit policy-to-constraint-set pin. Do not edit `imci-selected-v0`.
3. **Add a separate partial-case representation.** It must support unknown pathway-entry states, acquisition mode, observation validity metadata, and acquisition failure. Keep `ClinicalCase` unchanged for the frozen complete/static benchmark.
4. **Implement a pure information-policy evaluator.** It should wrap or repeatedly call the existing deterministic evaluator over completions admitted by the pinned constraint set; it must not duplicate or reinterpret clinical conditions. Separate projections for classification, exact rule trace, urgent action, and complete actions.
5. **Implement only the declared v1 constraints.** Enforce each constraint according to its declared mode. Input-validation-only constraints must not prune completions or propagate values; unresolved constraints must remain disabled. Do not add drinking-field inference until `IP-CQ-002` is resolved.
6. **Build exhaustive policy tests before dialogue tests.** Cover every rule boundary, every single unknown, selected multi-unknown combinations, pathway-entry unknowns, cross-pathway action branches, short circuits, and all examples above. Assert that complete benchmark cases retain their frozen classifications/actions.
7. **Introduce the approved compatibility reporting.** Where `decision_directed_acquisitions` differs from the current evaluator's procedural `missing_required_observations`, record the reason and test it. Do not silently redefine the legacy field.
8. **Implement the deterministic v1 scheduler.** Use fixed priority bands and canonical observation order; keep the decision-directed and assessment-completion queues disjoint; do not add information-gain scoring.
9. **Only after approval, design trajectory generation.** Generate acquisition turns from policy results, keep acquisition modes and queue types distinct, re-evaluate after each answer, preserve policy/constraint/provenance IDs at every turn, and keep all corpus roles/splits leakage-safe.

The resulting architecture should be:

```text
partial known observations
        |
        v
information-policy evaluator --------> decision-directed acquisitions
        |                                  - ask caregiver
        |                                  - instruct clinician observation
        |                                  - request measurement
        |
        +------------------------------> assessment-completion acquisitions
        |
        +----> known urgent actions (never delayed)
        |
        v
frozen deterministic evaluator
        |
        v
classification + source-backed actions + rule provenance
```

This keeps interaction policy reviewable and replaceable while preserving the frozen clinical oracle as the sole owner of clinical classification/action logic.
