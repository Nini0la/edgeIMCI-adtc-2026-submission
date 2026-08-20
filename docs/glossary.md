# EdgeIMCI Glossary

## Terminology rules

1. Use "classification" rather than "diagnosis" unless explicitly discussing diagnosis as a broader medical concept. EdgeIMCI currently executes encoded IMCI classifications; it is not being trained as an unrestricted diagnostic model.
2. "Required" must always be qualified when ambiguity exists: required for classification, required for action selection, required for urgent action, or required for assessment completion.

## Clinical truth / rule layer

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

## Dataset layer

| Term | Definition |
|------|-----------|
| Latent case / structured truth | The machine-readable underlying clinical state from which presentations and targets are generated. |
| Presentation | Natural-language information given to EdgeIMCI at a particular turn. It may expose only part of the latent case. |
| Training target | The desired natural-language model response associated with a training example. |
| Trajectory | A multi-turn sequence of presentation → information acquisition → new observations → eventual classification/action. |
| Renderer | The component that converts structured case information into natural language without changing its clinical meaning. |
| Golden slice | The small, manually audited pilot dataset used to validate the generation pipeline before bulk generation. |
| Round-trip consistency | A corpus-validation check in which generated natural language is converted back into structured meaning and compared with the original structured truth. |
| Counterfactual pair/group | Closely related cases differing in a controlled observation whose change should produce a known change—or deliberate lack of change—in outcome. |
| Logic signature | A stable identifier for the meaningful combination of clinical conditions represented by a generated case. |
| Template family | A family of related natural-language rendering patterns. |

## Evaluation layer

| Term | Definition |
|------|-----------|
| Premature classification | Producing a classification before enough information exists to support it. |
| Required-question recall | Fraction of currently required observations that the model appropriately requests. |
| Unnecessary-question rate | Degree to which the model asks for observations that are already known or not currently decision-relevant. |
| Trajectory completion | Successfully gathering the necessary information and reaching the correct terminal classification/actions without inappropriate early stopping. |
| Structured diagnostic | An evaluation mode using structured representations to make particular competencies easier to score objectively; it is not necessarily the intended user interface. |
| Natural-language evaluation | The primary user-facing evaluation in which EdgeIMCI receives and produces natural language. |
| External benchmark | An independently constructed evaluation such as Lundin et al., kept separate from EdgeIMCI's internally generated benchmarks. |
