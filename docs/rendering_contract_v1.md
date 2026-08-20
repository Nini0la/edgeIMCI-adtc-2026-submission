# EdgeIMCI rendering contract v1

**Status:** `PROPOSED_FOR_HUMAN_REVIEW`  
**Scope:** Language realization of the fixed 14-case golden semantic conversion slice.  
**Not:** clinical logic, a model-performance benchmark, an SFT corpus, or approval for bulk generation.

## 1. Purpose and authority

EdgeIMCI speaks to a frontline primary-health-care worker. The language layer converts an already-determined structured interaction into concise clinical communication:

```text
fixed golden semantic trajectory
        ↓
model-visible known information
        ↓
structured expected assistant semantics
        ↓
PHC rendering
```

The committed structured trajectory remains authoritative. Rendering may change wording and grouping, but must not add, omit, infer, or alter:

- observations or their known/unknown state;
- who supplies or assesses an observation;
- classifications;
- actions and referral urgency;
- whether classification must wait for more information;
- decision-directed requests;
- remaining assessment requests;
- turn order or cumulative multi-turn state.

Use **classification**, not diagnosis, except when explicitly discussing diagnosis as a separate concept. Do not expose rule IDs, schema fields, policy names, sufficiency flags, or implementation terminology.

## 2. Core voice

The v1 voice is:

- direct and clinically clear;
- concise enough to scan during a PHC encounter;
- calm in routine care and unmistakably urgent when escalation is required;
- specific about the next clinical action;
- faithful to caregiver report, clinician observation, and measurement as different evidence sources.

Use ordinary clinical English. Prefer short paragraphs or a brief list when urgent actions would be hard to scan in one sentence. Avoid rationale not present in the structured semantics.

## 3. Rendering modes

### 3.1 PHC case presentation

Render only information already visible at that turn. Group related facts rather than serializing every field separately. Preserve the evidence source where it affects interpretation.

**Do**

> The child is 18 months old. The caregiver reports cough or difficult breathing and no diarrhoea. On examination, there is chest indrawing while the child is calm, with no stridor. The respiratory rate is 35 breaths per minute, counted for one full minute while calm.

**Do not**

> The caregiver says cough. The caregiver says no diarrhoea. On observation chest indrawing is true. On observation stridor is false.

**Do not** imply that an unmentioned observation is absent. If only two danger signs have been assessed, report only those two.

### 3.2 Caregiver question

Tell the PHC worker to ask the caregiver. Do not convert caregiver history into clinician observation.

**Do**

> Ask the caregiver whether the child is able to drink or breastfeed.

**Do not**

> Observe whether the child is able to drink or breastfeed.

The question may use positive wording for clarity even when the underlying rule tests inability. It must still elicit the same observation.

### 3.3 Clinician observation request

Use `check`, `observe`, `look for`, or similarly explicit clinical-observation wording. Retain required conditions such as the child being calm.

**Do**

> Check for chest indrawing while the child is calm.

**Do not**

> Ask the caregiver whether there is chest indrawing.

### 3.4 Measurement request

State the actual measurement procedure. A qualitative impression is not a respiratory-rate measurement.

**Do**

> Count the child's breaths for one full minute while the child is calm and report the respiratory rate.

**Do not**

> Does the child seem to be breathing fast?

Do not render a caregiver statement such as “breathing seems fast” as a measured respiratory rate.

### 3.5 Classification and action response

Make the classification easy to scan, then state every source-backed action. Use the exact selected-scope classification label without presenting it as a diagnosis.

**Do**

> Classification: Pneumonia.
>
> Give oral amoxicillin for 5 days, soothe the throat and relieve the cough with a safe remedy, advise the caregiver when to return immediately, and follow up in 3 days.

**Do not**

> Diagnosis: Pneumonia. The action set is sufficient.

When classification is not yet determined, do not guess or emit a fallback classification. It is permissible to state an already invariant supported action while requesting the evidence still needed for classification.

### 3.6 Urgent escalation

Put urgency first. State immediate treatment/referral actions before non-urgent explanation. Do not delay known urgent actions while remaining assessment continues.

**Do**

> URGENT: Act now.
>
> Classification: Very severe disease.
>
> Give the indicated pre-referral treatment immediately, prevent low blood sugar, keep the child warm, and arrange urgent referral.

**Do not**

> There are several findings to consider. After completing the assessment, referral may be appropriate.

The presentation order of simultaneous action blocks remains a rendering choice under `IP-CQ-004`; no v1 wording may suppress an action.

## 4. Decision requests versus remaining assessment

These channels must remain distinguishable in natural language.

### Decision-directed request

The evidence is required before the supported classification or complete action set can be determined.

> Before classifying, count the child's breaths for one full minute while the child is calm and report the respiratory rate.

Do not classify prematurely.

### Remaining-assessment request

The current classification/actions are already determined, but selected-scope assessment remains incomplete.

> Classification: No dehydration.
>
> Give Plan A fluid, zinc, and food, advise when to return immediately, and follow up in 5 days if the child is not improving. Also pinch the abdominal skin and observe how quickly it returns.

Do not imply that the remaining check can change a decision when the structured semantics say it cannot. During urgent escalation, make clear that the remaining assessment must not delay treatment or referral.

## 5. Multi-turn behavior

At each turn:

1. use all information visible so far;
2. render newly supplied user information naturally;
3. do not repeat the whole case unless repetition prevents a clinical error;
4. request only the acquisitions in the current structured target;
5. recompute after the next reveal;
6. stop requesting decision information once the decision-directed queue is empty;
7. emit classifications/actions only when present in the structured target;
8. retain any separate remaining-assessment request.

Never reveal latent observations. Unknown remains unknown until validly acquired.

## 6. Required terminology and prohibited internals

### Required

- `Classification:` or an equally explicit classification statement;
- the selected-scope classification label;
- explicit action verbs;
- `ask the caregiver` for caregiver questions;
- `check`/`observe` for clinician observations;
- `count ... for one full minute ... while calm` for respiratory-rate measurement;
- an immediate urgency cue for urgent states.

### Prohibited in frontline output

- `DECISION_SUFFICIENT`;
- `ACTION_SET_SUFFICIENT`;
- `ASSESSMENT_COMPLETE`;
- `possible_fired_rule_ids`;
- `decision-directed acquisition`;
- `assessment-completion acquisition`;
- policy, schema, constraint, or rule IDs;
- “the model thinks” or implementation rationale.

Natural language may express the clinical consequence of an internal state—for example, “Before classifying, count…”—without naming that state.

## 7. Semantic acceptance gates

A candidate is rejected before naturalness review if deterministic checks find any of the following:

- missing or additional classification;
- missing or additional action;
- missing urgency cue;
- missing required acquisition;
- wrong acquisition mode;
- premature classification;
- internal policy/schema terminology;
- obvious unsupported numbers or assertion of a requested unknown as fact.

These lexical checks are conservative guards, not unrestricted language understanding. Human/domain-expert review must still assess:

- negation and subtle entailment;
- invented observations not caught lexically;
- completeness and clinical clarity;
- naturalness;
- suitability for a frontline PHC worker;
- action ordering under unresolved presentation questions.

## 8. Proposed reference renderings

All 14 cases have candidate reference renderings in:

- `data/golden/golden_reference_renderings_v1.jsonl`

Every record and turn is marked `PROPOSED_FOR_HUMAN_REVIEW`. These references are deterministic language proposals over the fixed semantics; they do not replace or modify `golden_conversion_slice_v1.jsonl`.

## 9. Bake-off interpretation

The teacher experiment uses the same 14 cases and 16 assistant targets for every configuration. It is a **conversion acceptance / teacher bake-off**, not a model-performance benchmark. A high lexical semantic pass rate is necessary but not sufficient for approval. No teacher or prompt becomes approved until a human/domain expert reviews the side-by-side outputs.
