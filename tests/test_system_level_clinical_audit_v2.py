from __future__ import annotations

from dataclasses import replace

import pytest

from edge_imci.evaluation.holistic import evaluate_holistic_encounter
from edge_imci.generation.cases import load_benchmark
from edge_imci.generation.golden import generate_golden_slice
from edge_imci.information_policy.artifacts import load_information_policy_artifacts
from edge_imci.information_policy.holistic_artifacts import load_holistic_artifacts
from edge_imci.rules.loader import load_rule_set
from edge_imci.schemas.case import DrinkingStatus, GeneralDangerSignObservations, SkinPinch
from edge_imci.schemas.holistic import (
    DehydrationAssessment,
    HolisticAction,
    HolisticClassification,
    HolisticDiarrhoeaObservations,
    HolisticEncounter,
    HolisticFeverObservations,
    HolisticPatientFacts,
    HolisticRespiratoryObservations,
    MalariaRisk,
    MalariaTestResult,
)


def _danger(**changes):
    values = dict(
        unable_to_drink_or_breastfeed=False,
        vomits_everything=False,
        had_convulsions=False,
        lethargic_or_unconscious=False,
        convulsing_now=False,
    )
    values.update(changes)
    return GeneralDangerSignObservations(**values)


def _facts(**changes):
    values = dict(
        age_months=24,
        has_cough_or_difficult_breathing=False,
        has_diarrhoea=False,
        has_fever=False,
        has_ear_problem=False,
    )
    values.update(changes)
    return HolisticPatientFacts(**values)


def _case(*, facts=None, danger=None, respiratory=None, diarrhoea=None, fever=None, ear=None):
    return HolisticEncounter(
        encounter_id="audit-v2",
        patient_facts=facts or _facts(),
        danger_signs=danger or _danger(),
        respiratory=respiratory,
        diarrhoea=diarrhoea,
        fever=fever,
        ear=ear,
    )


def _resp(**changes):
    values = dict(
        cough_duration_days=3,
        respiratory_rate=30,
        chest_indrawing=False,
        stridor_when_calm=False,
        wheezing=False,
        recurrent_wheeze=False,
        child_calm=True,
        breaths_counted_one_minute=True,
        pulse_oximeter_available=False,
    )
    values.update(changes)
    return HolisticRespiratoryObservations(**values)


def _dehydration(**changes):
    values = dict(
        restless_or_irritable=False,
        sunken_eyes=False,
        drinking_status=DrinkingStatus.NORMAL,
        skin_pinch=SkinPinch.NORMAL,
    )
    values.update(changes)
    return DehydrationAssessment(**values)


def _fever(**changes):
    values = dict(
        temperature_c=38.0,
        malaria_risk=MalariaRisk.HIGH,
        fever_duration_days=2,
        stiff_neck=False,
        runny_nose=False,
        obvious_cause_of_fever_present=False,
        identified_bacterial_cause_present=False,
        malaria_test_available=True,
        malaria_test_result=MalariaTestResult.NEGATIVE,
        measles_within_last_3_months=False,
        generalized_rash=False,
        measles_cough=False,
        red_eyes=False,
    )
    values.update(changes)
    return HolisticFeverObservations(**values)


def _classifications(result):
    return {item.classification for item in result.final_classifications}


def _internal_classifications(result):
    return {item.classification for item in result.internal_classifications}


def test_expanded_artifact_inventory_is_explicit() -> None:
    rules = load_holistic_artifacts().rule_set
    assert len(rules.rules) == 40
    assert {rule.source["source_pdf_page"] for rule in rules.rules} >= {5, 6, 7, 8, 9, 23, 24}
    assert {rule.kind for rule in rules.rules} >= {
        "danger_sign",
        "derived_finding",
        "intervention_reassessment",
        "respiratory_classification",
        "diarrhoea_classification",
        "fever_classification",
        "measles_classification",
        "ear_classification",
        "cross_pathway_action_dependency",
    }


def test_frozen_v0_assets_remain_historically_intact() -> None:
    assert len(load_rule_set().rules) == 15
    assert len(load_benchmark()) == 82
    assert len(generate_golden_slice()) == 14
    v1 = load_information_policy_artifacts()
    assert v1.policy["policy_id"] == "imci-selected-v0-information-policy-v1"
    assert v1.constraints["constraint_set_id"] == "imci-selected-v0-valid-completions-v1"


@pytest.mark.parametrize("age", [1, 60])
def test_expanded_scope_rejects_out_of_range_age(age) -> None:
    with pytest.raises(ValueError):
        _facts(age_months=age)


@pytest.mark.parametrize(
    ("saturation", "referred"),
    [(89.9, True), (90.0, False)],
)
def test_oxygen_saturation_referral_boundary(saturation, referred) -> None:
    result = evaluate_holistic_encounter(
        _case(
            facts=_facts(has_cough_or_difficult_breathing=True),
            respiratory=_resp(pulse_oximeter_available=True, oxygen_saturation_percent=saturation),
        )
    )
    assert result.supported_encounter_complete
    assert (
        HolisticAction.REFER_FOR_OXYGEN_SATURATION_BELOW_90 in result.urgent_actions
    ) is referred
    if referred:
        assert not result.unresolved_question_ids
        assert HolisticAction.REFER_FOR_OXYGEN_SATURATION_BELOW_90 in result.final_actions
        assert HolisticAction.SOOTHE_THROAT_AND_RELIEVE_COUGH in result.deferred_actions


@pytest.mark.parametrize(
    ("temperature", "paracetamol"),
    [(38.4, False), (38.5, True)],
)
def test_high_fever_paracetamol_boundary(temperature, paracetamol) -> None:
    result = evaluate_holistic_encounter(
        _case(facts=_facts(has_fever=True), fever=_fever(temperature_c=temperature))
    )
    assert result.supported_encounter_complete
    assert (HolisticAction.GIVE_PARACETAMOL_FOR_HIGH_FEVER in result.final_actions) is paracetamol


@pytest.mark.parametrize(
    ("duration", "every_day", "referred"),
    [(7, None, False), (8, False, False), (8, True, True)],
)
def test_prolonged_fever_requires_more_than_seven_days_every_day(duration, every_day, referred) -> None:
    result = evaluate_holistic_encounter(
        _case(
            facts=_facts(has_fever=True),
            fever=_fever(fever_duration_days=duration, fever_present_every_day=every_day),
        )
    )
    assert result.supported_encounter_complete
    assert (HolisticAction.REFER_PROLONGED_FEVER_FOR_ASSESSMENT in result.final_actions) is referred


@pytest.mark.parametrize(
    ("risk", "test_available", "obvious_cause", "expected", "complete"),
    [
        (MalariaRisk.HIGH, False, False, HolisticClassification.MALARIA, True),
        (MalariaRisk.LOW, False, False, HolisticClassification.MALARIA, True),
        (MalariaRisk.LOW, None, True, HolisticClassification.FEVER_NO_MALARIA, True),
        (MalariaRisk.NONE_NO_TRAVEL, None, False, HolisticClassification.FEVER, True),
    ],
)
def test_malaria_risk_and_test_availability_branches(
    risk, test_available, obvious_cause, expected, complete
) -> None:
    result = evaluate_holistic_encounter(
        _case(
            facts=_facts(has_fever=True),
            fever=_fever(
                malaria_risk=risk,
                malaria_test_available=test_available,
                malaria_test_result=None,
                obvious_cause_of_fever_present=obvious_cause,
            ),
        )
    )
    assert result.supported_encounter_complete is complete
    assert expected in _internal_classifications(result)
    assert not result.unresolved_question_ids


def test_stiff_neck_emits_common_urgent_actions_even_when_malaria_risk_is_missing() -> None:
    result = evaluate_holistic_encounter(
        _case(
            facts=replace(_facts(has_fever=True), has_ear_problem=None),
            fever=_fever(stiff_neck=True, malaria_risk=None),
        )
    )
    assert not result.supported_encounter_complete
    assert HolisticAction.GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC in result.urgent_actions
    assert HolisticAction.PREVENT_LOW_BLOOD_SUGAR in result.urgent_actions
    assert HolisticAction.URGENT_REFERRAL in result.urgent_actions
    assert HolisticAction.GIVE_FIRST_DOSE_SEVERE_MALARIA_TREATMENT not in result.urgent_actions


def test_severe_measles_precedence_and_conditional_eye_action() -> None:
    result = evaluate_holistic_encounter(
        _case(
            facts=_facts(has_fever=True),
            fever=_fever(
                generalized_rash=True,
                red_eyes=True,
                mouth_ulcers=True,
                mouth_ulcers_deep_or_extensive=True,
                pus_draining_from_eye=True,
                clouding_of_cornea=False,
            ),
        )
    )
    assert result.supported_encounter_complete
    assert not result.unresolved_question_ids
    assert HolisticClassification.SEVERE_COMPLICATED_MEASLES in _internal_classifications(result)
    assert HolisticClassification.MEASLES_WITH_EYE_OR_MOUTH_COMPLICATIONS not in _internal_classifications(result)
    assert HolisticAction.APPLY_TETRACYCLINE_EYE_OINTMENT in {
        item.action for item in result.action_trace
    }
    assert HolisticAction.URGENT_REFERRAL in result.urgent_actions
    assert HolisticAction.APPLY_TETRACYCLINE_EYE_OINTMENT in result.deferred_actions
    assert HolisticAction.APPLY_TETRACYCLINE_EYE_OINTMENT not in result.final_actions


@pytest.mark.parametrize(
    ("duration", "persistent"),
    [(13, False), (14, True)],
)
def test_persistent_diarrhoea_duration_boundary(duration, persistent) -> None:
    result = evaluate_holistic_encounter(
        _case(
            facts=_facts(has_diarrhoea=True),
            diarrhoea=HolisticDiarrhoeaObservations(
                duration_days=duration,
                blood_in_stool=False,
                dehydration=_dehydration(),
            ),
        )
    )
    assert result.supported_encounter_complete
    assert (HolisticClassification.PERSISTENT_DIARRHOEA in _classifications(result)) is persistent


def test_cholera_context_is_required_only_for_severe_dehydration_at_age_two_or_more() -> None:
    severe = HolisticDiarrhoeaObservations(
        duration_days=2,
        blood_in_stool=False,
        dehydration=_dehydration(sunken_eyes=True, drinking_status=DrinkingStatus.POORLY),
    )
    # Another severe classification avoids the local rehydration stage and isolates the cholera dependency.
    result = evaluate_holistic_encounter(
        _case(
            facts=_facts(has_diarrhoea=True),
            danger=_danger(convulsing_now=True),
            diarrhoea=severe,
        )
    )
    assert not result.supported_encounter_complete
    assert "diarrhoea.cholera_in_area" in result.missing_elements[next(key for key in result.missing_elements if key.value == "diarrhoea")]

    with_cholera = evaluate_holistic_encounter(
        replace(_case(facts=_facts(has_diarrhoea=True), danger=_danger(convulsing_now=True), diarrhoea=severe), diarrhoea=replace(severe, cholera_in_area=True))
    )
    assert with_cholera.supported_encounter_complete
    assert not with_cholera.unresolved_question_ids
    assert HolisticAction.GIVE_CHOLERA_ANTIBIOTIC_PER_LOCAL_PROTOCOL in {
        item.action for item in with_cholera.action_trace
    }


def test_hiv_chest_indrawing_action_is_traced_as_a_modification() -> None:
    result = evaluate_holistic_encounter(
        _case(
            facts=_facts(has_cough_or_difficult_breathing=True),
            respiratory=_resp(chest_indrawing=True, hiv_exposed_or_infected=True),
        )
    )
    assert result.supported_encounter_complete
    assert not result.unresolved_question_ids
    trace = next(item for item in result.action_trace if item.action is HolisticAction.GIVE_FIRST_DOSE_AMOXICILLIN_AND_REFER)
    assert trace.effect.value == "MODIFIED"
    assert trace.rule_id == "IMCI-MSC-RESP-HIV-CHEST-INDRAWING"
    assert HolisticAction.GIVE_ORAL_AMOXICILLIN_5_DAYS not in result.final_actions
    assert HolisticAction.FOLLOW_UP_3_DAYS not in result.final_actions


def test_no_internal_classification_leaks_to_incomplete_final_output() -> None:
    result = evaluate_holistic_encounter(
        _case(
            facts=replace(_facts(has_cough_or_difficult_breathing=True), has_ear_problem=None),
            respiratory=_resp(respiratory_rate=45),
        )
    )
    assert any(item.classification is HolisticClassification.PNEUMONIA for item in result.internal_classifications)
    assert not result.final_classifications
    assert not result.final_actions
