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
