from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from edge_imci.schemas.case import (
    Action,
    Classification,
    DangerSign,
    DrinkingStatus,
    EvaluationResult,
    Pathway,
    ReferralRequirement,
    SkinPinch,
    SourceProvenance,
)
from edge_imci.schemas.trajectory import (
    TRAJECTORY_SCHEMA_VERSION,
    AcquisitionMode,
    AcquisitionReason,
    AcquisitionRequest,
    AssistantBehavior,
    BasisType,
    ClinicalTrajectory,
    ConversationRole,
    ConversationTurn,
    CorpusRole,
    DecisionStatus,
    EntryStatus,
    EvidenceValidityStatus,
    ExpectedAssistantSemantics,
    InformationPolicyResult,
    KnowledgeState,
    LatentClinicalCase,
    LatentObservation,
    ModelVisibleMessage,
    ObservationEvidence,
    ObservationId,
    ObservationValidity,
    PartialCaseState,
    PathwayPolicyState,
    PolicyProvenance,
    ScopeStatus,
    TrajectoryInteraction,
    TrajectoryMetadata,
    acquisition_mode_for,
)

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures" / "trajectories"
POLICY_ID = "imci-selected-v0-information-policy-v1"
CONSTRAINT_SET_ID = "imci-selected-v0-valid-completions-v1"
RULE_SET_ID = "imci-selected-v0"
DEHYDRATION_RULES = (
    "IMCI-DIARRHOEA-SEVERE-DEHYDRATION",
    "IMCI-DIARRHOEA-SOME-DEHYDRATION",
    "IMCI-DIARRHOEA-NO-DEHYDRATION",
)
FINAL_ACTIONS = (
    Action.GIVE_FLUID_ZINC_AND_FOOD_PLAN_B,
    Action.ADVISE_WHEN_TO_RETURN_IMMEDIATELY,
    Action.FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING,
)

LATENT_VALUES = {
    ObservationId.AGE_MONTHS: 18,
    ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: False,
    ObservationId.HAS_DIARRHOEA: True,
    ObservationId.DANGER_CONVULSING_NOW: False,
    ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS: False,
    ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED: False,
    ObservationId.DANGER_VOMITS_EVERYTHING: False,
    ObservationId.DANGER_HAD_CONVULSIONS: False,
    ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM: False,
    ObservationId.RESPIRATORY_CHEST_INDRAWING: False,
    ObservationId.RESPIRATORY_RATE: 34,
    ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE: False,
    ObservationId.DEHYDRATION_SUNKEN_EYES: True,
    ObservationId.DEHYDRATION_DRINKING_STATUS: DrinkingStatus.EAGER_OR_THIRSTY,
    ObservationId.DEHYDRATION_SKIN_PINCH: SkinPinch.NORMAL,
}

INITIAL_VISIBLE_IDS = (
    ObservationId.AGE_MONTHS,
    ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING,
    ObservationId.HAS_DIARRHOEA,
    ObservationId.DANGER_CONVULSING_NOW,
    ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS,
    ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED,
    ObservationId.DANGER_VOMITS_EVERYTHING,
    ObservationId.DANGER_HAD_CONVULSIONS,
    ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE,
    ObservationId.DEHYDRATION_SUNKEN_EYES,
    ObservationId.DEHYDRATION_SKIN_PINCH,
)


def _policy_provenance(
    *rule_ids: str,
    basis: BasisType = BasisType.INTERACTION_POLICY,
    unresolved_question_ids: tuple[str, ...] = (),
) -> PolicyProvenance:
    return PolicyProvenance(
        basis=basis,
        source_rule_ids=tuple(rule_ids),
        source_pdf_pages=(7,) if rule_ids else (),
        source_printed_pages=("3 of 76",) if rule_ids else (),
        policy_rule_ids=("IP-DEHYD-001",) if rule_ids else ("IP-UNKNOWN-001",),
        unresolved_question_ids=unresolved_question_ids,
    )


def _known(observation_id: ObservationId) -> ObservationEvidence:
    provenance = _policy_provenance(*DEHYDRATION_RULES) if observation_id.value.startswith("dehydration.") else None
    return ObservationEvidence.known(
        observation_id,
        LATENT_VALUES[observation_id],
        provenance=provenance,
    )


def _drinking_request() -> AcquisitionRequest:
    return AcquisitionRequest(
        observation_id=ObservationId.DEHYDRATION_DRINKING_STATUS,
        acquisition_mode=AcquisitionMode.CLINICIAN_OBSERVATION,
        reason=AcquisitionReason.CAN_CHANGE_CLASSIFICATION,
        priority_band=5,
        priority_order=13,
        provenance=_policy_provenance(*DEHYDRATION_RULES),
        can_change_classification=True,
        can_change_actions=True,
    )


def _pathway_states(*, final: bool) -> tuple[PathwayPolicyState, ...]:
    return (
        PathwayPolicyState(
            pathway=Pathway.GENERAL_DANGER_SIGNS,
            entry_status=EntryStatus.ACTIVE,
            possible_classifications=(),
            decision_status=DecisionStatus.SUFFICIENT,
            action_set_sufficient=True,
            exact_rule_sufficient=True,
            possible_fired_rule_ids=(),
            assessment_complete=True,
        ),
        PathwayPolicyState(
            pathway=Pathway.RESPIRATORY,
            entry_status=EntryStatus.NOT_APPLICABLE,
            possible_classifications=(),
            decision_status=DecisionStatus.SUFFICIENT,
            action_set_sufficient=True,
            exact_rule_sufficient=True,
            possible_fired_rule_ids=(),
            assessment_complete=True,
        ),
        PathwayPolicyState(
            pathway=Pathway.DEHYDRATION,
            entry_status=EntryStatus.ACTIVE,
            possible_classifications=(Classification.SOME_DEHYDRATION,) if final else (
                Classification.SEVERE_DEHYDRATION,
                Classification.SOME_DEHYDRATION,
                Classification.NO_DEHYDRATION,
            ),
            decision_status=DecisionStatus.SUFFICIENT if final else DecisionStatus.INSUFFICIENT,
            action_set_sufficient=final,
            exact_rule_sufficient=final,
            possible_fired_rule_ids=("IMCI-DIARRHOEA-SOME-DEHYDRATION",) if final else DEHYDRATION_RULES,
            assessment_complete=final,
        ),
    )


def _policy_result(*, final: bool) -> InformationPolicyResult:
    return InformationPolicyResult(
        policy_id=POLICY_ID,
        constraint_set_id=CONSTRAINT_SET_ID,
        scope_status=ScopeStatus.IN_SCOPE,
        pathway_states=_pathway_states(final=final),
        supported_encounter_decision_status=DecisionStatus.SUFFICIENT if final else DecisionStatus.INSUFFICIENT,
        supported_encounter_action_set_sufficient=final,
        supported_encounter_assessment_complete=final,
        urgent_action_required=False,
        known_actions=FINAL_ACTIONS if final else (),
        decision_directed_acquisitions=() if final else (_drinking_request(),),
        applied_constraint_ids=("VC-SCOPE-001", "VC-ENTRY-001", "VC-UNKNOWN-001"),
    )


def _latent(case_id: str) -> LatentClinicalCase:
    return LatentClinicalCase(
        latent_case_id=case_id,
        observations=tuple(LatentObservation(observation_id, value) for observation_id, value in LATENT_VALUES.items()),
        scope_status=ScopeStatus.IN_SCOPE,
        oracle_result=EvaluationResult(
            classifications={Pathway.DEHYDRATION: Classification.SOME_DEHYDRATION},
            referral=ReferralRequirement.NONE,
            actions=FINAL_ACTIONS,
            fired_rule_ids=("IMCI-DIARRHOEA-SOME-DEHYDRATION",),
        ),
        provenance=SourceProvenance(
            document="WHO Integrated Management of Childhood Illness, Chart Booklet",
            edition="March 2014",
            source_pdf_pages=(5, 7),
            source_printed_pages=("1 of 76", "3 of 76"),
            source_rule_ids=DEHYDRATION_RULES,
        ),
    )


def _partial_state() -> PartialCaseState:
    return PartialCaseState.from_observations(
        "state-incomplete",
        tuple(_known(item) for item in INITIAL_VISIBLE_IDS),
        _policy_result(final=False),
    )


def _final_state() -> PartialCaseState:
    visible_ids = INITIAL_VISIBLE_IDS + (ObservationId.DEHYDRATION_DRINKING_STATUS,)
    return PartialCaseState.from_observations(
        "state-final",
        tuple(_known(item) for item in visible_ids),
        _policy_result(final=True),
    )


def _request_semantics() -> ExpectedAssistantSemantics:
    return ExpectedAssistantSemantics(
        behaviors=(AssistantBehavior.REQUEST_INFORMATION,),
        scope_status=ScopeStatus.IN_SCOPE,
        decision_status=DecisionStatus.INSUFFICIENT,
        action_set_sufficient=False,
        assessment_complete=False,
        urgent_action_required=False,
        exact_rule_sufficient=False,
        possible_classifications={
            Pathway.DEHYDRATION: (
                Classification.SEVERE_DEHYDRATION,
                Classification.SOME_DEHYDRATION,
                Classification.NO_DEHYDRATION,
            )
        },
        possible_fired_rule_ids=DEHYDRATION_RULES,
        decision_directed_acquisitions=(_drinking_request(),),
    )


def _final_semantics() -> ExpectedAssistantSemantics:
    return ExpectedAssistantSemantics(
        behaviors=(
            AssistantBehavior.EMIT_CLASSIFICATION,
            AssistantBehavior.EMIT_ACTIONS,
            AssistantBehavior.REPORT_NOT_APPLICABLE,
        ),
        scope_status=ScopeStatus.IN_SCOPE,
        decision_status=DecisionStatus.SUFFICIENT,
        action_set_sufficient=True,
        assessment_complete=True,
        urgent_action_required=False,
        exact_rule_sufficient=True,
        classifications={Pathway.DEHYDRATION: Classification.SOME_DEHYDRATION},
        possible_classifications={Pathway.DEHYDRATION: (Classification.SOME_DEHYDRATION,)},
        referral=ReferralRequirement.NONE,
        actions=FINAL_ACTIONS,
        possible_fired_rule_ids=("IMCI-DIARRHOEA-SOME-DEHYDRATION",),
        not_applicable_pathways=(Pathway.RESPIRATORY,),
    )


def _metadata(template_family: str) -> TrajectoryMetadata:
    return TrajectoryMetadata(
        schema_version=TRAJECTORY_SCHEMA_VERSION,
        rule_set_id=RULE_SET_ID,
        information_policy_id=POLICY_ID,
        constraint_set_id=CONSTRAINT_SET_ID,
        generator_version="trajectory-fixture-v1",
        generation_seed=20260819,
        rule_family="dehydration",
        logic_signature="illustrative:some-dehydration",
        template_family=template_family,
        corpus_role=CorpusRole.ILLUSTRATIVE_FIXTURE,
        counterfactual_group_id="illustrative-drinking-response",
        split_group_ids=("latent-family:illustrative-some-dehydration",),
    )


def build_complete_fixture() -> ClinicalTrajectory:
    final = _final_state()
    revealed = tuple(_known(item) for item in INITIAL_VISIBLE_IDS + (ObservationId.DEHYDRATION_DRINKING_STATUS,))
    interaction = TrajectoryInteraction(
        turns=(
            ConversationTurn(
                turn_index=0,
                visible_message=ModelVisibleMessage(
                    ConversationRole.USER,
                    "An 18-month-old has diarrhoea and no cough or difficult breathing. All general danger signs are absent. The child is not restless, has sunken eyes, drinks eagerly when offered fluid, and the skin pinch returns normally.",
                ),
                state_after_turn_id=final.state_id,
                revealed_observations=revealed,
            ),
            ConversationTurn(
                turn_index=1,
                visible_message=ModelVisibleMessage(
                    ConversationRole.ASSISTANT,
                    "The supported dehydration classification is some dehydration. Give Plan B fluids, zinc and food; advise when to return immediately; and follow up in 5 days if not improving.",
                ),
                state_after_turn_id=final.state_id,
                expected_assistant_semantics=_final_semantics(),
            ),
        )
    )
    return ClinicalTrajectory(
        trajectory_id="illustrative-complete-dehydration-v1",
        latent_truth=_latent("latent-illustrative-complete-dehydration"),
        states=(final,),
        interaction=interaction,
        initial_state_id=final.state_id,
        terminal_state_id=final.state_id,
        metadata=_metadata("illustrative-complete-single-turn"),
    )


def build_multiturn_fixture() -> ClinicalTrajectory:
    partial = _partial_state()
    final = _final_state()
    interaction = TrajectoryInteraction(
        turns=(
            ConversationTurn(
                turn_index=0,
                visible_message=ModelVisibleMessage(
                    ConversationRole.USER,
                    "An 18-month-old has diarrhoea and no cough or difficult breathing. All general danger signs are absent. The child is not restless, has sunken eyes, and the skin pinch returns normally.",
                ),
                state_after_turn_id=partial.state_id,
                revealed_observations=tuple(_known(item) for item in INITIAL_VISIBLE_IDS),
            ),
            ConversationTurn(
                turn_index=1,
                visible_message=ModelVisibleMessage(
                    ConversationRole.ASSISTANT,
                    "Offer the child fluid and report whether the child drinks normally, eagerly or thirstily, poorly, or is unable to drink.",
                ),
                state_after_turn_id=partial.state_id,
                expected_assistant_semantics=_request_semantics(),
            ),
            ConversationTurn(
                turn_index=2,
                visible_message=ModelVisibleMessage(
                    ConversationRole.USER,
                    "When offered fluid, the child drinks eagerly and appears thirsty.",
                ),
                state_after_turn_id=final.state_id,
                revealed_observations=(_known(ObservationId.DEHYDRATION_DRINKING_STATUS),),
            ),
            ConversationTurn(
                turn_index=3,
                visible_message=ModelVisibleMessage(
                    ConversationRole.ASSISTANT,
                    "The supported dehydration classification is some dehydration. Give Plan B fluids, zinc and food; advise when to return immediately; and follow up in 5 days if not improving.",
                ),
                state_after_turn_id=final.state_id,
                expected_assistant_semantics=_final_semantics(),
            ),
        )
    )
    return ClinicalTrajectory(
        trajectory_id="illustrative-multiturn-dehydration-v1",
        latent_truth=_latent("latent-illustrative-multiturn-dehydration"),
        states=(partial, final),
        interaction=interaction,
        initial_state_id=partial.state_id,
        terminal_state_id=final.state_id,
        metadata=_metadata("illustrative-multiturn-acquisition"),
    )


def _load_fixture(name: str) -> ClinicalTrajectory:
    return ClinicalTrajectory.from_json((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_unknown_observations_remain_unknown():
    state = _partial_state()
    record = state.observation(ObservationId.DEHYDRATION_DRINKING_STATUS)

    assert record.knowledge_state is KnowledgeState.UNKNOWN
    assert record.value is None
    assert not record.acquired
    assert PartialCaseState.from_dict(state.to_dict()) == state


def test_latent_observations_are_not_automatically_model_visible():
    trajectory = build_complete_fixture()
    visible = trajectory.model_visible_messages()
    serialized_visible = json.dumps(visible)

    assert all(set(message) == {"role", "content"} for message in visible)
    assert "respiratory.respiratory_rate" not in serialized_visible
    assert "latent_truth" not in serialized_visible
    assert trajectory.latent_truth.observation(ObservationId.RESPIRATORY_RATE).value == 34


def test_pathway_entry_states_can_be_unknown():
    policy = replace(
        _policy_result(final=False),
        pathway_states=tuple(
            replace(item, entry_status=EntryStatus.UNKNOWN, decision_status=DecisionStatus.INSUFFICIENT)
            if item.pathway in {Pathway.RESPIRATORY, Pathway.DEHYDRATION}
            else item
            for item in _pathway_states(final=False)
        ),
    )
    state = PartialCaseState.from_observations("unknown-entry", (), policy)
    loaded = PartialCaseState.from_dict(state.to_dict())

    assert loaded.observation(ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING).knowledge_state is KnowledgeState.UNKNOWN
    assert loaded.observation(ObservationId.HAS_DIARRHOEA).knowledge_state is KnowledgeState.UNKNOWN


def test_acquisition_mode_is_preserved_and_catalog_enforced():
    request = AcquisitionRequest.from_dict(_drinking_request().to_dict())
    evidence = ObservationEvidence.from_dict(_known(ObservationId.DEHYDRATION_DRINKING_STATUS).to_dict())

    assert request.acquisition_mode is AcquisitionMode.CLINICIAN_OBSERVATION
    assert evidence.acquisition_mode is AcquisitionMode.CLINICIAN_OBSERVATION
    assert acquisition_mode_for(ObservationId.RESPIRATORY_RATE) is AcquisitionMode.MEASUREMENT
    with pytest.raises(ValueError, match="requires MEASUREMENT"):
        ObservationEvidence(
            observation_id=ObservationId.RESPIRATORY_RATE,
            knowledge_state=KnowledgeState.KNOWN_VALUE,
            value=52,
            acquired=True,
            acquisition_mode=AcquisitionMode.CAREGIVER_QUESTION,
            validity=ObservationValidity(EvidenceValidityStatus.VALID),
        )


def test_acquisition_channels_remain_separate():
    decision = _drinking_request()
    assessment = replace(
        decision,
        reason=AcquisitionReason.ASSESSMENT_COMPLETION_ONLY,
        can_change_classification=False,
        can_change_actions=False,
    )

    with pytest.raises(ValueError, match="overlap"):
        replace(
            _policy_result(final=False),
            decision_directed_acquisitions=(decision,),
            assessment_completion_acquisitions=(assessment,),
        )


def test_complete_single_turn_fixture_is_representable_and_committed():
    expected = build_complete_fixture()
    loaded = _load_fixture("complete_case_v1.json")

    assert loaded == expected
    assert loaded.terminal_state_id == "state-final"
    assert len(loaded.interaction.turns) == 2
    assert loaded.interaction.turns[-1].expected_assistant_semantics.decision_status is DecisionStatus.SUFFICIENT


def test_incomplete_single_turn_is_representable():
    source = build_multiturn_fixture()
    partial_turns = source.interaction.turns[:2]
    incomplete = replace(
        source,
        trajectory_id="illustrative-incomplete-single-turn-v1",
        states=(source.states[0],),
        interaction=TrajectoryInteraction(partial_turns),
        terminal_state_id=None,
    )

    assert incomplete.terminal_state_id is None
    assert incomplete.interaction.turns[-1].expected_assistant_semantics.decision_status is DecisionStatus.INSUFFICIENT
    assert incomplete.interaction.turns[-1].expected_assistant_semantics.decision_directed_acquisitions


def test_multi_turn_fixture_is_representable_and_committed():
    expected = build_multiturn_fixture()
    loaded = _load_fixture("multi_turn_case_v1.json")

    assert loaded == expected
    assert len(loaded.interaction.turns) == 4
    assert loaded.states[0].policy_result.supported_encounter_decision_status is DecisionStatus.INSUFFICIENT
    assert loaded.states[-1].policy_result.supported_encounter_decision_status is DecisionStatus.SUFFICIENT


def test_urgent_action_and_incomplete_assessment_are_simultaneously_representable():
    assessment_request = AcquisitionRequest(
        observation_id=ObservationId.RESPIRATORY_RATE,
        acquisition_mode=AcquisitionMode.MEASUREMENT,
        reason=AcquisitionReason.ASSESSMENT_COMPLETION_ONLY,
        priority_band=6,
        priority_order=10,
        provenance=_policy_provenance("IMCI-RESP-FAST-BREATHING-12-60M"),
    )
    semantics = ExpectedAssistantSemantics(
        behaviors=(
            AssistantBehavior.EMIT_URGENT_ACTION,
            AssistantBehavior.EMIT_CLASSIFICATION,
            AssistantBehavior.EMIT_ACTIONS,
            AssistantBehavior.REQUEST_INFORMATION,
        ),
        scope_status=ScopeStatus.IN_SCOPE,
        decision_status=DecisionStatus.SUFFICIENT,
        action_set_sufficient=True,
        assessment_complete=False,
        urgent_action_required=True,
        exact_rule_sufficient=True,
        detected_danger_signs=(DangerSign.VOMITS_EVERYTHING,),
        classifications={Pathway.GENERAL_DANGER_SIGNS: Classification.VERY_SEVERE_DISEASE},
        referral=ReferralRequirement.URGENT,
        actions=(Action.URGENT_REFERRAL, Action.COMPLETE_ASSESSMENT_QUICKLY),
        possible_fired_rule_ids=("IMCI-GDS-VOMITS-EVERYTHING",),
        assessment_completion_acquisitions=(assessment_request,),
    )

    assert semantics.urgent_action_required
    assert not semantics.assessment_complete
    assert semantics.assessment_completion_acquisitions == (assessment_request,)


def test_natural_language_target_keeps_structured_semantics_beside_it():
    turn = build_complete_fixture().interaction.turns[-1]
    serialized = turn.to_dict()

    assert serialized["visible_message"]["content"].startswith("The supported dehydration classification")
    assert serialized["expected_assistant_semantics"]["classifications"] == {
        "dehydration": "SOME_DEHYDRATION"
    }
    assert serialized["expected_assistant_semantics"]["actions"]


def test_generation_and_leakage_metadata_round_trips():
    metadata = _metadata("round-trip-template")

    assert TrajectoryMetadata.from_dict(metadata.to_dict()) == metadata
    assert metadata.corpus_role is CorpusRole.ILLUSTRATIVE_FIXTURE
    assert metadata.counterfactual_group_id == "illustrative-drinking-response"
    assert metadata.split_group_ids == ("latent-family:illustrative-some-dehydration",)


def test_approved_contradictory_states_are_rejected():
    lethargic = ObservationEvidence.known(ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS, True)
    restless = ObservationEvidence.known(ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE, True)
    unable_false = ObservationEvidence.known(ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED, False)
    drinking_unable = ObservationEvidence.known(
        ObservationId.DEHYDRATION_DRINKING_STATUS,
        DrinkingStatus.UNABLE,
    )

    with pytest.raises(ValueError, match="both lethargic"):
        PartialCaseState.from_observations("contradictory-condition", (lethargic, restless), _policy_result(final=False))
    with pytest.raises(ValueError, match="UNABLE drinking status"):
        PartialCaseState.from_observations("contradictory-drinking", (unable_false, drinking_unable), _policy_result(final=False))


def test_unresolved_validity_is_retained_without_becoming_known_evidence():
    unresolved_provenance = _policy_provenance(
        "IMCI-RESP-FAST-BREATHING-12-60M",
        basis=BasisType.UNRESOLVED_CLINICAL_AMBIGUITY,
        unresolved_question_ids=("IP-CQ-003",),
    )
    unresolved_rate = ObservationEvidence(
        observation_id=ObservationId.RESPIRATORY_RATE,
        knowledge_state=KnowledgeState.UNKNOWN,
        value=52,
        acquired=True,
        acquisition_mode=AcquisitionMode.MEASUREMENT,
        validity=ObservationValidity(
            status=EvidenceValidityStatus.UNRESOLVED,
            child_calm=None,
            counted_for_one_minute=None,
            unresolved_question_ids=("IP-CQ-003",),
        ),
        provenance=unresolved_provenance,
    )
    policy = replace(
        _policy_result(final=False),
        supported_encounter_decision_status=DecisionStatus.BLOCKED,
        unresolved_question_ids=("IP-CQ-003",),
    )
    state = PartialCaseState.from_observations("unresolved-validity", (unresolved_rate,), policy)
    loaded = PartialCaseState.from_dict(state.to_dict())
    record = loaded.observation(ObservationId.RESPIRATORY_RATE)

    assert record.acquired
    assert record.value == 52
    assert record.knowledge_state is KnowledgeState.UNKNOWN
    assert record.validity.status is EvidenceValidityStatus.UNRESOLVED
    assert loaded.policy_result.supported_encounter_decision_status is DecisionStatus.BLOCKED
    assert loaded.policy_result.unresolved_question_ids == ("IP-CQ-003",)


def test_nonclinical_terminal_behaviors_are_distinct():
    out_of_scope = ExpectedAssistantSemantics(
        behaviors=(AssistantBehavior.REPORT_OUT_OF_SCOPE,),
        scope_status=ScopeStatus.OUT_OF_SCOPE,
        decision_status=DecisionStatus.SUFFICIENT,
        action_set_sufficient=True,
        assessment_complete=False,
        urgent_action_required=False,
        exact_rule_sufficient=False,
    )
    blocked = ExpectedAssistantSemantics(
        behaviors=(AssistantBehavior.REPORT_BLOCKED,),
        scope_status=ScopeStatus.IN_SCOPE,
        decision_status=DecisionStatus.BLOCKED,
        action_set_sufficient=False,
        assessment_complete=False,
        urgent_action_required=False,
        exact_rule_sufficient=False,
        blocked_observation_ids=(ObservationId.RESPIRATORY_RATE,),
        unresolved_question_ids=("IP-CQ-003",),
    )

    assert out_of_scope.behaviors != blocked.behaviors


def test_trajectory_json_serialization_is_deterministic():
    trajectory = build_multiturn_fixture()
    content = trajectory.to_json()

    assert ClinicalTrajectory.from_json(content) == trajectory
    assert trajectory.to_json() == content
