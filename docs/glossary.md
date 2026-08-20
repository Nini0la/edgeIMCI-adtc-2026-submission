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
