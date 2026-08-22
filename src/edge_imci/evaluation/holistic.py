"""Deterministic evaluator for the versioned major sick-child encounter scope.

The evaluator exposes internal classifications for auditability, but incomplete
encounters never expose final holistic classifications or management actions.
Known urgent and source-required intermediate actions remain independently
available before encounter completion.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from edge_imci.schemas.case import DangerSign, DrinkingStatus, SkinPinch
from edge_imci.schemas.holistic import (
    ActionTrace,
    ClassificationTrace,
    HolisticAction,
    HolisticClassification,
    HolisticDiarrhoeaObservations,
    HolisticEarObservations,
    HolisticEncounter,
    HolisticEvaluationResult,
    HolisticFeverObservations,
    HolisticRespiratoryObservations,
    MajorAssessment,
    MalariaRisk,
    MalariaTestResult,
    RuleEffect,
)


HOLISTIC_RULE_SET_ID = "imci-major-sick-child-v1"
HOLISTIC_COMPLETENESS_POLICY_ID = "imci-major-sick-child-holistic-completeness-v2"
HOLISTIC_ORACLE_ID = "edge-imci-holistic-deterministic-oracle-v1"

_DANGER_FIELDS = (
    "unable_to_drink_or_breastfeed",
    "vomits_everything",
    "had_convulsions",
    "lethargic_or_unconscious",
    "convulsing_now",
)
_DANGER_RULES = {
    "unable_to_drink_or_breastfeed": "IMCI-MSC-GDS-UNABLE-TO-DRINK",
    "vomits_everything": "IMCI-MSC-GDS-VOMITS-EVERYTHING",
    "had_convulsions": "IMCI-MSC-GDS-CONVULSIONS-HISTORY",
    "lethargic_or_unconscious": "IMCI-MSC-GDS-LETHARGIC-OR-UNCONSCIOUS",
    "convulsing_now": "IMCI-MSC-GDS-CONVULSING-NOW",
}

# These intermediate actions remain part of the immediate referral workflow.
# All other non-urgent actions are retained in the audit trace but deferred when
# an urgent-referral classification is present (approved decision IP-CQ-004).
_PRE_REFERRAL_INTERMEDIATE_ACTIONS = {
    HolisticAction.TREAT_DEHYDRATION_BEFORE_REFERRAL,
}


@dataclass
class _EvaluationState:
    missing: dict[MajorAssessment, set[str]]
    classifications: list[ClassificationTrace]
    action_trace: list[ActionTrace]
    urgent: set[HolisticAction]
    intermediate: set[HolisticAction]
    actions: set[HolisticAction]
    fired: list[str]
    unresolved: set[str]
    contradictions: list[str]
    danger_signs: set[DangerSign]

    def add_missing(self, pathway: MajorAssessment, *fields: str) -> None:
        self.missing[pathway].update(fields)

    def fire(self, rule_id: str) -> None:
        if rule_id not in self.fired:
            self.fired.append(rule_id)

    def classify(
        self,
        pathway: MajorAssessment,
        classification: HolisticClassification,
        rule_id: str,
        *,
        stage: str = "INITIAL",
    ) -> None:
        self.classifications.append(ClassificationTrace(pathway, classification, rule_id, stage))
        self.fire(rule_id)

    def add_action(
        self,
        action: HolisticAction,
        rule_id: str,
        *,
        urgent: bool = False,
        intermediate: bool = False,
        effect: RuleEffect = RuleEffect.ADDED,
        reason: str = "",
    ) -> None:
        target = self.urgent if urgent else self.intermediate if intermediate else self.actions
        target.add(action)
        self.action_trace.append(ActionTrace(action, rule_id, effect, reason))
        self.fire(rule_id)


def evaluate_holistic_encounter(encounter: HolisticEncounter) -> HolisticEvaluationResult:
    """Evaluate one partial or complete supported whole encounter."""

    state = _EvaluationState(
        missing={item: set() for item in MajorAssessment},
        classifications=[],
        action_trace=[],
        urgent=set(),
        intermediate=set(),
        actions=set(),
        fired=[],
        unresolved=set(),
        contradictions=[],
        danger_signs=set(),
    )
    _validate_and_mark_scope(encounter, state)
    _evaluate_danger_signs(encounter, state)
    respiratory = _evaluate_respiratory(encounter, state)
    dehydration = _evaluate_diarrhoea(encounter, state)
    fever = _evaluate_fever(encounter, state)
    ear = _evaluate_ear(encounter, state)

    severe_elsewhere = bool(state.danger_signs) or any(
        trace.classification
        in {
            HolisticClassification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE,
            HolisticClassification.VERY_SEVERE_FEBRILE_DISEASE,
            HolisticClassification.SEVERE_COMPLICATED_MEASLES,
            HolisticClassification.MASTOIDITIS,
        }
        for trace in state.classifications
    )

    _add_respiratory_actions(encounter, state, respiratory)
    _add_diarrhoea_actions(encounter, state, dehydration, severe_elsewhere)
    _add_fever_actions(encounter, state, fever)
    _add_ear_actions(encounter, state, ear)
    _validate_cross_field_consistency(encounter, state)

    missing = {key: tuple(sorted(value)) for key, value in state.missing.items() if value}
    # Approved review decisions no longer block synthesis. Encounter completeness
    # remains stricter than factual field coverage whenever a future encounter-
    # specific ambiguity is explicitly raised.
    complete = not missing and not state.contradictions and not state.unresolved

    if state.urgent:
        immediate_intermediate = state.intermediate & _PRE_REFERRAL_INTERMEDIATE_ACTIONS
        all_actions = state.urgent | immediate_intermediate
        deferred_actions = state.actions | (state.intermediate - immediate_intermediate)
    else:
        all_actions = state.actions | state.intermediate
        deferred_actions = set()
    final_classifications = tuple(state.classifications) if complete else ()
    final_actions = tuple(sorted(all_actions, key=lambda item: item.value)) if complete else ()
    return HolisticEvaluationResult(
        rule_set_id=HOLISTIC_RULE_SET_ID,
        completeness_policy_id=HOLISTIC_COMPLETENESS_POLICY_ID,
        supported_encounter_complete=complete,
        final_holistic_synthesis_authorized=complete,
        urgent_action_required=bool(state.urgent),
        internal_classifications=tuple(state.classifications),
        final_classifications=final_classifications,
        urgent_actions=tuple(sorted(state.urgent, key=lambda item: item.value)),
        intermediate_actions=tuple(sorted(state.intermediate, key=lambda item: item.value)),
        deferred_actions=tuple(sorted(deferred_actions, key=lambda item: item.value)),
        final_actions=final_actions,
        action_trace=tuple(state.action_trace),
        fired_rule_ids=tuple(state.fired),
        missing_elements=missing,
        unresolved_question_ids=tuple(sorted(state.unresolved)),
        contradictions=tuple(state.contradictions),
    )


def _validate_and_mark_scope(encounter: HolisticEncounter, state: _EvaluationState) -> None:
    facts = encounter.patient_facts
    if facts.age_months is None:
        state.add_missing(MajorAssessment.ENCOUNTER, "patient_facts.age_months")
    for name in (
        "has_cough_or_difficult_breathing",
        "has_diarrhoea",
        "has_fever",
        "has_ear_problem",
    ):
        if getattr(facts, name) is None:
            state.add_missing(MajorAssessment.ENCOUNTER, f"patient_facts.{name}")


def _evaluate_danger_signs(encounter: HolisticEncounter, state: _EvaluationState) -> None:
    signs = encounter.danger_signs
    for field_name in _DANGER_FIELDS:
        value = getattr(signs, field_name)
        if value is None:
            state.add_missing(MajorAssessment.GENERAL_DANGER_SIGNS, f"danger_signs.{field_name}")
        elif value:
            rule_id = _DANGER_RULES[field_name]
            state.danger_signs.add(DangerSign(field_name.upper()))
            state.fire(rule_id)

    if not state.danger_signs:
        return
    first_rule = _DANGER_RULES[next(field for field in _DANGER_FIELDS if getattr(signs, field) is True)]
    state.classify(
        MajorAssessment.GENERAL_DANGER_SIGNS,
        HolisticClassification.VERY_SEVERE_DISEASE,
        first_rule,
    )
    for action in (
        HolisticAction.COMPLETE_ASSESSMENT_QUICKLY,
        HolisticAction.GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY,
        HolisticAction.PREVENT_LOW_BLOOD_SUGAR,
        HolisticAction.KEEP_WARM,
        HolisticAction.URGENT_REFERRAL,
    ):
        state.add_action(action, first_rule, urgent=True)
    if signs.convulsing_now is True:
        state.add_action(
            HolisticAction.GIVE_DIAZEPAM_IF_CONVULSING_NOW,
            _DANGER_RULES["convulsing_now"],
            urgent=True,
        )


def _fast_breathing(age_months: int | None, rate: int | None) -> bool | None:
    if age_months is None or rate is None:
        return None
    return rate >= (50 if age_months < 12 else 40)


def _evaluate_respiratory(
    encounter: HolisticEncounter,
    state: _EvaluationState,
) -> HolisticClassification | None:
    if encounter.patient_facts.has_cough_or_difficult_breathing is not True:
        return None
    obs = encounter.respiratory or HolisticRespiratoryObservations()
    required = (
        "cough_duration_days",
        "respiratory_rate",
        "chest_indrawing",
        "stridor_when_calm",
        "wheezing",
        "recurrent_wheeze",
        "child_calm",
        "breaths_counted_one_minute",
        "pulse_oximeter_available",
    )
    for name in required:
        if getattr(obs, name) is None:
            state.add_missing(MajorAssessment.RESPIRATORY, f"respiratory.{name}")
    if obs.child_calm is False:
        state.contradictions.append("respiratory observations are invalid because the child was not calm")
    if obs.breaths_counted_one_minute is False:
        state.contradictions.append("respiratory rate is invalid because breaths were not counted for one minute")
    if obs.pulse_oximeter_available is True and obs.oxygen_saturation_percent is None:
        state.add_missing(MajorAssessment.RESPIRATORY, "respiratory.oxygen_saturation_percent")

    initial_fast = _fast_breathing(encounter.patient_facts.age_months, obs.respiratory_rate)
    if encounter.patient_facts.age_months is not None and obs.respiratory_rate is not None:
        state.fire(
            "IMCI-MSC-RESP-FAST-BREATHING-2-12M"
            if encounter.patient_facts.age_months < 12
            else "IMCI-MSC-RESP-FAST-BREATHING-12-60M"
        )
    severe_known = bool(state.danger_signs) or obs.stridor_when_calm is True
    trial_required = obs.wheezing is True and (initial_fast is True or obs.chest_indrawing is True) and not severe_known
    effective_rate = obs.respiratory_rate
    effective_chest = obs.chest_indrawing
    if trial_required:
        rule_id = "IMCI-MSC-RESP-WHEEZE-BRONCHODILATOR-REASSESS"
        state.add_action(HolisticAction.GIVE_RAPID_ACTING_INHALED_BRONCHODILATOR_TRIAL, rule_id, intermediate=True)
        state.add_action(HolisticAction.REASSESS_BREATHING_AFTER_BRONCHODILATOR, rule_id, intermediate=True)
        for name in (
            "bronchodilator_trial_completed",
            "post_bronchodilator_respiratory_rate",
            "post_bronchodilator_chest_indrawing",
            "post_bronchodilator_child_calm",
            "post_bronchodilator_breaths_counted_one_minute",
        ):
            value = getattr(obs, name)
            if value is None or (name == "bronchodilator_trial_completed" and value is False):
                state.add_missing(MajorAssessment.RESPIRATORY, f"respiratory.{name}")
        if obs.post_bronchodilator_child_calm is False:
            state.contradictions.append("post-bronchodilator respiratory observations were not made while calm")
        if obs.post_bronchodilator_breaths_counted_one_minute is False:
            state.contradictions.append("post-bronchodilator breaths were not counted for one minute")
        if obs.bronchodilator_trial_completed is True:
            effective_rate = obs.post_bronchodilator_respiratory_rate
            effective_chest = obs.post_bronchodilator_chest_indrawing

    if severe_known:
        rule_id = "IMCI-MSC-RESP-SEVERE-DANGER-SIGN" if state.danger_signs else "IMCI-MSC-RESP-SEVERE-STRIDOR"
        state.classify(
            MajorAssessment.RESPIRATORY,
            HolisticClassification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE,
            rule_id,
        )
        return HolisticClassification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE

    if any(getattr(encounter.danger_signs, name) is None for name in _DANGER_FIELDS):
        return None
    effective_fast = _fast_breathing(encounter.patient_facts.age_months, effective_rate)
    if effective_chest is True:
        rule_id = "IMCI-MSC-RESP-PNEUMONIA-CHEST-INDRAWING"
        state.classify(MajorAssessment.RESPIRATORY, HolisticClassification.PNEUMONIA, rule_id)
        if obs.hiv_exposed_or_infected is None:
            state.add_missing(MajorAssessment.RESPIRATORY, "respiratory.hiv_exposed_or_infected")
        return HolisticClassification.PNEUMONIA
    if effective_fast is True:
        rule_id = "IMCI-MSC-RESP-PNEUMONIA-FAST-BREATHING"
        state.classify(MajorAssessment.RESPIRATORY, HolisticClassification.PNEUMONIA, rule_id)
        return HolisticClassification.PNEUMONIA
    decision_values = (effective_chest, effective_fast, obs.stridor_when_calm)
    if all(value is False for value in decision_values):
        rule_id = "IMCI-MSC-RESP-COUGH-OR-COLD"
        state.classify(MajorAssessment.RESPIRATORY, HolisticClassification.COUGH_OR_COLD, rule_id)
        return HolisticClassification.COUGH_OR_COLD
    return None


def _dehydration_classification(
    obs: Any,
    lethargic_or_unconscious: bool | None,
) -> HolisticClassification | None:
    values = (
        obs.restless_or_irritable,
        obs.sunken_eyes,
        obs.drinking_status,
        obs.skin_pinch,
    )
    if any(value is None for value in values) or lethargic_or_unconscious is None:
        return None
    severe = sum(
        (
            lethargic_or_unconscious is True,
            obs.sunken_eyes is True,
            obs.drinking_status in {DrinkingStatus.UNABLE, DrinkingStatus.POORLY},
            obs.skin_pinch is SkinPinch.VERY_SLOWLY,
        )
    )
    # Lethargy is added by the caller because it is stored with danger signs.
    some = sum(
        (
            obs.restless_or_irritable is True,
            obs.sunken_eyes is True,
            obs.drinking_status is DrinkingStatus.EAGER_OR_THIRSTY,
            obs.skin_pinch is SkinPinch.SLOWLY,
        )
    )
    if severe >= 2:
        return HolisticClassification.SEVERE_DEHYDRATION
    if some >= 2:
        return HolisticClassification.SOME_DEHYDRATION
    return HolisticClassification.NO_DEHYDRATION


def _evaluate_diarrhoea(
    encounter: HolisticEncounter,
    state: _EvaluationState,
) -> dict[str, HolisticClassification | None]:
    result: dict[str, HolisticClassification | None] = {"dehydration": None, "persistence": None, "dysentery": None}
    if encounter.patient_facts.has_diarrhoea is not True:
        return result
    obs = encounter.diarrhoea or HolisticDiarrhoeaObservations()
    if obs.duration_days is None:
        state.add_missing(MajorAssessment.DIARRHOEA, "diarrhoea.duration_days")
    if obs.blood_in_stool is None:
        state.add_missing(MajorAssessment.DIARRHOEA, "diarrhoea.blood_in_stool")
    positive_drinking_reuse = (
        obs.dehydration.drinking_status is None
        and encounter.danger_signs.unable_to_drink_or_breastfeed is True
    )
    for name in ("restless_or_irritable", "sunken_eyes", "drinking_status", "skin_pinch"):
        if name == "drinking_status" and positive_drinking_reuse:
            continue
        if getattr(obs.dehydration, name) is None:
            state.add_missing(MajorAssessment.DIARRHOEA, f"diarrhoea.dehydration.{name}")

    dehydration_observations = (
        replace(obs.dehydration, drinking_status=DrinkingStatus.UNABLE)
        if positive_drinking_reuse
        else obs.dehydration
    )
    dehydration = _dehydration_classification(
        dehydration_observations,
        encounter.danger_signs.lethargic_or_unconscious,
    )
    if dehydration is not None and encounter.danger_signs.lethargic_or_unconscious is not None:
        rule_id = {
            HolisticClassification.SEVERE_DEHYDRATION: "IMCI-MSC-DIARRHOEA-SEVERE-DEHYDRATION",
            HolisticClassification.SOME_DEHYDRATION: "IMCI-MSC-DIARRHOEA-SOME-DEHYDRATION",
            HolisticClassification.NO_DEHYDRATION: "IMCI-MSC-DIARRHOEA-NO-DEHYDRATION",
        }[dehydration]
        state.classify(MajorAssessment.DIARRHOEA, dehydration, rule_id)
        result["dehydration"] = dehydration

    if obs.duration_days is not None and obs.duration_days >= 14 and dehydration is not None:
        persistence = (
            HolisticClassification.SEVERE_PERSISTENT_DIARRHOEA
            if dehydration is not HolisticClassification.NO_DEHYDRATION
            else HolisticClassification.PERSISTENT_DIARRHOEA
        )
        rule_id = (
            "IMCI-MSC-DIARRHOEA-SEVERE-PERSISTENT"
            if persistence is HolisticClassification.SEVERE_PERSISTENT_DIARRHOEA
            else "IMCI-MSC-DIARRHOEA-PERSISTENT"
        )
        state.classify(MajorAssessment.DIARRHOEA, persistence, rule_id)
        result["persistence"] = persistence
    if obs.blood_in_stool is True:
        rule_id = "IMCI-MSC-DIARRHOEA-DYSENTERY"
        state.classify(MajorAssessment.DIARRHOEA, HolisticClassification.DYSENTERY, rule_id)
        result["dysentery"] = HolisticClassification.DYSENTERY
    return result


def _measles_active(obs: HolisticFeverObservations) -> bool | None:
    if obs.measles_within_last_3_months is True:
        return True
    values = (obs.generalized_rash, obs.measles_cough, obs.runny_nose, obs.red_eyes)
    if any(value is None for value in values):
        return None
    return obs.generalized_rash is True and any(value is True for value in values[1:])


def _evaluate_fever(
    encounter: HolisticEncounter,
    state: _EvaluationState,
) -> dict[str, HolisticClassification | None]:
    result: dict[str, HolisticClassification | None] = {"fever": None, "measles": None}
    if encounter.patient_facts.has_fever is not True:
        return result
    obs = encounter.fever or HolisticFeverObservations()
    required = (
        "temperature_c",
        "malaria_risk",
        "fever_duration_days",
        "stiff_neck",
        "runny_nose",
        "obvious_cause_of_fever_present",
        "identified_bacterial_cause_present",
        "measles_within_last_3_months",
        "generalized_rash",
        "measles_cough",
        "red_eyes",
    )
    for name in required:
        if getattr(obs, name) is None:
            state.add_missing(MajorAssessment.FEVER, f"fever.{name}")
    if obs.fever_duration_days is not None and obs.fever_duration_days > 7 and obs.fever_present_every_day is None:
        state.add_missing(MajorAssessment.FEVER, "fever.fever_present_every_day")

    danger_known = bool(state.danger_signs)
    danger_complete = all(getattr(encounter.danger_signs, name) is not None for name in _DANGER_FIELDS)
    severe = danger_known or obs.stiff_neck is True
    if severe:
        rule_id = "IMCI-MSC-FEVER-VERY-SEVERE"
        state.classify(MajorAssessment.FEVER, HolisticClassification.VERY_SEVERE_FEBRILE_DISEASE, rule_id)
        result["fever"] = HolisticClassification.VERY_SEVERE_FEBRILE_DISEASE
    elif danger_complete and obs.stiff_neck is False and obs.malaria_risk is not None:
        if obs.malaria_risk is MalariaRisk.NONE_NO_TRAVEL:
            rule_id = "IMCI-MSC-FEVER-NO-MALARIA-RISK"
            state.classify(MajorAssessment.FEVER, HolisticClassification.FEVER, rule_id)
            result["fever"] = HolisticClassification.FEVER
        else:
            test_required = obs.malaria_risk is MalariaRisk.HIGH or obs.obvious_cause_of_fever_present is False
            if test_required:
                if obs.malaria_test_available is None:
                    state.add_missing(MajorAssessment.FEVER, "fever.malaria_test_available")
                elif obs.malaria_test_available and obs.malaria_test_result is None:
                    state.add_missing(MajorAssessment.FEVER, "fever.malaria_test_result")
                elif not obs.malaria_test_available or obs.malaria_test_result is MalariaTestResult.POSITIVE:
                    rule_id = "IMCI-MSC-FEVER-MALARIA"
                    state.classify(MajorAssessment.FEVER, HolisticClassification.MALARIA, rule_id)
                    result["fever"] = HolisticClassification.MALARIA
                elif obs.malaria_test_result is MalariaTestResult.NEGATIVE:
                    rule_id = "IMCI-MSC-FEVER-NO-MALARIA"
                    state.classify(MajorAssessment.FEVER, HolisticClassification.FEVER_NO_MALARIA, rule_id)
                    result["fever"] = HolisticClassification.FEVER_NO_MALARIA
            elif obs.obvious_cause_of_fever_present is True:
                rule_id = "IMCI-MSC-FEVER-NO-MALARIA"
                state.classify(MajorAssessment.FEVER, HolisticClassification.FEVER_NO_MALARIA, rule_id)
                result["fever"] = HolisticClassification.FEVER_NO_MALARIA

    measles = _measles_active(obs)
    if measles:
        for name in ("mouth_ulcers", "pus_draining_from_eye", "clouding_of_cornea"):
            if getattr(obs, name) is None:
                state.add_missing(MajorAssessment.FEVER, f"fever.{name}")
        if obs.mouth_ulcers is True and obs.mouth_ulcers_deep_or_extensive is None:
            state.add_missing(MajorAssessment.FEVER, "fever.mouth_ulcers_deep_or_extensive")
        if danger_known or obs.clouding_of_cornea is True or obs.mouth_ulcers_deep_or_extensive is True:
            rule_id = "IMCI-MSC-MEASLES-SEVERE-COMPLICATED"
            classification = HolisticClassification.SEVERE_COMPLICATED_MEASLES
        elif obs.pus_draining_from_eye is True or obs.mouth_ulcers is True:
            rule_id = "IMCI-MSC-MEASLES-EYE-OR-MOUTH-COMPLICATIONS"
            classification = HolisticClassification.MEASLES_WITH_EYE_OR_MOUTH_COMPLICATIONS
        elif all(
            value is False
            for value in (obs.mouth_ulcers, obs.pus_draining_from_eye, obs.clouding_of_cornea)
        ):
            rule_id = "IMCI-MSC-MEASLES"
            classification = HolisticClassification.MEASLES
        else:
            classification = None
            rule_id = ""
        if classification is not None:
            state.classify(MajorAssessment.FEVER, classification, rule_id)
            result["measles"] = classification
    return result


def _evaluate_ear(
    encounter: HolisticEncounter,
    state: _EvaluationState,
) -> HolisticClassification | None:
    if encounter.patient_facts.has_ear_problem is not True:
        return None
    obs = encounter.ear or HolisticEarObservations()
    for name in ("ear_pain", "ear_discharge_reported", "pus_draining_from_ear", "tender_swelling_behind_ear"):
        if getattr(obs, name) is None:
            state.add_missing(MajorAssessment.EAR_PROBLEM, f"ear.{name}")
    if obs.ear_discharge_reported is True and obs.ear_discharge_duration_days is None:
        state.add_missing(MajorAssessment.EAR_PROBLEM, "ear.ear_discharge_duration_days")
    if obs.tender_swelling_behind_ear is True:
        rule_id = "IMCI-MSC-EAR-MASTOIDITIS"
        classification = HolisticClassification.MASTOIDITIS
    elif obs.ear_pain is True or (
        obs.pus_draining_from_ear is True
        and (
            obs.ear_discharge_reported is False
            or (
                obs.ear_discharge_reported is True
                and obs.ear_discharge_duration_days is not None
                and obs.ear_discharge_duration_days < 14
            )
        )
    ):
        rule_id = "IMCI-MSC-EAR-ACUTE-INFECTION"
        classification = HolisticClassification.ACUTE_EAR_INFECTION
    elif (
        obs.pus_draining_from_ear is True
        and obs.ear_discharge_reported is True
        and obs.ear_discharge_duration_days is not None
        and obs.ear_discharge_duration_days >= 14
    ):
        rule_id = "IMCI-MSC-EAR-CHRONIC-INFECTION"
        classification = HolisticClassification.CHRONIC_EAR_INFECTION
    elif obs.ear_pain is False and obs.pus_draining_from_ear is False:
        rule_id = "IMCI-MSC-EAR-NO-INFECTION"
        classification = HolisticClassification.NO_EAR_INFECTION
    else:
        return None
    state.classify(MajorAssessment.EAR_PROBLEM, classification, rule_id)
    return classification


def _add_respiratory_actions(
    encounter: HolisticEncounter,
    state: _EvaluationState,
    classification: HolisticClassification | None,
) -> None:
    if encounter.patient_facts.has_cough_or_difficult_breathing is not True:
        return
    obs = encounter.respiratory or HolisticRespiratoryObservations()
    if classification is HolisticClassification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE:
        rule_id = next(
            trace.rule_id
            for trace in state.classifications
            if trace.pathway is MajorAssessment.RESPIRATORY
        )
        state.add_action(HolisticAction.GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC, rule_id, urgent=True)
        state.add_action(HolisticAction.URGENT_REFERRAL, rule_id, urgent=True)
    elif classification is HolisticClassification.PNEUMONIA:
        chest = obs.post_bronchodilator_chest_indrawing if obs.bronchodilator_trial_completed else obs.chest_indrawing
        rule_id = next(trace.rule_id for trace in state.classifications if trace.pathway is MajorAssessment.RESPIRATORY)
        hiv_chest_referral = chest is True and obs.hiv_exposed_or_infected is True
        if hiv_chest_referral:
            dependency_rule = "IMCI-MSC-RESP-HIV-CHEST-INDRAWING"
            state.add_action(
                HolisticAction.GIVE_FIRST_DOSE_AMOXICILLIN_AND_REFER,
                dependency_rule,
                effect=RuleEffect.MODIFIED,
                reason="HIV exposure/infection changes chest-indrawing pneumonia management",
            )
        elif chest is not True or obs.hiv_exposed_or_infected is False:
            state.add_action(HolisticAction.GIVE_ORAL_AMOXICILLIN_5_DAYS, rule_id)
        if not hiv_chest_referral:
            for action in (
                HolisticAction.SOOTHE_THROAT_AND_RELIEVE_COUGH,
                HolisticAction.ADVISE_WHEN_TO_RETURN_IMMEDIATELY,
                HolisticAction.FOLLOW_UP_3_DAYS,
            ):
                state.add_action(action, rule_id)
    elif classification is HolisticClassification.COUGH_OR_COLD:
        rule_id = "IMCI-MSC-RESP-COUGH-OR-COLD"
        for action in (
            HolisticAction.SOOTHE_THROAT_AND_RELIEVE_COUGH,
            HolisticAction.ADVISE_WHEN_TO_RETURN_IMMEDIATELY,
            HolisticAction.FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING,
        ):
            state.add_action(action, rule_id)

    if obs.wheezing is True and classification is not None:
        state.add_action(
            HolisticAction.GIVE_INHALED_BRONCHODILATOR_5_DAYS,
            "IMCI-MSC-RESP-WHEEZE-HOME-TREATMENT",
        )
    if (obs.cough_duration_days is not None and obs.cough_duration_days > 14) or obs.recurrent_wheeze is True:
        state.add_action(
            HolisticAction.REFER_FOR_TB_OR_ASTHMA_ASSESSMENT,
            "IMCI-MSC-RESP-PROLONGED-OR-RECURRENT",
        )
    if obs.pulse_oximeter_available is True and obs.oxygen_saturation_percent is not None:
        if obs.oxygen_saturation_percent < 90:
            state.add_action(
                HolisticAction.REFER_FOR_OXYGEN_SATURATION_BELOW_90,
                "IMCI-MSC-RESP-OXYGEN-SATURATION",
                urgent=True,
            )


def _add_diarrhoea_actions(
    encounter: HolisticEncounter,
    state: _EvaluationState,
    results: dict[str, HolisticClassification | None],
    severe_elsewhere: bool,
) -> None:
    if encounter.patient_facts.has_diarrhoea is not True:
        return
    obs = encounter.diarrhoea or HolisticDiarrhoeaObservations()
    dehydration = results["dehydration"]
    if dehydration is HolisticClassification.SEVERE_DEHYDRATION:
        rule_id = "IMCI-MSC-DIARRHOEA-SEVERE-DEHYDRATION"
        if severe_elsewhere:
            for action in (
                HolisticAction.URGENT_REFERRAL,
                HolisticAction.FREQUENT_ORS_SIPS_DURING_REFERRAL,
                HolisticAction.CONTINUE_BREASTFEEDING,
            ):
                state.add_action(action, rule_id, urgent=True)
        else:
            state.add_action(HolisticAction.GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C, rule_id, intermediate=True)
            state.add_action(HolisticAction.REASSESS_DEHYDRATION_AFTER_PLAN_C, rule_id, intermediate=True)
        if encounter.patient_facts.age_months is not None and encounter.patient_facts.age_months >= 24:
            if obs.cholera_in_area is None:
                state.add_missing(MajorAssessment.DIARRHOEA, "diarrhoea.cholera_in_area")
            elif obs.cholera_in_area:
                state.add_action(
                    HolisticAction.GIVE_CHOLERA_ANTIBIOTIC_PER_LOCAL_PROTOCOL,
                    "IMCI-MSC-DIARRHOEA-CHOLERA-CONTEXT",
                )
    elif dehydration is HolisticClassification.SOME_DEHYDRATION:
        rule_id = "IMCI-MSC-DIARRHOEA-SOME-DEHYDRATION"
        if severe_elsewhere:
            for action in (
                HolisticAction.URGENT_REFERRAL,
                HolisticAction.FREQUENT_ORS_SIPS_DURING_REFERRAL,
                HolisticAction.CONTINUE_BREASTFEEDING,
            ):
                state.add_action(action, rule_id, urgent=True)
        else:
            state.add_action(HolisticAction.GIVE_FLUID_ZINC_AND_FOOD_PLAN_B, rule_id, intermediate=True)
            state.add_action(HolisticAction.REASSESS_DEHYDRATION_AFTER_PLAN_B, rule_id, intermediate=True)
            state.add_action(HolisticAction.ADVISE_WHEN_TO_RETURN_IMMEDIATELY, rule_id)
            state.add_action(HolisticAction.FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING, rule_id)
    elif dehydration is HolisticClassification.NO_DEHYDRATION:
        rule_id = "IMCI-MSC-DIARRHOEA-NO-DEHYDRATION"
        for action in (
            HolisticAction.GIVE_FLUID_ZINC_AND_FOOD_PLAN_A,
            HolisticAction.ADVISE_WHEN_TO_RETURN_IMMEDIATELY,
            HolisticAction.FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING,
        ):
            state.add_action(action, rule_id)

    if results["persistence"] is HolisticClassification.SEVERE_PERSISTENT_DIARRHOEA:
        rule_id = "IMCI-MSC-DIARRHOEA-SEVERE-PERSISTENT"
        if not severe_elsewhere:
            state.add_action(HolisticAction.TREAT_DEHYDRATION_BEFORE_REFERRAL, rule_id, intermediate=True)
        state.add_action(HolisticAction.REFER_TO_HOSPITAL, rule_id, urgent=True)
    elif results["persistence"] is HolisticClassification.PERSISTENT_DIARRHOEA:
        rule_id = "IMCI-MSC-DIARRHOEA-PERSISTENT"
        for action in (
            HolisticAction.ADVISE_FEEDING_FOR_PERSISTENT_DIARRHOEA,
            HolisticAction.GIVE_MULTIVITAMINS_MINERALS_ZINC_14_DAYS,
            HolisticAction.FOLLOW_UP_5_DAYS,
        ):
            state.add_action(action, rule_id)
    if results["dysentery"] is HolisticClassification.DYSENTERY:
        rule_id = "IMCI-MSC-DIARRHOEA-DYSENTERY"
        state.add_action(HolisticAction.GIVE_CIPROFLOXACIN_3_DAYS, rule_id)
        state.add_action(HolisticAction.FOLLOW_UP_3_DAYS, rule_id)


def _add_fever_actions(
    encounter: HolisticEncounter,
    state: _EvaluationState,
    results: dict[str, HolisticClassification | None],
) -> None:
    if encounter.patient_facts.has_fever is not True:
        return
    obs = encounter.fever or HolisticFeverObservations()
    fever = results["fever"]
    if fever is HolisticClassification.VERY_SEVERE_FEBRILE_DISEASE:
        rule_id = next(
            trace.rule_id
            for trace in state.classifications
            if trace.pathway is MajorAssessment.FEVER
            and trace.classification is HolisticClassification.VERY_SEVERE_FEBRILE_DISEASE
        )
        if obs.malaria_risk in {MalariaRisk.HIGH, MalariaRisk.LOW}:
            state.add_action(HolisticAction.GIVE_FIRST_DOSE_SEVERE_MALARIA_TREATMENT, rule_id, urgent=True)
        state.add_action(HolisticAction.GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC, rule_id, urgent=True)
        state.add_action(HolisticAction.PREVENT_LOW_BLOOD_SUGAR, rule_id, urgent=True)
        state.add_action(HolisticAction.URGENT_REFERRAL, rule_id, urgent=True)
    elif fever is HolisticClassification.MALARIA:
        rule_id = "IMCI-MSC-FEVER-MALARIA"
        state.add_action(HolisticAction.GIVE_FIRST_LINE_ORAL_ANTIMALARIAL, rule_id)
        state.add_action(HolisticAction.ADVISE_WHEN_TO_RETURN_IMMEDIATELY, rule_id)
        state.add_action(HolisticAction.FOLLOW_UP_3_DAYS_IF_FEVER_PERSISTS, rule_id)
    elif fever is HolisticClassification.FEVER_NO_MALARIA:
        rule_id = "IMCI-MSC-FEVER-NO-MALARIA"
        state.add_action(HolisticAction.ADVISE_WHEN_TO_RETURN_IMMEDIATELY, rule_id)
        state.add_action(HolisticAction.FOLLOW_UP_3_DAYS_IF_FEVER_PERSISTS, rule_id)
    elif fever is HolisticClassification.FEVER:
        rule_id = "IMCI-MSC-FEVER-NO-MALARIA-RISK"
        state.add_action(HolisticAction.ADVISE_WHEN_TO_RETURN_IMMEDIATELY, rule_id)
        state.add_action(HolisticAction.FOLLOW_UP_2_DAYS_IF_FEVER_PERSISTS, rule_id)

    if obs.temperature_c is not None and obs.temperature_c >= 38.5 and fever is not None:
        state.add_action(HolisticAction.GIVE_PARACETAMOL_FOR_HIGH_FEVER, "IMCI-MSC-FEVER-HIGH-TEMPERATURE")
    if obs.identified_bacterial_cause_present is True and fever is not None:
        state.add_action(
            HolisticAction.GIVE_APPROPRIATE_ANTIBIOTIC_FOR_IDENTIFIED_BACTERIAL_CAUSE,
            "IMCI-MSC-FEVER-IDENTIFIED-BACTERIAL-CAUSE",
        )
    if obs.fever_duration_days is not None and obs.fever_duration_days > 7 and obs.fever_present_every_day is True:
        state.add_action(
            HolisticAction.REFER_PROLONGED_FEVER_FOR_ASSESSMENT,
            "IMCI-MSC-FEVER-PROLONGED",
        )

    measles = results["measles"]
    if measles is None:
        return
    rule_id = {
        HolisticClassification.SEVERE_COMPLICATED_MEASLES: "IMCI-MSC-MEASLES-SEVERE-COMPLICATED",
        HolisticClassification.MEASLES_WITH_EYE_OR_MOUTH_COMPLICATIONS: "IMCI-MSC-MEASLES-EYE-OR-MOUTH-COMPLICATIONS",
        HolisticClassification.MEASLES: "IMCI-MSC-MEASLES",
    }[measles]
    state.add_action(HolisticAction.GIVE_VITAMIN_A_TREATMENT, rule_id)
    if measles is HolisticClassification.SEVERE_COMPLICATED_MEASLES:
        state.add_action(HolisticAction.GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC, rule_id, urgent=True)
        state.add_action(HolisticAction.URGENT_REFERRAL, rule_id, urgent=True)
    if obs.clouding_of_cornea is True or obs.pus_draining_from_eye is True:
        state.add_action(HolisticAction.APPLY_TETRACYCLINE_EYE_OINTMENT, rule_id)
    if obs.mouth_ulcers is True:
        state.add_action(HolisticAction.TREAT_MOUTH_ULCERS_WITH_GENTIAN_VIOLET, rule_id)
    if measles is HolisticClassification.MEASLES_WITH_EYE_OR_MOUTH_COMPLICATIONS:
        state.add_action(HolisticAction.FOLLOW_UP_3_DAYS, rule_id)


def _add_ear_actions(
    encounter: HolisticEncounter,
    state: _EvaluationState,
    classification: HolisticClassification | None,
) -> None:
    if encounter.patient_facts.has_ear_problem is not True or classification is None:
        return
    rule_id = {
        HolisticClassification.MASTOIDITIS: "IMCI-MSC-EAR-MASTOIDITIS",
        HolisticClassification.ACUTE_EAR_INFECTION: "IMCI-MSC-EAR-ACUTE-INFECTION",
        HolisticClassification.CHRONIC_EAR_INFECTION: "IMCI-MSC-EAR-CHRONIC-INFECTION",
        HolisticClassification.NO_EAR_INFECTION: "IMCI-MSC-EAR-NO-INFECTION",
    }[classification]
    if classification is HolisticClassification.MASTOIDITIS:
        for action in (
            HolisticAction.GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC,
            HolisticAction.GIVE_PARACETAMOL_FOR_EAR_PAIN,
            HolisticAction.URGENT_REFERRAL,
        ):
            state.add_action(action, rule_id, urgent=True)
    elif classification is HolisticClassification.ACUTE_EAR_INFECTION:
        for action in (
            HolisticAction.GIVE_ANTIBIOTIC_5_DAYS,
            HolisticAction.GIVE_PARACETAMOL_FOR_EAR_PAIN,
            HolisticAction.DRY_EAR_BY_WICKING,
            HolisticAction.FOLLOW_UP_5_DAYS,
        ):
            state.add_action(action, rule_id)
    elif classification is HolisticClassification.CHRONIC_EAR_INFECTION:
        for action in (
            HolisticAction.DRY_EAR_BY_WICKING,
            HolisticAction.GIVE_TOPICAL_QUINOLONE_EARDROPS_14_DAYS,
            HolisticAction.FOLLOW_UP_5_DAYS,
        ):
            state.add_action(action, rule_id)
    else:
        state.add_action(HolisticAction.NO_EAR_TREATMENT, rule_id)


def _validate_cross_field_consistency(encounter: HolisticEncounter, state: _EvaluationState) -> None:
    if (
        encounter.patient_facts.has_diarrhoea is True
        and encounter.diarrhoea is not None
        and encounter.diarrhoea.dehydration.restless_or_irritable is True
        and encounter.danger_signs.lethargic_or_unconscious is True
    ):
        state.contradictions.append("a child cannot be both lethargic/unconscious and restless/irritable")
    if (
        encounter.patient_facts.has_diarrhoea is True
        and encounter.diarrhoea is not None
        and encounter.diarrhoea.dehydration.drinking_status is DrinkingStatus.UNABLE
        and encounter.danger_signs.unable_to_drink_or_breastfeed is False
    ):
        state.contradictions.append("UNABLE observed drinking conflicts with a negative general danger sign")
    if encounter.respiratory is not None:
        obs = encounter.respiratory
        if obs.pulse_oximeter_available is False and obs.oxygen_saturation_percent is not None:
            state.contradictions.append("oxygen saturation was supplied while pulse oximetry was marked unavailable")
    if encounter.fever is not None:
        obs = encounter.fever
        if obs.malaria_test_available is False and obs.malaria_test_result is not None:
            state.contradictions.append("malaria test result was supplied while testing was marked unavailable")
