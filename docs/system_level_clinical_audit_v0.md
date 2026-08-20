# `imci-selected-v0` system-level clinical substrate audit

**Audit date:** 2026-08-20  
**Scope:** The frozen 15-rule EdgeIMCI machine-readable rule set derived from the WHO *Integrated Management of Childhood Illness, Chart Booklet*, March 2014. This is not a WHO-authored machine-readable rule set and is not complete IMCI.  
**Population:** `2 <= age_months < 60`.  
**Selected areas:** five general danger-sign rules, two fast-breathing derived-finding rules, five respiratory classification rules, and three dehydration classification rules.

## Conclusion

Within its declared complete/static-case contract, the 15 rules behave coherently when executed together. Mechanical tests confirmed age and respiratory-rate boundaries, severity precedence, conservative unknown handling, simultaneous danger-sign firing, diazepam preservation, derived-finding consumption, cross-pathway dehydration action selection, and action aggregation. No selected-scope implementation bug was found. No frozen clinical rule, evaluator behavior, information-policy semantic, trajectory schema semantic, corpus logic, SFT artifact, model weight, or benchmark oracle output was changed.

`imci-selected-v0` is safe to continue using as the clinical substrate for the upcoming information-policy implementation and very small golden conversion slice, subject to all of these boundaries:

- inputs to the frozen evaluator are complete/static cases under its existing evidence-validity assumptions;
- unknown remains distinct from known absent;
- the information-policy layer must preserve the recorded `IP-CQ-*` unresolved states rather than infer clinical semantics;
- the result must not be described as complete IMCI or as the complete respiratory/diarrhoea algorithm.

## Audit results

| Audit ID | Rules involved | Expected combined behaviour | Executable test(s) | Actual behaviour | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| AGE-001 | Population gate; both `IMCI-RESP-FAST-BREATHING-*` rules | Ages 2 and 59 are supported; ages 1 and 60 are rejected; age 11 uses the younger threshold and age 12 uses the older threshold. | `test_respiratory_thresholds_at_supported_age_bounds`; `test_threshold_changes_exactly_at_twelve_months`; `test_age_outside_selected_scope_is_rejected` | Boundaries are exactly `2 <= age < 12` and `12 <= age < 60`; out-of-scope ages raise `ValueError`. | PASS | Preserves the approved integer-month semantics. |
| RESP-THRESH-001 | Both fast-breathing rules; `IMCI-RESP-PNEUMONIA-FAST-BREATHING`; cough/cold fallback | Younger: RR 49 is below and 50 is at cutoff. Older: RR 39 is below and 40 is at cutoff. | `test_respiratory_thresholds_at_supported_age_bounds` | Below-cutoff cases classify `COUGH_OR_COLD`; at-cutoff cases classify `PNEUMONIA`. | PASS | Exact inclusive `gte` thresholds confirmed at lower and upper supported ages. |
| RESP-PRIORITY-001 | Respiratory priorities 1–5 | Severe respiratory predicates dominate pneumonia; pneumonia dominates fallback. | `test_severe_respiratory_classification_dominates_pneumonia_predicates`; `test_pneumonia_dominates_cough_or_cold_fallback` | Only the highest-priority respiratory classification rule is recorded and its action block is selected. | PASS | Existing danger-sign-over-stridor ordering remains priority 1 over priority 2. |
| DEHYD-PRIORITY-001 | All three dehydration rules | Severe dominates simultaneously satisfiable some-dehydration predicates; some dominates no-dehydration fallback. | `test_severe_dehydration_dominates_simultaneously_satisfied_some_dehydration`; `test_some_dehydration_dominates_no_dehydration_fallback` | Evaluator checks severe, then some, then fallback and records only the selected classification rule. | PASS | Count uncertainty capable of changing a higher-priority result blocks lower classification. |
| UNKNOWN-001 | Respiratory and dehydration fallback rules | Missing observations must not be converted to negative evidence or trigger fallback when a valid completion could change classification. | `test_missing_information_does_not_trigger_fallback_classifications` | No respiratory/dehydration classification is emitted; the decision-relevant missing field is reported. | PASS | A missing field that cannot mathematically change either dehydration count may still permit invariant fallback; that is outcome invariance, not unknown-as-negative. |
| GDS-MULTI-001 | All five danger-sign rules, especially unable-to-drink and convulsing-now | Multiple danger signs may fire together even though they share `VERY_SEVERE_DISEASE`. | `test_multiple_general_danger_sign_rules_fire_together` | Both detected signs and both rule IDs are retained. | PASS | Classification is pathway-level; the sign and rule inventories remain multi-valued. |
| GDS-ACTION-001 | `IMCI-GDS-UNABLE-TO-DRINK`; `IMCI-GDS-CONVULSING-NOW` | Shared classification/action values must not erase convulsing-now diazepam. | `test_convulsing_now_preserves_diazepam_with_shared_severe_classification` | Diazepam remains in the unioned action set and both provider rules remain in the trace. | PASS | Action values are de-duplicated, not rule firings. |
| DERIVED-001 | Both fast-breathing rules; `IMCI-RESP-PNEUMONIA-FAST-BREATHING` | Threshold rules produce only `fast_breathing=true`; the downstream classification rule consumes that predicate. | `test_fast_breathing_is_derived_then_consumed_by_pneumonia_rule` | Threshold artifact has no classification; evaluator records threshold and pneumonia rule IDs and emits only `PNEUMONIA`. | PASS | Derived state is internal and traceable through the threshold rule ID; it is not a standalone clinical classification. |
| CROSS-001 | Severe/some dehydration action branches; general danger and severe respiratory classifications | `other_severe_classification` changes the dehydration action branch without changing dehydration classification. | `test_other_severe_classification_changes_dehydration_actions_not_classification` | The same `SEVERE_DEHYDRATION` state selects Plan C alone without another severe classification, but referral/ORS/breastfeeding with severe respiratory classification. | PASS | `evaluate_case` computes the dependency as any detected general danger sign or respiratory `SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE`, then selects `actions_with_*` versus `actions_without_*`. |
| ACTION-AGG-001 | Two GDS rules, severe respiratory danger-sign rule, some-dehydration referral branch | Every selected-scope provider contributes its distinct required actions. | `test_selected_scope_action_aggregation_preserves_every_provider` | Exact nine-action union includes danger care, diazepam, antibiotic, urgent referral, ORS sips, and breastfeeding; all four provider rule IDs remain. | PASS | Duplicate action values are intentionally emitted once. Provider linkage is recoverable from fired rule IDs plus the canonical rule artifact. |
| REASSESS-001 | All 15 rules | Identify any selected behavior requiring intervention followed by reassessment before classification. | Artifact/evaluator inspection; DERIVED-001 | None of the 15 rules has an intervention→reassessment→classification transition. Fast breathing is observation→derived finding→classification. | PASS | Follow-up actions are emitted instructions, not a follow-up-visit evaluator workflow. |
| SCOPE-DOC-001 | Repository scope/provenance wording | Describe an EdgeIMCI machine-readable rule set derived from the WHO chart and avoid complete-IMCI claims. | Regenerated crosscheck artifacts; full suite | README, source notes, glossary, crosscheck generator, Markdown, and PDF now use bounded/provenance-correct language. | DOCUMENTATION_ONLY | Canonical clinical content was not changed. |
| REP-VALIDITY-001 | Respiratory observations; `IP-CQ-003` | Validity of calm-state/one-minute respiratory evidence must not be invented. | Proposal/schema/evaluator inspection | Frozen `ClinicalCase`/evaluator assumes supplied values meet the benchmark evidence contract; trajectory schema can record validity, but the minimum acceptable evidence contract remains unresolved. | REPRESENTATION_GAP | Medium impact for future interaction data; non-blocking for complete valid benchmark cases. Requires expert/source review, not a rule edit. |
| REP-DRINKING-001 | Unable-to-drink danger sign; dehydration drinking status; `IP-CQ-002` | Do not silently reuse evidence across distinct acquisition procedures. | Proposal/schema/evaluator inspection | Fields remain separate; explicit contradiction is rejected, but neither field is inferred from the other. | REPRESENTATION_GAP | Medium interaction-policy impact; no current complete-case evaluator bug. Requires expert/source review. |
| REP-ACTION-PRESENT-001 | No-dehydration actions plus unrelated urgent classification; `IP-CQ-004` | Preserve all configured actions pending a reviewed presentation/ordering policy. | `test_selected_scope_action_aggregation_preserves_every_provider`; proposal inspection | Evaluator unions action blocks and does not suppress home-care actions when another pathway refers urgently. | REPRESENTATION_GAP | Action preservation passes; conversational ordering/suppression remains unresolved. Do not suppress an encoded action by assumption. |

## Selected-scope classification/action provider map

| Classification / condition | Expected selected-scope actions | Providing rule(s) / mechanism |
| --- | --- | --- |
| Any one general danger sign | `COMPLETE_ASSESSMENT_QUICKLY`, `GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY`, `PREVENT_LOW_BLOOD_SUGAR`, `KEEP_WARM`, `URGENT_REFERRAL` | Each firing `IMCI-GDS-*` rule directly contains this action block. |
| `convulsing_now=true` | General danger-sign block plus `GIVE_DIAZEPAM_IF_CONVULSING_NOW` | `IMCI-GDS-CONVULSING-NOW` directly provides diazepam; aggregation preserves it alongside other danger rules. |
| Respiratory `SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE` | `GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC`, `URGENT_REFERRAL` | `IMCI-RESP-SEVERE-DANGER-SIGN` or `IMCI-RESP-SEVERE-STRIDOR`; any separately firing GDS rules also contribute their actions. |
| Respiratory `PNEUMONIA` | `GIVE_ORAL_AMOXICILLIN_5_DAYS`, `SOOTHE_THROAT_AND_RELIEVE_COUGH`, `ADVISE_WHEN_TO_RETURN_IMMEDIATELY`, `FOLLOW_UP_3_DAYS` | Highest-priority firing rule among `IMCI-RESP-PNEUMONIA-CHEST-INDRAWING` and `IMCI-RESP-PNEUMONIA-FAST-BREATHING`. |
| Respiratory `COUGH_OR_COLD` | `SOOTHE_THROAT_AND_RELIEVE_COUGH`, `ADVISE_WHEN_TO_RETURN_IMMEDIATELY`, `FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING` | `IMCI-RESP-COUGH-OR-COLD` fallback after severe and pneumonia are excluded. |
| `SEVERE_DEHYDRATION`, no other severe classification | `GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C` | `IMCI-DIARRHOEA-SEVERE-DEHYDRATION.actions_without_other_severe_classification`; selected by evaluator branch. |
| `SEVERE_DEHYDRATION`, with another severe classification | `URGENT_REFERRAL`, `FREQUENT_ORS_SIPS_DURING_REFERRAL`, `CONTINUE_BREASTFEEDING` | Same rule's `actions_with_other_severe_classification`; selected by evaluator branch. |
| `SOME_DEHYDRATION`, no other severe classification | `GIVE_FLUID_ZINC_AND_FOOD_PLAN_B`, `ADVISE_WHEN_TO_RETURN_IMMEDIATELY`, `FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING` | `IMCI-DIARRHOEA-SOME-DEHYDRATION.actions_without_other_severe_classification`; selected by evaluator branch. |
| `SOME_DEHYDRATION`, with another severe classification | `URGENT_REFERRAL`, `FREQUENT_ORS_SIPS_DURING_REFERRAL`, `CONTINUE_BREASTFEEDING` | Same rule's `actions_with_other_severe_classification`; selected by evaluator branch. |
| `NO_DEHYDRATION` | `GIVE_FLUID_ZINC_AND_FOOD_PLAN_A`, `ADVISE_WHEN_TO_RETURN_IMMEDIATELY`, `FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING` | `IMCI-DIARRHOEA-NO-DEHYDRATION` directly provides an unconditional action block; cross-pathway action presentation remains `IP-CQ-004`. |

No selected-scope action depends on an unrepresented separate clinical rule. The only cross-rule action mechanism is the explicit dehydration `other_severe_classification` branch described above.

## Findings by requested category

### Confirmed passes

- Exact age and respiratory thresholds, including ages 2, 11, 12, and 59 and rates immediately below/at both cutoffs.
- Respiratory and dehydration severity precedence.
- Conservative handling of decision-relevant unknowns.
- Simultaneous danger-sign detection/rule trace and preservation of convulsing-now diazepam.
- Fast breathing as a derived finding rather than a classification.
- Cross-pathway dehydration action branching with unchanged dehydration classification.
- Exact selected-scope action aggregation and provider trace.
- Frozen 82-case oracle identity.

### Implementation bugs

None found.

### Representation gaps / unresolved selected-scope dependencies

- `IP-CQ-003`: acceptable respiratory evidence-validity contract.
- `IP-CQ-002`: whether evidence may be reused between the two drinking assessments.
- `IP-CQ-004`: conversational ordering or suppression of home-care actions alongside urgent referral.
- `IP-CQ-001`: operational sequencing of immediate urgent action and rapid continued supported assessment. The trajectory schema can represent simultaneous action and acquisition, but policy must not invent the sequence.

These are not corrections to frozen clinical semantics. They require expert/source or interaction-policy review as already recorded.

### Known out of scope

The following are `KNOWN_OUT_OF_SCOPE_DEPENDENCY`, not selected-scope implementation bugs:

- wheeze/rapid-acting bronchodilator intervention and reassessment;
- prolonged cough and recurrent wheeze handling;
- HIV-specific chest-indrawing handling;
- persistent diarrhoea;
- dysentery;
- cholera treatment;
- oxygen-saturation handling;
- unavailable-referral behavior;
- follow-up-visit workflow and other IMCI main symptoms.

## Verification record

- Existing tests: **94 passed** as part of the full repository run.
- New system-level audit tests: **21 passed** (`tests/test_system_level_clinical_audit.py`).
- 82-case oracle regression: **PASS**; `test_yaml_mirror_preserves_all_committed_benchmark_oracle_outputs` recomputed all 82 and found every output identical.
- Full repository status: **115 passed** (`python -m pytest -q`).
- Review artifacts regenerated: 15 rule rows and 82 case rows; provenance/scope wording updated in Markdown and PDF outputs.
