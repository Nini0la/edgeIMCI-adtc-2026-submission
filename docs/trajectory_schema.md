# EdgeIMCI trajectory schema v1

**Status:** Typed representation for future golden-slice and corpus work. This layer does not generate training data, implement the information-policy evaluator, or change `imci-selected-v0`.

The implementation is `src/edge_imci/schemas/trajectory.py`. It is separate from the frozen `ClinicalCase` benchmark schema.

## Four non-interchangeable layers

### 1. Latent truth

`LatentClinicalCase` contains the complete machine-readable observation catalog, the frozen oracle result for an in-scope case, and source provenance. Latent values are ground truth even when they are never shown in a conversation.

A latent case is complete: all 15 supported observation IDs have concrete values. In-scope latent cases require an oracle result with no missing observations. Out-of-scope latent cases carry no clinical oracle result.

### 2. Current known state

`PartialCaseState` contains one `ObservationEvidence` record for every supported observation ID. An omitted/unacquired value is materialized as `KnowledgeState.UNKNOWN`; it is never defaulted to negative.

Each acquired record preserves:

- observation ID and typed value;
- whether acquisition occurred;
- approved acquisition mode;
- knowledge state;
- evidence-validity status and method metadata;
- evidence/policy provenance.

Known values require `VALID` evidence. Acquired evidence with unresolved or invalid validity remains `UNKNOWN`, even when its reported or measured value is retained for audit.

The approved explicit contradictions are rejected: lethargic/unconscious cannot coexist with restless/irritable, and an explicitly negative unable-to-drink danger sign cannot coexist with `drinking_status=UNABLE`. No value is propagated between the drinking fields.

### 3. Model-visible interaction

Every `ConversationTurn` owns a `ModelVisibleMessage` containing only `role` and natural-language `content`. `TrajectoryInteraction.model_visible_messages()` and `prompt_before_assistant()` return only those role/content pairs. They cannot serialize `latent_truth`, partial-state records, policy labels, or expected semantics into a prompt.

Structured observations revealed by a user/worker turn are stored beside the visible message for audit. `ClinicalTrajectory` verifies that acquired state cannot appear before a corresponding reveal and that a known revealed value agrees with latent truth. Hidden latent observations are not automatically visible.

Free-form text can still state a fact that its structured reveal metadata omits. Detecting that semantic mismatch requires the planned renderer/extractor round-trip gate; a typed schema cannot infer the meaning of arbitrary prose.

### 4. Expected assistant semantics

Every assistant natural-language target must carry `ExpectedAssistantSemantics` beside it. The structured target separately records:

- behavior flags;
- scope and decision status;
- classifications and possible classifications;
- referral and source-backed actions;
- decision, action-set, exact-rule, and assessment sufficiency;
- urgent-action state;
- both acquisition channels;
- possible fired rules, blocked observations, and unresolved questions.

Behavior is represented with combinable flags rather than one mutually exclusive response type. For example, one turn may simultaneously contain `EMIT_URGENT_ACTION`, `EMIT_ACTIONS`, and `REQUEST_INFORMATION` while `assessment_complete=false`.

## Acquisition requests

`AcquisitionRequest` preserves the observation ID, acquisition mode, reason, priority band/order, decision-effect flags, and provenance. The schema enforces the approved observation-to-mode catalog, so a caregiver report cannot be stored as a respiratory-rate measurement.

`InformationPolicyResult` and assistant semantics retain disjoint channels:

- `decision_directed_acquisitions` may change classification, actions, or urgency;
- `assessment_completion_acquisitions` use `ASSESSMENT_COMPLETION_ONLY` and carry no decision-changing flags.

An observation cannot appear in both channels at one evaluation step.

## Turns and state transitions

A trajectory has any number of ordered turns and one or more immutable partial-state snapshots. Each turn references the state after that turn. A user/worker turn may reveal newly acquired evidence; the next state can then carry a newly computed policy result. An assistant turn carries its natural-language target and structured semantics.

- Complete single-turn trajectory: user turn, sufficient state, terminal assistant target.
- Incomplete single-turn trajectory: user turn, insufficient state, acquisition-request target, no terminal state.
- Multi-turn trajectory: repeated reveal → recompute → assistant-target transitions, ending in a terminal state when appropriate.

Known evidence cannot regress to unknown or change value in a later state. Invalid/unresolved evidence may be reacquired and become valid.

## Reproducibility and leakage identity

`TrajectoryMetadata` records:

- trajectory schema version;
- frozen rule-set ID;
- information-policy ID;
- valid-completion constraint-set ID;
- generator version and seed;
- rule family and logic signature;
- template family;
- counterfactual group;
- optional split-group IDs;
- corpus role.

This schema does not create a final split. The metadata only provides the identities needed by later group-aware splitting and leakage checks.

## Illustrative fixtures

Two committed JSON fixtures validate the representation:

- `data/fixtures/trajectories/complete_case_v1.json`
- `data/fixtures/trajectories/multi_turn_case_v1.json`

Both use `corpus_role=ILLUSTRATIVE_FIXTURE`. They are schema examples only: **not training data, not a golden slice, and not final benchmark data**.

## Policy dependencies and unresolved questions

No new contradiction requiring a change to the approved information-policy design was found. The schema deliberately does not resolve the existing open questions:

- `IP-CQ-001`: simultaneous urgent-action and incomplete-assessment states are representable, but the schema does not choose rapid-assessment sequencing.
- `IP-CQ-002`: the two drinking observations remain separate; only the approved explicit contradiction is rejected, with no inference or completion pruning.
- `IP-CQ-003`: calm state, one-minute count, and an `UNRESOLVED` validity status are representable. The schema does not define the minimum evidence contract that makes a respiratory observation valid.
- `IP-CQ-004`: all source-backed action blocks can be preserved simultaneously, but the schema does not choose their conversational ordering or suppression.

One implementation dependency remains: the repository does not yet contain the canonical machine-readable information-policy/constraint artifacts or a policy evaluator. Trajectory records can pin their approved IDs and represent their results, but future golden-slice generation must obtain those results from the tested policy implementation rather than hand-authoring them as the illustrative fixtures do.
