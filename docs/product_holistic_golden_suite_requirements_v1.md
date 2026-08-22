# Product-level holistic golden suite — requirements v1

**Status:** Definition approved for construction against `imci-major-sick-child-review-decisions-v1`. The suite has not yet been constructed; this is hackathon-scope approval, not production clinical authorization.

## Relationship to the existing golden slice

The archived 14-case `LEGACY_SELECTED_V0_COMPONENT_REGRESSION` remains fixed under `data/archive/selected_v0/` for selected-v0 component regression and historical reproduction only.

It is not the product-level golden suite for holistic v2 behavior. It is mechanically ineligible for holistic generation, product evaluation, teacher selection, and training. Existing v1 cases that emit an early classification while assessment is incomplete must not be reused as affirmative v2 product targets. The future suite must use `corpus_role=HOLISTIC_PRODUCT_GOLDEN` and pin the major-sick-child rule, policy, oracle, and review-decision identifiers.

## Pinned prerequisites

The future suite must pin approved versions of:

```text
clinical rule set
holistic completeness policy
whole-encounter schema
integrated action-synthesis oracle
clinical-question disposition set
```

The pinned hackathon-scope substrate is `imci-major-sick-child-v1` with `imci-major-sick-child-holistic-completeness-v2` and `imci-major-sick-child-review-decisions-v1`. The recorded domain/policy gate is satisfied for construction of the holistic golden suite; production clinical authorization remains outside this approval.

## Required semantic families

The reviewed suite should include at least:

- a complete low-severity whole encounter;
- one complete encounter for each classification family;
- multiple simultaneous classifications across assessment areas;
- an integrated management plan with deduplicated shared actions;
- each identified cross-pathway treatment interaction;
- urgent/severe findings;
- exact age, duration, respiratory-rate, temperature, and ear-discharge boundaries;
- systematic single and multiple omissions;
- explicit negative versus omission twins;
- an incomplete encounter without a known urgent finding;
- an incomplete encounter with a known urgent finding;
- grouped missing-elements output;
- contradiction and ambiguity cases;
- bronchodilator intervention/reassessment;
- Plan B and Plan C intervention/reassessment;
- a complete post-reassessment encounter;
- malaria-risk and test-availability branches;
- measles with simultaneous respiratory/diarrhoea/ear classifications;
- out-of-scope cases that must not receive unsupported synthesis.

## Target behavior

```text
COMPLETE
→ final integrated classifications and management synthesis

INCOMPLETE, no urgent finding
→ grouped missing elements
→ no final holistic synthesis

INCOMPLETE, known urgent finding
→ immediate source-backed urgent/pre-referral actions
→ explicit incomplete status and remaining assessment
→ no final holistic synthesis
```

## Review gates

Every semantic case must pass:

1. deterministic schema validation;
2. exact recomputation by the approved completeness and clinical oracle;
3. rule/action trace validation;
4. source-provenance review;
5. domain-expert semantic approval;
6. explicit confirmation that omitted findings remain unknown.

Only after semantic approval should language renderings be produced and reviewed. Teacher selection, prompt bake-offs, bulk generation, splits, and SFT remain later stages.
