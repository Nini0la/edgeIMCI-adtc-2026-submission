# EdgeIMCI information policy v1

**Status:** Implemented and tested deterministic execution layer for `imci-selected-v0`. It does not add clinical rules, generate a golden slice, or represent complete IMCI.

## Two separate evaluators

The frozen clinical evaluator answers:

```text
What does this complete, in-scope case classify as,
and which selected-scope actions fire?
```

The information-policy evaluator answers:

```text
Given only the observations validly known now,
which classifications/actions are already invariant,
is urgent action already supported,
and what should be acquired next?
```

`src/edge_imci/information_policy/evaluator.py` implements the second question by generating valid completions of `UNKNOWN` observations and passing every in-scope completion to the unchanged `evaluate_case` clinical evaluator. It compares classification, action, urgent-action, and fired-rule projections. It never obtains a clinical result by copying rule predicates into a second engine.

## Canonical artifacts

Two independently versioned JSON files are canonical:

- `configs/information_policy/imci_selected_v0_information_policy_v1.json`
  - `policy_id`: `imci-selected-v0-information-policy-v1`
  - pins `rule_set_id=imci-selected-v0`
  - pins `constraint_set_id=imci-selected-v0-valid-completions-v1`
- `configs/information_policy/imci_selected_v0_valid_completions_v1.json`
  - `constraint_set_id`: `imci-selected-v0-valid-completions-v1`
  - pins `rule_set_id=imci-selected-v0`

Their `.yaml` files are deterministic review mirrors. Regenerate them after editing canonical JSON:

```bash
PYTHONPATH=src python scripts/sync_information_policy.py
```

`src/edge_imci/information_policy/artifacts.py` rejects identity drift, rule-set/constraint-set pin drift, an incomplete or reordered observation catalog, acquisition-mode disagreement with the trajectory schema, unknown source rule IDs, non-deterministic scheduler settings, a changed unresolved-question set, or incorrect constraint enforcement modes. Tests require each YAML mirror to deserialize exactly to its canonical JSON and match deterministic regeneration byte for byte.

## Runtime API

```python
from edge_imci.information_policy import evaluate_information_policy

policy_result = evaluate_information_policy(partial_case_state)
```

`PartialCaseState.policy_result` may contain the result from the previous turn or an initial construction result. The evaluator ignores that embedded result, reads only the observation evidence, and returns a newly computed `InformationPolicyResult`. A trajectory generator should attach this returned result to the next immutable state snapshot.

After every newly acquired observation:

1. create the next `PartialCaseState` observation snapshot;
2. call `evaluate_information_policy` again;
3. store the returned `InformationPolicyResult` on that snapshot;
4. derive `ExpectedAssistantSemantics` from that structured result;
5. render natural language without exposing latent observations or policy labels.

No policy result should be hand-authored for the archived selected-v0 component regression slice.

## Valid completions

V1 implements every constraint in `imci-selected-v0-valid-completions-v1` according to its declared enforcement mode:

- boolean and enum domains are explicit;
- unknown age branches to representative younger, older, and out-of-scope states;
- unknown respiratory rate uses representative values for every age-specific below/at-or-above threshold partition;
- pathway-entry observations control whether respiratory/dehydration fields are active;
- `lethargic_or_unconscious=true` plus `restless_or_irritable=true` is pruned by `VC-COHERENCE-001`;
- the two drinking observations remain separate;
- unknown is never defaulted to false;
- invalid or unresolved acquired evidence remains unknown.

`VC-COHERENCE-002` is intentionally input-validation-only. `PartialCaseState` rejects the explicitly supplied contradictory drinking pair. During hypothetical completion, the evaluator neither infers one field from the other nor prunes a candidate solely under that input-only rule. The isolated completion adapter bypasses only the complete-case schema's explicit-input check so the approved completion semantics can be evaluated by the frozen clinical evaluator. `IP-CQ-002` remains exposed whenever one drinking observation is known and the other remains unknown.

The finite representative domains are exhaustive over the distinctions used by the frozen selected-scope evaluator. They do not approximate an information-gain score or alter a clinical threshold.

## Sufficiency and exact-rule projection

For each pathway, the evaluator returns:

- `possible_classifications`;
- `decision_status`;
- `action_set_sufficient`;
- `exact_rule_sufficient` and `possible_fired_rule_ids`;
- `assessment_complete`.

Decision sufficiency and action-set sufficiency use outcome invariance. Assessment completeness instead checks whether every observation designated for the active supported assessment was acquired with `VALID` evidence. Consequently these are valid states:

```text
DECISION_SUFFICIENT = true
ASSESSMENT_COMPLETE = false
```

and:

```text
classification fixed
exact fired respiratory rule unresolved
actions fixed
```

The second state implements approved `IP-RQ-001`, including fast breathing with chest indrawing unknown: both completions produce the same `PNEUMONIA` classification and respiratory actions, while the possible classification-rule IDs remain distinct.

Dehydration action projections retain the frozen evaluator's `other_severe_classification` dependency. A fixed dehydration classification may therefore have `action_set_sufficient=false` until danger-sign and severe-respiratory possibilities are resolved.

## Urgent actions and acquisition channels

`known_actions` is the intersection of action sets across every valid completion. `possible_additional_actions` is the union minus that intersection. Known urgent or immediate actions are surfaced without waiting for assessment completion.

The evaluator keeps two disjoint channels:

- `decision_directed_acquisitions`: the next deterministic scheduler batch that can change classification/actions or add urgent/immediate action;
- `assessment_completion_acquisitions`: active supported-assessment observations that cannot change the current decision projection.

The next decision batch is sorted by fixed priority band and canonical observation order, then restricted to the first band's first acquisition mode. This preserves caregiver questions, clinician observations, measurements, and history/record acquisition as distinct operations. The evaluator is recomputed before any lower-priority batch is selected.

No information-gain scoring, learned ordering, adaptive optimization, or stochastic scheduling is present.

## Unresolved questions

All four approved unresolved questions remain unresolved:

- `IP-CQ-001`: immediate urgent action versus rapid continued-assessment sequencing;
- `IP-CQ-002`: reuse of evidence between the two drinking assessments;
- `IP-CQ-003`: minimum valid evidence contract for calm respiratory assessment;
- `IP-CQ-004`: presentation ordering of home-care actions alongside unrelated urgent referral.

An acquired respiratory observation with `UNRESOLVED` validity and `IP-CQ-003` remains unknown. If it can change the current decision, the relevant pathway and supported encounter return `BLOCKED`; the evaluator does not classify from its retained raw value. Other `IP-CQ` IDs are retained when their approved ambiguity is present without suppressing source-backed actions or inferring observations.

## Scope and non-goals

The supported encounter means only general danger signs, the selected respiratory classifications, and dehydration classification for ages 2–59 months. The information-policy layer itself does not:

- modify the 15 frozen clinical rules or their evaluator;
- modify the 82 committed oracle outputs;
- add an IMCI pathway;
- resolve `IP-CQ-001` through `IP-CQ-004`;
- implement wheeze/bronchodilator reassessment or other known out-of-scope dependencies;
- generate or render trajectories, paraphrases, or SFT data;
- train or modify a model.

## Golden-slice handoff

The executable handoff is:

```text
PartialCaseState
      ↓
evaluate_information_policy
      ↓
InformationPolicyResult
  - pathway decision/action sufficiency
  - urgent-action state
  - next decision-directed batch
  - assessment-completion queue
      ↓
ExpectedAssistantSemantics / trajectory schema
```

The archived 14-record selected-v0 component slice implements this historical handoff in `data/archive/selected_v0/golden/golden_conversion_slice_v1.jsonl`. Every state is recomputed with this evaluator, both artifact IDs are pinned in trajectory metadata, controlled-language round-trip results are recorded, and `docs/golden_slice_review_v1.md` preserves the historical human/domain-expert review surface. It is not eligible for holistic generation, product evaluation, teacher selection, or training.
