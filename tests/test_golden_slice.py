from __future__ import annotations

import json
from pathlib import Path

import pytest

from edge_imci.generation.golden import (
    DEFAULT_GOLDEN_PATH,
    DEFAULT_REVIEW_PATH,
    ConservativeGoldenRenderer,
    generate_golden_slice,
    load_golden_slice,
)
from edge_imci.information_policy import evaluate_information_policy_observations
from edge_imci.schemas.case import Action, Classification, DangerSign, DrinkingStatus, Pathway
from edge_imci.schemas.trajectory import (
    AssistantBehavior,
    ClinicalTrajectory,
    ConversationRole,
    CorpusRole,
    DecisionStatus,
    KnowledgeState,
    ObservationEvidence,
    ObservationId,
    ScopeStatus,
)


@pytest.fixture(scope="module")
def golden_records():
    return generate_golden_slice()


def _by_id(records):
    return {record.golden_case_id: record for record in records}


def _assistant_turns(record):
    return [
        turn
        for turn in record.trajectory.interaction.turns
        if turn.visible_message.role is ConversationRole.ASSISTANT
    ]


def _final_semantics(record):
    return _assistant_turns(record)[-1].expected_assistant_semantics


def _state_before_final_assistant(record):
    turn = _assistant_turns(record)[-1]
    return next(item for item in record.trajectory.states if item.state_id == turn.state_after_turn_id)


def test_slice_is_tiny_explicit_and_not_training_data(golden_records) -> None:
    assert 12 <= len(golden_records) <= 16
    assert len(golden_records) < 20
    assert len({record.golden_case_id for record in golden_records}) == len(golden_records)
    assert all(record.trajectory.metadata.corpus_role is CorpusRole.GOLDEN_CONVERSION_SLICE for record in golden_records)
    assert all("HUMAN_REVIEW_REQUIRED" in record.review_flags for record in golden_records)
    assert not (Path("data") / "train").exists()
    assert not (Path("data") / "validation").exists()


def test_generation_is_reproducible_and_committed_jsonl_matches(golden_records) -> None:
    first = [record.to_dict() for record in golden_records]
    second = [record.to_dict() for record in generate_golden_slice()]
    assert first == second
    assert load_golden_slice(DEFAULT_GOLDEN_PATH) == first


def test_every_record_round_trips_through_trajectory_schema(golden_records) -> None:
    for record in golden_records:
        trajectory = record.trajectory
        assert ClinicalTrajectory.from_json(trajectory.to_json()).to_dict() == trajectory.to_dict()


def test_latent_information_does_not_enter_model_visible_state_or_text(golden_records) -> None:
    renderer = ConservativeGoldenRenderer()
    for record in golden_records:
        revealed: set[ObservationId] = set()
        state_by_id = {state.state_id: state for state in record.trajectory.states}
        for turn in record.trajectory.interaction.turns:
            if turn.visible_message.role is ConversationRole.USER:
                assert turn.visible_message.content == renderer.render_reveal(turn.revealed_observations)
                revealed.update(item.observation_id for item in turn.revealed_observations)
            else:
                semantics = turn.expected_assistant_semantics
                assert semantics is not None
                assert turn.visible_message.content == renderer.render_assistant_target(semantics)
                assert "latent-" not in turn.visible_message.content
                assert "IMCI-" not in turn.visible_message.content
            visible_ids = {
                item.observation_id
                for item in state_by_id[turn.state_after_turn_id].observations
                if item.acquired
            }
            assert visible_ids == revealed


def test_every_state_recomputes_the_canonical_information_policy(golden_records) -> None:
    for record in golden_records:
        for state in record.trajectory.states:
            recomputed = evaluate_information_policy_observations(state.observations)
            assert recomputed.to_dict() == state.policy_result.to_dict()


def test_structured_targets_match_policy_outputs(golden_records) -> None:
    for record in golden_records:
        state_by_id = {state.state_id: state for state in record.trajectory.states}
        for turn in _assistant_turns(record):
            semantics = turn.expected_assistant_semantics
            assert semantics is not None
            policy = state_by_id[turn.state_after_turn_id].policy_result
            assert semantics.scope_status is policy.scope_status
            assert semantics.decision_status is policy.supported_encounter_decision_status
            assert semantics.action_set_sufficient is policy.supported_encounter_action_set_sufficient
            assert semantics.assessment_complete is policy.supported_encounter_assessment_complete
            assert semantics.urgent_action_required is policy.urgent_action_required
            assert semantics.actions == policy.known_actions
            assert semantics.decision_directed_acquisitions == policy.decision_directed_acquisitions
            assert semantics.assessment_completion_acquisitions == policy.assessment_completion_acquisitions
            for pathway_state in policy.pathway_states:
                if pathway_state.decision_status is DecisionStatus.SUFFICIENT and len(pathway_state.possible_classifications) == 1:
                    assert semantics.classifications[pathway_state.pathway] is pathway_state.possible_classifications[0]


def test_all_controlled_targets_have_passing_recorded_round_trips(golden_records) -> None:
    validations = [item for record in golden_records for item in record.assistant_target_validations]
    assert len(validations) == 16
    for item in validations:
        result = item.round_trip
        assert result.deterministic_match
        assert result.expected_projection == result.extracted_projection
        assert result.limitations
        assert result.human_review_required is True


def test_round_trip_preserves_acquisition_modes_and_channels(golden_records) -> None:
    renderer = ConservativeGoldenRenderer()
    for record in golden_records:
        for turn in _assistant_turns(record):
            semantics = turn.expected_assistant_semantics
            assert semantics is not None
            validation = next(item.round_trip for item in record.assistant_target_validations if item.turn_index == turn.turn_index)
            fresh = renderer.render_assistant_target(semantics)
            assert fresh == turn.visible_message.content
            assert validation.expected_projection == validation.extracted_projection
            assert all(
                item.split("|")[0] in {"decision", "assessment"}
                and item.split("|")[2] in {"CAREGIVER_QUESTION", "CLINICIAN_OBSERVATION", "MEASUREMENT", "HISTORY_OR_RECORD"}
                for item in validation.extracted_projection["acquisitions"]
            )


def test_unknown_respiratory_rate_stays_unknown_and_is_requested(golden_records) -> None:
    record = _by_id(golden_records)["golden-partial-needs-respiratory-measurement"]
    state = _state_before_final_assistant(record)
    semantics = _final_semantics(record)
    respiratory_rate = next(item for item in state.observations if item.observation_id is ObservationId.RESPIRATORY_RATE)
    assert respiratory_rate.knowledge_state is KnowledgeState.UNKNOWN
    assert respiratory_rate.value is None
    assert semantics is not None
    assert semantics.decision_status is DecisionStatus.INSUFFICIENT
    assert Pathway.RESPIRATORY not in semantics.classifications
    assert [item.observation_id for item in semantics.decision_directed_acquisitions] == [ObservationId.RESPIRATORY_RATE]


def test_age_and_respiratory_threshold_examples_have_expected_oracles(golden_records) -> None:
    records = _by_id(golden_records)
    expected = {
        "golden-age11-rr49-cough-cold": Classification.COUGH_OR_COLD,
        "golden-age11-rr50-pneumonia": Classification.PNEUMONIA,
        "golden-age12-rr39-cough-cold": Classification.COUGH_OR_COLD,
        "golden-multiturn-age12-rr40": Classification.PNEUMONIA,
    }
    for case_id, classification in expected.items():
        assert records[case_id].trajectory.latent_truth.oracle_result.classifications[Pathway.RESPIRATORY] is classification


def test_danger_sign_escalation_is_immediate_and_assessment_can_continue(golden_records) -> None:
    record = _by_id(golden_records)["golden-danger-sign-early-escalation"]
    semantics = _final_semantics(record)
    assert semantics is not None
    assert semantics.decision_status is DecisionStatus.SUFFICIENT
    assert semantics.action_set_sufficient
    assert not semantics.assessment_complete
    assert semantics.urgent_action_required
    assert AssistantBehavior.EMIT_URGENT_ACTION in semantics.behaviors
    assert Action.URGENT_REFERRAL in semantics.actions
    assert semantics.assessment_completion_acquisitions
    assert "UNRESOLVED:IP-CQ-001" in record.review_flags


def test_simultaneous_danger_rules_preserve_trace_and_diazepam(golden_records) -> None:
    record = _by_id(golden_records)["golden-simultaneous-danger-diazepam"]
    semantics = _final_semantics(record)
    state = _state_before_final_assistant(record)
    danger = next(item for item in state.policy_result.pathway_states if item.pathway is Pathway.GENERAL_DANGER_SIGNS)
    assert semantics is not None
    assert set(semantics.detected_danger_signs) == {
        DangerSign.CONVULSING_NOW,
        DangerSign.UNABLE_TO_DRINK_OR_BREASTFEED,
    }
    assert Action.GIVE_DIAZEPAM_IF_CONVULSING_NOW in semantics.actions
    assert danger.exact_rule_sufficient
    assert set(danger.possible_fired_rule_ids) == {
        "IMCI-GDS-CONVULSING-NOW",
        "IMCI-GDS-UNABLE-TO-DRINK",
    }


def test_dehydration_branch_examples_preserve_selected_actions(golden_records) -> None:
    records = _by_id(golden_records)
    plan_c = _final_semantics(records["golden-severe-dehydration-plan-c"])
    cross_severe = _final_semantics(records["golden-dehydration-cross-severe-referral"])
    no_dehydration = _final_semantics(records["golden-no-dehydration-invariant"])
    assert plan_c is not None and cross_severe is not None and no_dehydration is not None
    assert plan_c.classifications[Pathway.DEHYDRATION] is Classification.SEVERE_DEHYDRATION
    assert Action.GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C in plan_c.actions
    assert cross_severe.classifications[Pathway.DEHYDRATION] is Classification.SEVERE_DEHYDRATION
    assert Action.GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C not in cross_severe.actions
    assert Action.FREQUENT_ORS_SIPS_DURING_REFERRAL in cross_severe.actions
    assert Action.CONTINUE_BREASTFEEDING in cross_severe.actions
    assert no_dehydration.classifications[Pathway.DEHYDRATION] is Classification.NO_DEHYDRATION
    assert no_dehydration.decision_status is DecisionStatus.SUFFICIENT
    assert not no_dehydration.assessment_complete
    assert [item.observation_id for item in no_dehydration.assessment_completion_acquisitions] == [ObservationId.DEHYDRATION_SKIN_PINCH]


def test_entry_observations_remain_decision_relevant_after_danger_assessment() -> None:
    evidence = [ObservationEvidence.known(ObservationId.AGE_MONTHS, 18)]
    evidence.extend(ObservationEvidence.known(item, False) for item in (
        ObservationId.DANGER_CONVULSING_NOW,
        ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS,
        ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED,
        ObservationId.DANGER_VOMITS_EVERYTHING,
        ObservationId.DANGER_HAD_CONVULSIONS,
    ))
    result = evaluate_information_policy_observations(evidence)
    assert [item.observation_id for item in result.decision_directed_acquisitions] == [
        ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING,
        ObservationId.HAS_DIARRHOEA,
    ]
    assert result.assessment_completion_acquisitions == ()


def test_ip_cq_002_only_blocks_relevant_cross_assessment_evidence() -> None:
    inactive = evaluate_information_policy_observations((
        ObservationEvidence.known(ObservationId.AGE_MONTHS, 18),
        ObservationEvidence.known(ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED, False),
        ObservationEvidence.known(ObservationId.HAS_DIARRHOEA, False),
    ))
    assert "IP-CQ-002" not in inactive.unresolved_question_ids

    relevant = evaluate_information_policy_observations((
        ObservationEvidence.known(ObservationId.AGE_MONTHS, 18),
        ObservationEvidence.known(ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED, True),
        ObservationEvidence.known(ObservationId.HAS_DIARRHOEA, True),
    ))
    assert "IP-CQ-002" in relevant.unresolved_question_ids


def test_review_package_covers_every_record_and_states_validation_limit(golden_records) -> None:
    review = DEFAULT_REVIEW_PATH.read_text(encoding="utf-8")
    for record in golden_records:
        assert f"### {record.golden_case_id}" in review
    assert "not independent clinical proof" in review
    assert "not training data" in review.lower()
    assert "Domain-expert review" in review


def test_golden_scope_is_in_scope_and_contains_no_blocked_clinical_ambiguity(golden_records) -> None:
    for record in golden_records:
        assert record.trajectory.latent_truth.scope_status is ScopeStatus.IN_SCOPE
        assert all(state.policy_result.scope_status is ScopeStatus.IN_SCOPE for state in record.trajectory.states)
        assert all("UNRESOLVED:IP-CQ-002" not in record.review_flags for record in golden_records)
        for turn in _assistant_turns(record):
            semantics = turn.expected_assistant_semantics
            assert semantics is not None
            assert semantics.decision_status is not DecisionStatus.BLOCKED
            assert semantics.blocked_observation_ids == ()


def test_committed_jsonl_is_canonical_json_lines() -> None:
    lines = DEFAULT_GOLDEN_PATH.read_text(encoding="utf-8").splitlines()
    assert lines
    for line in lines:
        parsed = json.loads(line)
        assert line == json.dumps(parsed, sort_keys=True)
