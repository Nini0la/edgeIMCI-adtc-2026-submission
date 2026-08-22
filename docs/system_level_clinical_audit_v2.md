# `imci-major-sick-child-v1` system-level clinical audit

**Audit date:** 2026-08-22

**Population:** `2 <= age_months < 60`

**Supported initial-assessment areas:** general danger signs, cough/difficult breathing, diarrhoea, fever including measles, and ear problem.

**Rule artifact:** `imci-major-sick-child-v1`
**Completeness policy:** `imci-major-sick-child-holistic-completeness-v2`
**Review decisions:** `imci-major-sick-child-review-decisions-v1`

## Conclusion

The expanded artifacts and evaluator form a deterministic, versioned engineering substrate for the bounded hackathon scope. The 13 recorded clinical/policy questions are resolved in a pinned decision set. Mechanical tests pass for the encoded conditions, completeness gate, urgent-action interrupt, approved reassessment boundary, simultaneous classifications, and selected cross-pathway action branches.

The substrate is **approved only for the bounded hackathon representation**, not for production clinical use. The former blockers no longer prevent product-level holistic golden-slice construction. Golden data must still be built and reviewed before bulk generation or training can begin.

No bulk dataset generation, teacher generation, training, optimization, or final split construction was performed.

## Artifact inventory

| Item | Count/status |
| --- | --- |
| Expanded logic units | 40 |
| General danger-sign units | 5 |
| Respiratory-prefixed units | 12 |
| Diarrhoea-prefixed units | 9 |
| Fever-prefixed units | 7 |
| Measles-prefixed units | 3 |
| Ear-prefixed units | 4 |
| Classification enum values | 21 |
| Action/referral/follow-up enum values | 47 |
| Named fast-breathing derived finding | 1, supplied by 2 age-threshold units |
| Intervention/reassessment units | 3: bronchodilator, Plan B, Plan C |
| Atomic whole-encounter observation/state fields | 62, of which 47 are new relative to the 15-field v0 case substrate |

The 62 fields comprise five patient/scope facts, five danger signs, sixteen respiratory fields, thirteen diarrhoea/rehydration-stage fields, eighteen fever/measles fields, and five ear fields.

## Verification matrix

| Audit area | Executable evidence | Result | Notes |
| --- | --- | --- | --- |
| Scope | ages 1/60 rejected; ages 2/59 exercised | PASS | Exactly 2–59 completed months |
| Respiratory thresholds | 49/50 at younger boundary and 39/40 at older boundary | PASS | Inclusive source thresholds |
| Ear duration | 13 versus 14 days | PASS | Acute/chronic boundary |
| Persistent diarrhoea | 13 versus 14 days | PASS | Duration classification boundary |
| High fever | 38.4 versus 38.5°C | PASS | Axillary threshold |
| Prolonged fever | 7 versus >7 days plus every-day evidence | PASS | Referral action only when both source conditions hold |
| Oxygen saturation | 89.9 versus 90% | PASS | Referral below 90 when oximetry is available |
| Explicit negative vs omission | explicit no diarrhoea versus unmentioned diarrhoea | PASS | Only explicit negative makes pathway not applicable |
| Holistic gate | internal classification with another area missing | PASS | No classification/action leaks into final output |
| Urgent incomplete | danger sign, stiff neck, mastoiditis | PASS | Known urgent/common pre-referral actions surface; final synthesis remains withheld |
| Bronchodilator sequence | trial trigger and post-treatment respiratory evidence | PASS | Approved simplified state contract under `MSC-CQ-RESP-001` |
| Rehydration sequence | initial Plan B/Plan C plus separate timed reassessment | PASS | Later treatment-stage submission does not block initial holistic answer |
| Dehydration severity interaction | another severe classification selects referral/ORS/breastfeeding | PASS | Local reassessment branch not required in that state |
| Persistent + dysentery | simultaneous classification families | PASS | Duration and blood rows coexist with dehydration row |
| Fever + measles | simultaneous malaria/measles results and actions | PASS | Measles precedence verified |
| HIV chest-indrawing dependency | action modification and provider trace | PASS | First dose amoxicillin + non-urgent referral replaces routine outpatient course |
| Cholera conditional action | age/severe/locality dependency | PASS | Generic locally recommended antibiotic; no invented drug details |
| Contradictions | drinking/GDS, calm evidence, malaria-test availability | PASS | Contradictions prevent completion; observed pus/no prior history is acute, not contradictory |
| Provenance/mirrors | JSON/YAML equality and evaluator rule-ID coverage | PASS | Every evaluator `IMCI-MSC-*` ID exists canonically |
| V0 preservation | 15 rules, 82 cases, approved v1 policy, 14 golden cases | PASS | Historical artifacts unchanged |

## Precedence and interaction relationships

1. respiratory severe rows precede pneumonia, which precedes cough/cold fallback;
2. dehydration severe precedes some, which precedes no-dehydration fallback;
3. fever severe precedes malaria/no-malaria/non-risk fever branches;
4. severe complicated measles precedes eye/mouth complications, which precede uncomplicated measles;
5. mastoiditis precedes acute, chronic, and no-ear-infection rows;
6. any other supported severe classification changes some/severe dehydration management;
7. dehydration presence changes persistent diarrhoea to severe persistent diarrhoea;
8. HIV exposure/infection modifies chest-indrawing pneumonia management;
9. intervention/reassessment stages take classification evidence from the post-intervention state where required;
10. actions are deduplicated by identity while every provider remains in the trace;
11. urgent referral output contains immediate pre-referral/transfer actions, while routine actions remain auditable as deferred.

The urgent-output rule is explicitly approved by `IP-CQ-004`; ordinary medication courses are never converted into first-dose instructions unless a source rule already says so.

## Urgent and pre-referral behavior

Implemented early channels include known source-backed actions for:

- any general danger sign;
- severe respiratory disease;
- very severe febrile disease;
- severe complicated measles;
- mastoiditis;
- another-severe-classification dehydration referral branches;
- severe persistent diarrhoea referral;
- oxygen saturation below 90% when measured.

An early action by itself never sets `supported_encounter_complete=true` and never authorizes final holistic synthesis. The remaining supported assessment must be completed rapidly without delaying urgent action/referral. Any future encounter-specific unresolved review question still blocks completion and final output.

## Reassessment behavior

Three staged branches are represented:

```text
wheeze + fast breathing/chest indrawing
→ bronchodilator trial
→ repeat rate/chest assessment
→ respiratory classification

some dehydration, no other severe classification
→ initial classification + Plan B
→ initial holistic answer may complete
→ four-hour reassessment arrives as a separate treatment-stage submission

severe dehydration, no other severe classification
→ initial classification + Plan C at plan level
→ initial holistic answer may complete
→ later reassessment arrives separately
```

The bronchodilator branch requires a completed indicated trial and valid post-treatment respiratory rate/chest-indrawing evidence before respiratory classification. Plan B/C timed reassessment is different: it belongs to a later treatment-stage submission and does not block completion of the initial holistic answer. Hackathon v1 does not execute detailed Plan C facility-capability branches or automatic treatment loops.

## Resolved clinical/policy questions

The approved hackathon review set is:

- `IP-CQ-001` through `IP-CQ-004` from v1;
- `MSC-CQ-SCOPE-001` follow-up-visit scope;
- `MSC-CQ-RESP-001` bronchodilator state contract;
- `MSC-CQ-RESP-002` HIV chest-indrawing action integration;
- `MSC-CQ-DIARRHOEA-001` local cholera antibiotic;
- `MSC-CQ-REASSESS-001` rehydration loops/facility branches;
- `MSC-CQ-FEVER-001` negative test versus other-cause Boolean logic;
- `MSC-CQ-FEVER-002` bacterial-cause vocabulary and antibiotic interaction;
- `MSC-CQ-FEVER-003` deployment-specific malaria-risk mapping;
- `MSC-CQ-EAR-001` observed pus with denied discharge history.

See [`clinical_questions.md`](clinical_questions.md) for source-oriented question history and `configs/information_policy/imci_major_sick_child_review_decisions_v1.json` for the canonical decisions. The policy's active unresolved list is empty. This does not imply production clinical authorization.

## Test record

- Holistic evaluator tests: **20 passed**.
- Holistic artifact tests: **3 passed**.
- V2 system-level audit tests: **22 passed**.
- New v2 total: **45 passed**.
- Full repository: **218 passed**.
- Frozen v0 inventory: **15 rules**, **82 benchmark cases**, **14 component golden cases**.

## Readiness decision

| Question | Decision |
| --- | --- |
| Is the mechanical holistic completeness evaluator implemented? | **YES, deterministically.** |
| Is the recorded domain/policy review complete for the bounded hackathon scope? | **YES.** All 13 decisions are versioned and pinned. |
| Is the integrated classification/action oracle approved for production clinical use? | **NO.** Hackathon scope only. |
| Do any of the 13 recorded questions still block the hackathon oracle? | **NO.** |
| Is the project ready to construct the product-level holistic golden slice? | **YES, as the next reviewed stage.** The slice itself has not yet been built. |
| Is the project ready for bulk generation or training? | **NO.** Explicitly out of scope. |
