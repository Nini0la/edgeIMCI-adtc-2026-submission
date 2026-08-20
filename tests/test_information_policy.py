from __future__ import annotations

import pytest

from edge_imci.information_policy import evaluate_information_policy
from edge_imci.information_policy.artifacts import CONSTRAINT_SET_ID, POLICY_ID
from edge_imci.schemas.case import (
    Action,
    Classification,
    DrinkingStatus,
    Pathway,
    SkinPinch,
)
from edge_imci.schemas.trajectory import (
    AcquisitionMode,
    AcquisitionReason,
    DecisionStatus,
    EntryStatus,
    EvidenceValidityStatus,
    InformationPolicyResult,
    KnowledgeState,
    ObservationEvidence,
    ObservationId,
    ObservationValidity,
    PartialCaseState,
    PathwayPolicyState,
    ScopeStatus,
)


DANGER_IDS = (
    ObservationId.DANGER_CONVULSING_NOW,
    ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS,
    ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED,
    ObservationId.DANGER_VOMITS_EVERYTHING,
    ObservationId.DANGER_HAD_CONVULSIONS,
)


def _placeholder_result() -> InformationPolicyResult:
    return InformationPolicyResult(
        policy_id=POLICY_ID,
        constraint_set_id=CONSTRAINT_SET_ID,
        scope_status=ScopeStatus.UNKNOWN,
        pathway_states=(
            PathwayPolicyState(
                pathway=Pathway.GENERAL_DANGER_SIGNS,
                entry_status=EntryStatus.ACTIVE,
                possible_classifications=(),
                decision_status=DecisionStatus.INSUFFICIENT,
                action_set_sufficient=False,
                exact_rule_sufficient=False,
                possible_fired_rule_ids=(),
                assessment_complete=False,
            ),
            PathwayPolicyState(
                pathway=Pathway.RESPIRATORY,
                entry_status=EntryStatus.UNKNOWN,
                possible_classifications=(),
                decision_status=DecisionStatus.INSUFFICIENT,
                action_set_sufficient=False,
                exact_rule_sufficient=False,
                possible_fired_rule_ids=(),
                assessment_complete=False,
            ),
            PathwayPolicyState(
                pathway=Pathway.DEHYDRATION,
                entry_status=EntryStatus.UNKNOWN,
                possible_classifications=(),
                decision_status=DecisionStatus.INSUFFICIENT,
                action_set_sufficient=False,
                exact_rule_sufficient=False,
                possible_fired_rule_ids=(),
                assessment_complete=False,
            ),
        ),
        supported_encounter_decision_status=DecisionStatus.INSUFFICIENT,
        supported_encounter_action_set_sufficient=False,
        supported_encounter_assessment_complete=False,
        urgent_action_required=False,
    )


def _known_values(**overrides):
    values = {
        ObservationId.AGE_MONTHS: 18,
        ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: False,
        ObservationId.HAS_DIARRHOEA: False,
    }
    values.update({item: False for item in DANGER_IDS})
    values.update(overrides)
    return values


def _state(*, records=(), **values) -> PartialCaseState:
    evidence = [ObservationEvidence.known(item, value) for item, value in values.items()]
    evidence.extend(records)
    return PartialCaseState.from_observations("policy-test", tuple(evidence), _placeholder_result())


def _complete_state(**overrides) -> PartialCaseState:
    values = _known_values(
        **{
            ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM: False,
            ObservationId.RESPIRATORY_CHEST_INDRAWING: False,
            ObservationId.RESPIRATORY_RATE: 20,
            ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE: False,
            ObservationId.DEHYDRATION_SUNKEN_EYES: False,
            ObservationId.DEHYDRATION_DRINKING_STATUS: DrinkingStatus.NORMAL,
            ObservationId.DEHYDRATION_SKIN_PINCH: SkinPinch.NORMAL,
        }
    )
    values.update(overrides)
    return _state(**values)


def _pathway(result: InformationPolicyResult, pathway: Pathway) -> PathwayPolicyState:
    return next(item for item in result.pathway_states if item.pathway is pathway)


def _request_ids(result: InformationPolicyResult):
    return tuple(item.observation_id for item in result.decision_directed_acquisitions)


def test_unknown_danger_sign_is_not_treated_as_negative():
    values = _known_values()
    values.pop(ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED)

    result = evaluate_information_policy(_state(**values))
    danger = _pathway(result, Pathway.GENERAL_DANGER_SIGNS)

    assert danger.decision_status is DecisionStatus.INSUFFICIENT
    assert danger.possible_classifications == (Classification.VERY_SEVERE_DISEASE,)
    assert ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED in _request_ids(result)


def test_known_danger_sign_makes_severe_and_urgent_decisions_sufficient_early():
    result = evaluate_information_policy(
        _state(
            **{
                ObservationId.AGE_MONTHS: 18,
                ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True,
                ObservationId.HAS_DIARRHOEA: False,
                ObservationId.DANGER_CONVULSING_NOW: False,
                ObservationId.DANGER_VOMITS_EVERYTHING: True,
            }
        )
    )

    danger = _pathway(result, Pathway.GENERAL_DANGER_SIGNS)
    respiratory = _pathway(result, Pathway.RESPIRATORY)
    assert danger.decision_status is DecisionStatus.SUFFICIENT
    assert respiratory.decision_status is DecisionStatus.SUFFICIENT
    assert respiratory.possible_classifications == (
        Classification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE,
    )
    assert result.urgent_action_required
    assert not result.supported_encounter_assessment_complete
    assert Action.URGENT_REFERRAL in result.known_actions
    assert "IP-CQ-001" in result.unresolved_question_ids


def test_all_danger_signs_must_be_negative_to_prove_absence():
    incomplete = _known_values()
    incomplete.pop(ObservationId.DANGER_HAD_CONVULSIONS)
    incomplete_result = evaluate_information_policy(_state(**incomplete))
    complete_result = evaluate_information_policy(_state(**_known_values()))

    assert _pathway(incomplete_result, Pathway.GENERAL_DANGER_SIGNS).decision_status is DecisionStatus.INSUFFICIENT
    complete_danger = _pathway(complete_result, Pathway.GENERAL_DANGER_SIGNS)
    assert complete_danger.decision_status is DecisionStatus.SUFFICIENT
    assert complete_danger.possible_classifications == ()


def test_convulsing_now_remains_action_relevant_after_severe_is_known():
    values = _known_values(**{ObservationId.DANGER_VOMITS_EVERYTHING: True})
    values.pop(ObservationId.DANGER_CONVULSING_NOW)

    result = evaluate_information_policy(_state(**values))
    request = result.decision_directed_acquisitions[0]

    assert _pathway(result, Pathway.GENERAL_DANGER_SIGNS).decision_status is DecisionStatus.SUFFICIENT
    assert result.urgent_action_required
    assert Action.GIVE_DIAZEPAM_IF_CONVULSING_NOW not in result.known_actions
    assert Action.GIVE_DIAZEPAM_IF_CONVULSING_NOW in result.possible_additional_actions
    assert request.observation_id is ObservationId.DANGER_CONVULSING_NOW
    assert request.reason is AcquisitionReason.CAN_ADD_IMMEDIATE_ACTION


def test_respiratory_stridor_short_circuits_classification_not_assessment():
    result = evaluate_information_policy(
        _state(
            **_known_values(
                **{
                    ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True,
                    ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM: True,
                }
            )
        )
    )
    respiratory = _pathway(result, Pathway.RESPIRATORY)
    assessment_ids = {item.observation_id for item in result.assessment_completion_acquisitions}

    assert respiratory.decision_status is DecisionStatus.SUFFICIENT
    assert respiratory.action_set_sufficient
    assert not respiratory.assessment_complete
    assert respiratory.possible_classifications == (
        Classification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE,
    )
    assert ObservationId.RESPIRATORY_CHEST_INDRAWING in assessment_ids
    assert ObservationId.RESPIRATORY_RATE in assessment_ids


def test_pneumonia_is_invariant_while_exact_rule_is_unresolved():
    result = evaluate_information_policy(
        _state(
            **_known_values(
                **{
                    ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True,
                    ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM: False,
                    ObservationId.RESPIRATORY_RATE: 45,
                }
            )
        )
    )
    respiratory = _pathway(result, Pathway.RESPIRATORY)

    assert respiratory.possible_classifications == (Classification.PNEUMONIA,)
    assert respiratory.decision_status is DecisionStatus.SUFFICIENT
    assert respiratory.action_set_sufficient
    assert not respiratory.exact_rule_sufficient
    assert set(respiratory.possible_fired_rule_ids) == {
        "IMCI-RESP-PNEUMONIA-CHEST-INDRAWING",
        "IMCI-RESP-PNEUMONIA-FAST-BREATHING",
    }
    assert ObservationId.RESPIRATORY_CHEST_INDRAWING not in _request_ids(result)
    assert ObservationId.RESPIRATORY_CHEST_INDRAWING in {
        item.observation_id for item in result.assessment_completion_acquisitions
    }


@pytest.mark.parametrize(
    ("age", "rate", "classification"),
    [
        (11, 49, Classification.COUGH_OR_COLD),
        (11, 50, Classification.PNEUMONIA),
        (12, 39, Classification.COUGH_OR_COLD),
        (12, 40, Classification.PNEUMONIA),
    ],
)
def test_policy_preserves_respiratory_age_and_rate_boundaries(age, rate, classification):
    result = evaluate_information_policy(
        _complete_state(
            **{
                ObservationId.AGE_MONTHS: age,
                ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True,
                ObservationId.RESPIRATORY_RATE: rate,
            }
        )
    )

    assert _pathway(result, Pathway.RESPIRATORY).possible_classifications == (classification,)


def test_two_severe_dehydration_signs_are_decision_sufficient():
    result = evaluate_information_policy(
        _state(
            **_known_values(
                **{
                    ObservationId.HAS_DIARRHOEA: True,
                    ObservationId.DEHYDRATION_SUNKEN_EYES: True,
                    ObservationId.DEHYDRATION_DRINKING_STATUS: DrinkingStatus.POORLY,
                }
            )
        )
    )
    dehydration = _pathway(result, Pathway.DEHYDRATION)

    assert dehydration.possible_classifications == (Classification.SEVERE_DEHYDRATION,)
    assert dehydration.decision_status is DecisionStatus.SUFFICIENT
    assert dehydration.action_set_sufficient
    assert Action.GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C in result.known_actions
    assert not dehydration.assessment_complete


def test_two_some_dehydration_signs_classify_some_when_severe_is_impossible():
    result = evaluate_information_policy(
        _complete_state(
            **{
                ObservationId.HAS_DIARRHOEA: True,
                ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE: True,
                ObservationId.DEHYDRATION_SUNKEN_EYES: True,
            }
        )
    )

    assert _pathway(result, Pathway.DEHYDRATION).possible_classifications == (
        Classification.SOME_DEHYDRATION,
    )


def test_no_dehydration_is_sufficient_only_after_higher_counts_are_impossible():
    values = _known_values(
        **{
            ObservationId.HAS_DIARRHOEA: True,
            ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE: False,
            ObservationId.DEHYDRATION_SUNKEN_EYES: False,
            ObservationId.DEHYDRATION_DRINKING_STATUS: DrinkingStatus.NORMAL,
        }
    )
    result = evaluate_information_policy(_state(**values))
    dehydration = _pathway(result, Pathway.DEHYDRATION)

    assert dehydration.possible_classifications == (Classification.NO_DEHYDRATION,)
    assert dehydration.decision_status is DecisionStatus.SUFFICIENT
    assert ObservationId.DEHYDRATION_SKIN_PINCH not in _request_ids(result)
    assert ObservationId.DEHYDRATION_SKIN_PINCH in {
        item.observation_id for item in result.assessment_completion_acquisitions
    }


def test_dehydration_classification_can_be_fixed_while_actions_are_unresolved():
    result = evaluate_information_policy(
        _state(
            **{
                ObservationId.AGE_MONTHS: 18,
                ObservationId.HAS_DIARRHOEA: True,
                ObservationId.DEHYDRATION_SUNKEN_EYES: True,
                ObservationId.DEHYDRATION_DRINKING_STATUS: DrinkingStatus.POORLY,
            }
        )
    )
    dehydration = _pathway(result, Pathway.DEHYDRATION)

    assert dehydration.possible_classifications == (Classification.SEVERE_DEHYDRATION,)
    assert dehydration.decision_status is DecisionStatus.SUFFICIENT
    assert not dehydration.action_set_sufficient
    assert {
        Action.GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C,
        Action.FREQUENT_ORS_SIPS_DURING_REFERRAL,
    } <= set(result.possible_additional_actions)


def test_decision_sufficient_and_assessment_incomplete_are_independent():
    result = evaluate_information_policy(
        _state(
            **_known_values(
                **{
                    ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True,
                    ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM: False,
                    ObservationId.RESPIRATORY_CHEST_INDRAWING: True,
                }
            )
        )
    )
    respiratory = _pathway(result, Pathway.RESPIRATORY)

    assert respiratory.decision_status is DecisionStatus.SUFFICIENT
    assert not respiratory.assessment_complete


def test_urgent_action_and_assessment_incomplete_are_independent():
    values = _known_values(**{ObservationId.DANGER_VOMITS_EVERYTHING: True})
    values.pop(ObservationId.DANGER_HAD_CONVULSIONS)
    result = evaluate_information_policy(_state(**values))

    assert result.urgent_action_required
    assert not result.supported_encounter_assessment_complete


def test_decision_and_assessment_acquisition_channels_are_disjoint():
    result = evaluate_information_policy(
        _state(
            **{
                ObservationId.AGE_MONTHS: 18,
                ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: False,
                ObservationId.HAS_DIARRHOEA: False,
                ObservationId.DANGER_VOMITS_EVERYTHING: True,
            }
        )
    )
    decision_ids = {item.observation_id for item in result.decision_directed_acquisitions}
    assessment_ids = {item.observation_id for item in result.assessment_completion_acquisitions}

    assert decision_ids == {ObservationId.DANGER_CONVULSING_NOW}
    assert assessment_ids
    assert decision_ids.isdisjoint(assessment_ids)
    assert all(item.reason is AcquisitionReason.ASSESSMENT_COMPLETION_ONLY for item in result.assessment_completion_acquisitions)


def test_scheduler_uses_deterministic_band_mode_and_canonical_order_batches():
    first = evaluate_information_policy(_state(**{ObservationId.AGE_MONTHS: 18}))
    assert _request_ids(first) == (
        ObservationId.DANGER_CONVULSING_NOW,
        ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS,
    )
    assert all(item.priority_band == 2 for item in first.decision_directed_acquisitions)
    assert all(item.acquisition_mode is AcquisitionMode.CLINICIAN_OBSERVATION for item in first.decision_directed_acquisitions)

    second_values = {
        ObservationId.AGE_MONTHS: 18,
        ObservationId.DANGER_CONVULSING_NOW: False,
        ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS: False,
    }
    second = evaluate_information_policy(_state(**second_values))
    assert _request_ids(second) == (
        ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED,
        ObservationId.DANGER_VOMITS_EVERYTHING,
        ObservationId.DANGER_HAD_CONVULSIONS,
    )


def test_invalid_lethargic_and_restless_completion_is_excluded():
    values = _known_values(
        **{
            ObservationId.HAS_DIARRHOEA: True,
            ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE: True,
            ObservationId.DEHYDRATION_SUNKEN_EYES: False,
            ObservationId.DEHYDRATION_DRINKING_STATUS: DrinkingStatus.NORMAL,
            ObservationId.DEHYDRATION_SKIN_PINCH: SkinPinch.NORMAL,
        }
    )
    values.pop(ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS)
    result = evaluate_information_policy(_state(**values))

    assert _pathway(result, Pathway.DEHYDRATION).possible_classifications == (
        Classification.NO_DEHYDRATION,
    )
    assert "VC-COHERENCE-001" in result.applied_constraint_ids


def test_unresolved_respiratory_validity_blocks_instead_of_guessing():
    unresolved_rate = ObservationEvidence(
        observation_id=ObservationId.RESPIRATORY_RATE,
        knowledge_state=KnowledgeState.UNKNOWN,
        value=45,
        acquired=True,
        acquisition_mode=AcquisitionMode.MEASUREMENT,
        validity=ObservationValidity(
            status=EvidenceValidityStatus.UNRESOLVED,
            child_calm=None,
            counted_for_one_minute=True,
            unresolved_question_ids=("IP-CQ-003",),
        ),
    )
    result = evaluate_information_policy(
        _state(
            records=(unresolved_rate,),
            **_known_values(
                **{
                    ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True,
                    ObservationId.RESPIRATORY_STRIDOR_WHEN_CALM: False,
                    ObservationId.RESPIRATORY_CHEST_INDRAWING: False,
                }
            ),
        )
    )

    assert _pathway(result, Pathway.RESPIRATORY).decision_status is DecisionStatus.BLOCKED
    assert result.supported_encounter_decision_status is DecisionStatus.BLOCKED
    assert "IP-CQ-003" in result.unresolved_question_ids
    assert _request_ids(result) == (ObservationId.RESPIRATORY_RATE,)
    assert result.decision_directed_acquisitions[0].provenance.unresolved_question_ids == ("IP-CQ-003",)


def test_drinking_fields_remain_separate_and_ip_cq_002_is_retained():
    result = evaluate_information_policy(
        _state(
            **{
                ObservationId.AGE_MONTHS: 18,
                ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: False,
                ObservationId.HAS_DIARRHOEA: True,
                ObservationId.DANGER_CONVULSING_NOW: False,
                ObservationId.DANGER_LETHARGIC_OR_UNCONSCIOUS: False,
                ObservationId.DANGER_VOMITS_EVERYTHING: False,
                ObservationId.DANGER_HAD_CONVULSIONS: False,
                ObservationId.DEHYDRATION_RESTLESS_OR_IRRITABLE: False,
                ObservationId.DEHYDRATION_SUNKEN_EYES: True,
                ObservationId.DEHYDRATION_DRINKING_STATUS: DrinkingStatus.UNABLE,
                ObservationId.DEHYDRATION_SKIN_PINCH: SkinPinch.NORMAL,
            }
        )
    )

    assert "IP-CQ-002" in result.unresolved_question_ids
    assert ObservationId.DANGER_UNABLE_TO_DRINK_OR_BREASTFEED in _request_ids(result)
    assert _pathway(result, Pathway.GENERAL_DANGER_SIGNS).decision_status is DecisionStatus.INSUFFICIENT


def test_home_care_with_urgent_referral_retains_ip_cq_004():
    result = evaluate_information_policy(
        _complete_state(
            **{
                ObservationId.HAS_DIARRHOEA: True,
                ObservationId.DANGER_VOMITS_EVERYTHING: True,
            }
        )
    )

    assert Action.URGENT_REFERRAL in result.known_actions
    assert Action.GIVE_FLUID_ZINC_AND_FOOD_PLAN_A in result.known_actions
    assert "IP-CQ-004" in result.unresolved_question_ids


def test_policy_result_serialization_is_deterministic():
    result = evaluate_information_policy(
        _complete_state(
            **{
                ObservationId.HAS_COUGH_OR_DIFFICULT_BREATHING: True,
                ObservationId.RESPIRATORY_RATE: 45,
            }
        )
    )

    assert InformationPolicyResult.from_dict(result.to_dict()) == result
    assert result.to_dict() == InformationPolicyResult.from_dict(result.to_dict()).to_dict()
