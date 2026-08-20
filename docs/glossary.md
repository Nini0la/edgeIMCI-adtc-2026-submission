# EdgeIMCI Glossary

| Term | Definition |
|------|-----------|
| Clinical rule | A source-backed deterministic rule encoded from the currently supported IMCI material. Clinical rules determine classifications/actions; interaction policy must not alter them. |
| Clinical rules v0 / imci-selected-v0 | The frozen current EdgeIMCI clinical subset: children 2–59 months, general danger signs, respiratory pathway, and diarrhoea/dehydration pathway. |
| Observation | A clinical fact that may be reported, observed, or measured, e.g. respiratory rate or vomiting everything. |
| Predicate | A logical condition derived from observations, e.g. age < 12 months AND RR >= 50. |
| Derived finding | An intermediate result computed from observations and used by later rules, e.g. fast_breathing=true. |
| Classification | The IMCI category produced by the encoded rules, e.g. PNEUMONIA or SEVERE_DEHYDRATION. Prefer this over diagnosis when describing EdgeIMCI. |
| Action | A source-backed treatment, referral, counselling, follow-up, or other prescribed step produced by a rule. |
| Rule priority | The deterministic precedence among competing rules within a pathway. |
| Oracle / reference evaluator | The deterministic implementation that applies the frozen clinical rules and produces ground truth. It is not an LLM. |

## Information-state layer

| Term | Definition |
|------|-----------|
| Known present/value | An observation has been explicitly acquired and is positive or has a specific value. |
| Known absent | An observation has been explicitly acquired and found absent/negative. |
| Unknown | The observation has not been validly acquired. Unknown never means negative. |
| Partial case | A case in which some potentially relevant observations remain unknown. |
| Valid completion | One clinically/schema-valid assignment of values to currently unknown observations. Used to determine whether unresolved information could alter an outcome. |
| Decision-relevant observation | An unknown observation for which at least two valid values lead to different outcomes for the target currently being considered. |
| Required next observation | A currently unknown observation that the information policy says must now be acquired because it can change classification, actions, urgency, or another active decision target. |
| Remaining assessment observation | An observation still needed to complete the supported assessment but no longer necessary to determine the current classification/action. |

## Sufficiency / policy layer

These definitions are especially important because "sufficient information" is no longer one boolean.

| Term | Definition |
|------|-----------|
| Information policy | The deterministic policy that decides whether current information is sufficient and, if not, which information should be acquired next. It sits above the frozen clinical oracle. |
| Decision sufficient | All valid completions of the remaining unknowns yield the same classification for the specified target. |
| Action-set sufficient | All valid completions yield the same relevant source-backed action set. |
| Assessment complete | Every observation designated as part of the currently supported active assessment has been validly acquired, even if some were no longer decision-relevant. |
| Urgent action required | Existing evidence already supports a source-backed urgent action that must not be delayed while further information is acquired. |
| Outcome invariance | The principle that a target is sufficient when its outcome remains identical across every valid completion of the unknown information. |
| Short circuit | A state in which further observations cannot change a specified decision target, although they may still matter for assessment completion or another target. |
| Blocked | A necessary observation cannot be acquired, so the policy cannot safely resolve the relevant decision and must not guess. |

## Information acquisition layer

| Term | Definition |
|------|-----------|
| Acquisition request | A request to obtain a missing observation. It may be a question, observation instruction, or measurement instruction. |
| Caregiver question | Information obtained by asking the caregiver, e.g. vomiting everything. |
| Clinician observation | Information the frontline worker must directly observe/assess. |
| Measurement | Information requiring an explicit measurement procedure, e.g. respiratory rate. |
| History or record | Information such as age obtained from history or an existing record. |
| Acquisition mode | The method by which an observation must be obtained. The current proposal distinguishes the four types above. See `information_policy_proposal.md`. |
| Validity requirement | Conditions that must hold for an acquired observation to count as valid evidence, e.g. respiratory assessment while the child is calm. |
