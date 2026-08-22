from __future__ import annotations

from dataclasses import replace

import pytest

from edge_imci.evaluation.holistic import evaluate_holistic_encounter
from edge_imci.schemas.case import DrinkingStatus, GeneralDangerSignObservations, SkinPinch
from edge_imci.schemas.holistic import (
    DehydrationAssessment,
    HolisticAction,
    HolisticClassification,
    HolisticDiarrhoeaObservations,
    HolisticEarObservations,
    HolisticEncounter,
    HolisticFeverObservations,
    HolisticPatientFacts,
    HolisticRespiratoryObservations,
    MajorAssessment,
    MalariaRisk,
    MalariaTestResult,
)


def _danger(**overrides: bool | None) -> GeneralDangerSignObservations:
    values = {
        "unable_to_drink_or_breastfeed": False,
        "vomits_everything": False,
        "had_convulsions": False,
        "lethargic_or_unconscious": False,
        "convulsing_now": False,
    }
    values.update(overrides)
    return GeneralDangerSignObservations(**values)


def _facts(**overrides: object) -> HolisticPatientFacts:
    values: dict[str, object] = {
        "age_months": 18,
        "has_cough_or_difficult_breathing": False,
        "has_diarrhoea": False,
        "has_fever": False,
        "has_ear_problem": False,
    }
    values.update(overrides)
    return HolisticPatientFacts(**values)  # type: ignore[arg-type]


def _encounter(**overrides: object) -> HolisticEncounter:
    values: dict[str, object] = {
        "encounter_id": "test-encounter",
        "patient_facts": _facts(),
        "danger_signs": _danger(),
    }
    values.update(overrides)
    return HolisticEncounter(**values)  # type: ignore[arg-type]


def _resp(**overrides: object) -> HolisticRespiratoryObservations:
    values: dict[str, object] = {
        "cough_duration_days": 3,
        "respiratory_rate": 35,
        "chest_indrawing": False,
        "stridor_when_calm": False,
        "wheezing": False,
        "recurrent_wheeze": False,
        "child_calm": True,
        "breaths_counted_one_minute": True,
        "pulse_oximeter_available": False,
    }
    values.update(overrides)
    return HolisticRespiratoryObservations(**values)  # type: ignore[arg-type]


def _dehydration(**overrides: object) -> DehydrationAssessment:
    values: dict[str, object] = {
        "restless_or_irritable": False,
        "sunken_eyes": False,
        "drinking_status": DrinkingStatus.NORMAL,
        "skin_pinch": SkinPinch.NORMAL,
    }
    values.update(overrides)
    return DehydrationAssessment(**values)  # type: ignore[arg-type]


def _fever(**overrides: object) -> HolisticFeverObservations:
    values: dict[str, object] = {
        "temperature_c": 38.0,
        "malaria_risk": MalariaRisk.HIGH,
        "fever_duration_days": 2,
        "stiff_neck": False,
        "runny_nose": False,
        "obvious_cause_of_fever_present": False,
        "identified_bacterial_cause_present": False,
        "malaria_test_available": True,
        "malaria_test_result": MalariaTestResult.NEGATIVE,
        "measles_within_last_3_months": False,
        "generalized_rash": False,
        "measles_cough": False,
        "red_eyes": False,
    }
    values.update(overrides)
    return HolisticFeverObservations(**values)  # type: ignore[arg-type]


def _ear(**overrides: object) -> HolisticEarObservations:
    values: dict[str, object] = {
        "ear_pain": False,
        "ear_discharge_reported": False,
        "pus_draining_from_ear": False,
        "tender_swelling_behind_ear": False,
    }
    values.update(overrides)
    return HolisticEarObservations(**values)  # type: ignore[arg-type]


def _classes(result) -> set[HolisticClassification]:
    return {item.classification for item in result.final_classifications}


def test_complete_encounter_requires_explicit_entry_status_for_every_supported_area() -> None:
    complete = evaluate_holistic_encounter(_encounter())
    assert complete.supported_encounter_complete
    assert complete.final_holistic_synthesis_authorized

    incomplete = evaluate_holistic_encounter(
        _encounter(patient_facts=replace(_facts(), has_diarrhoea=None))
    )
    assert not incomplete.supported_encounter_complete
    assert not incomplete.final_classifications
    assert "patient_facts.has_diarrhoea" in incomplete.missing_elements[MajorAssessment.ENCOUNTER]


def test_explicit_negative_entry_is_not_equivalent_to_omission() -> None:
    explicit_no = evaluate_holistic_encounter(_encounter())
    omitted = evaluate_holistic_encounter(
        _encounter(patient_facts=replace(_facts(), has_diarrhoea=None))
    )
    assert explicit_no.supported_encounter_complete
    assert not omitted.supported_encounter_complete


def test_incomplete_known_danger_sign_emits_urgent_actions_but_no_final_synthesis() -> None:
    encounter = _encounter(
        patient_facts=HolisticPatientFacts(None, None, None, None, None),
        danger_signs=_danger(convulsing_now=True, vomits_everything=None),
    )
    result = evaluate_holistic_encounter(encounter)
    assert not result.supported_encounter_complete
    assert result.urgent_action_required
    assert HolisticAction.URGENT_REFERRAL in result.urgent_actions
    assert HolisticAction.GIVE_DIAZEPAM_IF_CONVULSING_NOW in result.urgent_actions
    assert not result.final_classifications
    assert not result.final_actions


@pytest.mark.parametrize(
    ("age", "rate", "expected"),
    [(2, 49, HolisticClassification.COUGH_OR_COLD), (2, 50, HolisticClassification.PNEUMONIA), (12, 39, HolisticClassification.COUGH_OR_COLD), (12, 40, HolisticClassification.PNEUMONIA), (59, 40, HolisticClassification.PNEUMONIA)],
)
def test_respiratory_age_and_rate_boundaries(age, rate, expected) -> None:
    encounter = _encounter(
        patient_facts=_facts(age_months=age, has_cough_or_difficult_breathing=True),
        respiratory=_resp(respiratory_rate=rate),
    )
    result = evaluate_holistic_encounter(encounter)
    assert result.supported_encounter_complete
    assert expected in _classes(result)


def test_chest_indrawing_requires_hiv_dependency_before_completion() -> None:
    incomplete = evaluate_holistic_encounter(
        _encounter(
            patient_facts=_facts(has_cough_or_difficult_breathing=True),
            respiratory=_resp(chest_indrawing=True),
        )
    )
    assert not incomplete.supported_encounter_complete
    assert "respiratory.hiv_exposed_or_infected" in incomplete.missing_elements[MajorAssessment.RESPIRATORY]

    complete = evaluate_holistic_encounter(
        _encounter(
            patient_facts=_facts(has_cough_or_difficult_breathing=True),
            respiratory=_resp(chest_indrawing=True, hiv_exposed_or_infected=False),
        )
    )
    assert complete.supported_encounter_complete
    assert HolisticClassification.PNEUMONIA in _classes(complete)


def test_wheeze_with_fast_breathing_requires_intervention_and_reassessment() -> None:
    base = _encounter(
        patient_facts=_facts(has_cough_or_difficult_breathing=True),
        respiratory=_resp(respiratory_rate=45, wheezing=True),
    )
    incomplete = evaluate_holistic_encounter(base)
    assert not incomplete.supported_encounter_complete
    assert HolisticAction.GIVE_RAPID_ACTING_INHALED_BRONCHODILATOR_TRIAL in incomplete.intermediate_actions
    assert "respiratory.post_bronchodilator_respiratory_rate" in incomplete.missing_elements[MajorAssessment.RESPIRATORY]

    completed = evaluate_holistic_encounter(
        replace(
            base,
            respiratory=replace(
                base.respiratory,
                bronchodilator_trial_completed=True,
                post_bronchodilator_respiratory_rate=35,
                post_bronchodilator_chest_indrawing=False,
                post_bronchodilator_child_calm=True,
                post_bronchodilator_breaths_counted_one_minute=True,
            ),
        )
    )
    assert completed.supported_encounter_complete
    assert not completed.unresolved_question_ids
    assert any(
        item.classification is HolisticClassification.COUGH_OR_COLD
        for item in completed.internal_classifications
    )
    assert any(
        item.action is HolisticAction.GIVE_INHALED_BRONCHODILATOR_5_DAYS
        for item in completed.action_trace
    )


def test_some_dehydration_emits_plan_b_and_separate_reassessment_action() -> None:
    observations = HolisticDiarrhoeaObservations(
        duration_days=3,
        blood_in_stool=False,
        dehydration=_dehydration(
            restless_or_irritable=True,
            sunken_eyes=True,
        ),
    )
    encounter = _encounter(
        patient_facts=_facts(has_diarrhoea=True),
        diarrhoea=observations,
    )
    result = evaluate_holistic_encounter(encounter)
    assert result.supported_encounter_complete
    assert HolisticAction.GIVE_FLUID_ZINC_AND_FOOD_PLAN_B in result.intermediate_actions
    assert HolisticAction.REASSESS_DEHYDRATION_AFTER_PLAN_B in result.intermediate_actions
    assert not result.unresolved_question_ids


def test_persistent_diarrhoea_and_dysentery_are_simultaneous_classifications() -> None:
    result = evaluate_holistic_encounter(
        _encounter(
            patient_facts=_facts(has_diarrhoea=True),
            diarrhoea=HolisticDiarrhoeaObservations(
                duration_days=14,
                blood_in_stool=True,
                dehydration=_dehydration(),
            ),
        )
    )
    assert result.supported_encounter_complete
    assert {HolisticClassification.NO_DEHYDRATION, HolisticClassification.PERSISTENT_DIARRHOEA, HolisticClassification.DYSENTERY} <= _classes(result)


def test_fever_malaria_and_measles_can_be_classified_together() -> None:
    result = evaluate_holistic_encounter(
        _encounter(
            patient_facts=_facts(has_fever=True),
            fever=_fever(
                temperature_c=38.5,
                malaria_test_result=MalariaTestResult.POSITIVE,
                generalized_rash=True,
                measles_cough=True,
                mouth_ulcers=False,
                pus_draining_from_eye=False,
                clouding_of_cornea=False,
            ),
        )
    )
    assert result.supported_encounter_complete
    assert {HolisticClassification.MALARIA, HolisticClassification.MEASLES} <= _classes(result)
    assert HolisticAction.GIVE_FIRST_LINE_ORAL_ANTIMALARIAL in result.final_actions
    assert HolisticAction.GIVE_VITAMIN_A_TREATMENT in result.final_actions
    assert HolisticAction.GIVE_PARACETAMOL_FOR_HIGH_FEVER in result.final_actions


@pytest.mark.parametrize(
    ("duration", "expected"),
    [(13, HolisticClassification.ACUTE_EAR_INFECTION), (14, HolisticClassification.CHRONIC_EAR_INFECTION)],
)
def test_ear_discharge_duration_boundary(duration, expected) -> None:
    result = evaluate_holistic_encounter(
        _encounter(
            patient_facts=_facts(has_ear_problem=True),
            ear=_ear(
                ear_discharge_reported=True,
                ear_discharge_duration_days=duration,
                pus_draining_from_ear=True,
            ),
        )
    )
    assert result.supported_encounter_complete
    assert expected in _classes(result)


def test_observed_pus_with_no_prior_discharge_is_acute() -> None:
    result = evaluate_holistic_encounter(
        _encounter(
            patient_facts=_facts(has_ear_problem=True),
            ear=_ear(
                ear_pain=False,
                ear_discharge_reported=False,
                pus_draining_from_ear=True,
                tender_swelling_behind_ear=False,
            ),
        )
    )
    assert result.supported_encounter_complete
    assert HolisticClassification.ACUTE_EAR_INFECTION in _classes(result)


def test_positive_unable_to_drink_is_reused_for_dehydration_only_one_way() -> None:
    positive = evaluate_holistic_encounter(
        _encounter(
            patient_facts=_facts(has_diarrhoea=True),
            danger_signs=_danger(unable_to_drink_or_breastfeed=True),
            diarrhoea=HolisticDiarrhoeaObservations(
                duration_days=2,
                blood_in_stool=False,
                dehydration=_dehydration(sunken_eyes=True, drinking_status=None),
            ),
        )
    )
    assert positive.supported_encounter_complete
    assert HolisticClassification.SEVERE_DEHYDRATION in _classes(positive)
    assert "diarrhoea.dehydration.drinking_status" not in {
        field for fields in positive.missing_elements.values() for field in fields
    }

    negative = evaluate_holistic_encounter(
        _encounter(
            patient_facts=_facts(has_diarrhoea=True),
            danger_signs=_danger(unable_to_drink_or_breastfeed=False),
            diarrhoea=HolisticDiarrhoeaObservations(
                duration_days=2,
                blood_in_stool=False,
                dehydration=_dehydration(drinking_status=None),
            ),
        )
    )
    assert not negative.supported_encounter_complete
    assert "diarrhoea.dehydration.drinking_status" in negative.missing_elements[MajorAssessment.DIARRHOEA]


def test_mastoiditis_short_circuits_to_urgent_action_but_not_completion() -> None:
    result = evaluate_holistic_encounter(
        _encounter(
            patient_facts=replace(_facts(has_ear_problem=True), has_fever=None),
            ear=HolisticEarObservations(tender_swelling_behind_ear=True),
        )
    )
    assert not result.supported_encounter_complete
    assert result.urgent_action_required
    assert HolisticAction.URGENT_REFERRAL in result.urgent_actions
    assert not result.final_classifications


def test_cross_pathway_severity_changes_dehydration_management() -> None:
    result = evaluate_holistic_encounter(
        _encounter(
            patient_facts=_facts(has_diarrhoea=True, has_ear_problem=True),
            diarrhoea=HolisticDiarrhoeaObservations(
                duration_days=2,
                blood_in_stool=False,
                dehydration=_dehydration(sunken_eyes=True, drinking_status=DrinkingStatus.POORLY),
            ),
            ear=_ear(tender_swelling_behind_ear=True),
        )
    )
    assert result.supported_encounter_complete
    assert HolisticAction.URGENT_REFERRAL in result.final_actions
    assert HolisticAction.FREQUENT_ORS_SIPS_DURING_REFERRAL in result.final_actions
    assert HolisticAction.REASSESS_DEHYDRATION_AFTER_PLAN_C not in result.final_actions


def test_contradiction_blocks_completion() -> None:
    result = evaluate_holistic_encounter(
        _encounter(
            patient_facts=_facts(has_diarrhoea=True),
            danger_signs=_danger(unable_to_drink_or_breastfeed=False),
            diarrhoea=HolisticDiarrhoeaObservations(
                duration_days=2,
                blood_in_stool=False,
                dehydration=_dehydration(drinking_status=DrinkingStatus.UNABLE),
            ),
        )
    )
    assert not result.supported_encounter_complete
    assert result.contradictions
