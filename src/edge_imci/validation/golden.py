"""Isolated deterministic semantic checks for conservative golden targets.

This validator checks the controlled v1 language contract. It is intentionally
separate from both clinical and information-policy evaluation. Passing it is
not independent clinical proof; every golden record remains human-reviewable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from edge_imci.schemas.trajectory import ExpectedAssistantSemantics

VALIDATOR_ID = "golden-controlled-language-roundtrip-v1"

_CLASSIFICATION_PHRASES = {
    "The supported general danger-sign classification is very severe disease.": "general_danger_signs:VERY_SEVERE_DISEASE",
    "The supported respiratory classification is severe pneumonia or very severe disease.": "respiratory:SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE",
    "The supported respiratory classification is pneumonia.": "respiratory:PNEUMONIA",
    "The supported respiratory classification is cough or cold.": "respiratory:COUGH_OR_COLD",
    "The supported dehydration classification is severe dehydration.": "dehydration:SEVERE_DEHYDRATION",
    "The supported dehydration classification is some dehydration.": "dehydration:SOME_DEHYDRATION",
    "The supported dehydration classification is no dehydration.": "dehydration:NO_DEHYDRATION",
}
_ACTION_PHRASES = {
    "Complete the supported assessment quickly.": "COMPLETE_ASSESSMENT_QUICKLY",
    "Give the indicated pre-referral treatment immediately.": "GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY",
    "Prevent low blood sugar.": "PREVENT_LOW_BLOOD_SUGAR",
    "Keep the child warm.": "KEEP_WARM",
    "Arrange urgent referral.": "URGENT_REFERRAL",
    "Give diazepam because the child is convulsing now.": "GIVE_DIAZEPAM_IF_CONVULSING_NOW",
    "Give the first dose of an appropriate antibiotic.": "GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC",
    "Give oral amoxicillin for 5 days.": "GIVE_ORAL_AMOXICILLIN_5_DAYS",
    "Soothe the throat and relieve the cough with a safe remedy.": "SOOTHE_THROAT_AND_RELIEVE_COUGH",
    "Advise the caregiver when to return immediately.": "ADVISE_WHEN_TO_RETURN_IMMEDIATELY",
    "Follow up in 3 days.": "FOLLOW_UP_3_DAYS",
    "Follow up in 5 days if the child is not improving.": "FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING",
    "Give Plan C fluid for severe dehydration.": "GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C",
    "Give Plan B fluid, zinc, and food.": "GIVE_FLUID_ZINC_AND_FOOD_PLAN_B",
    "Give Plan A fluid, zinc, and food.": "GIVE_FLUID_ZINC_AND_FOOD_PLAN_A",
    "Give frequent sips of ORS during referral.": "FREQUENT_ORS_SIPS_DURING_REFERRAL",
    "Continue breastfeeding.": "CONTINUE_BREASTFEEDING",
}
_ACQUISITION_PHRASES = {
    "Confirm the child's age in completed months from the caregiver or record.": "patient_facts.age_months|HISTORY_OR_RECORD",
    "Ask the caregiver whether the child has cough or difficult breathing.": "patient_facts.has_cough_or_difficult_breathing|CAREGIVER_QUESTION",
    "Ask the caregiver whether the child has diarrhoea.": "patient_facts.has_diarrhoea|CAREGIVER_QUESTION",
    "Observe whether the child is convulsing now.": "danger_signs.convulsing_now|CLINICIAN_OBSERVATION",
    "Observe whether the child is lethargic or unconscious.": "danger_signs.lethargic_or_unconscious|CLINICIAN_OBSERVATION",
    "Ask the caregiver whether the child is unable to drink or breastfeed.": "danger_signs.unable_to_drink_or_breastfeed|CAREGIVER_QUESTION",
    "Ask the caregiver whether the child vomits everything.": "danger_signs.vomits_everything|CAREGIVER_QUESTION",
    "Ask the caregiver whether the child has had convulsions during this illness.": "danger_signs.had_convulsions|CAREGIVER_QUESTION",
    "When the child is calm, observe whether stridor is present.": "respiratory.stridor_when_calm|CLINICIAN_OBSERVATION",
    "When the child is calm, observe whether chest indrawing is present.": "respiratory.chest_indrawing|CLINICIAN_OBSERVATION",
    "When the child is calm, count breaths for one full minute and report the respiratory rate.": "respiratory.respiratory_rate|MEASUREMENT",
    "Observe whether the child is restless or irritable.": "dehydration.restless_or_irritable|CLINICIAN_OBSERVATION",
    "Observe whether the child's eyes are sunken.": "dehydration.sunken_eyes|CLINICIAN_OBSERVATION",
    "Offer fluid and observe whether the child drinks normally, eagerly or thirstily, poorly, or is unable to drink.": "dehydration.drinking_status|CLINICIAN_OBSERVATION",
    "Pinch the abdominal skin and observe how quickly it returns.": "dehydration.skin_pinch|CLINICIAN_OBSERVATION",
}
_DECISION_PHRASES = {
    "The available information is sufficient to determine the supported classification decision.": "SUFFICIENT",
    "More information is needed before the supported classification decision is determined.": "INSUFFICIENT",
    "The supported classification decision is blocked by unresolved evidence.": "BLOCKED",
}
_ACTION_SUFFICIENCY_PHRASES = {
    "The supported action set is determined.": True,
    "The complete supported action set is not yet determined.": False,
}
_ASSESSMENT_PHRASES = {
    "The supported assessment is complete.": True,
    "The supported assessment is not yet complete.": False,
}
_URGENT_PHRASE = "Urgent action is required now."


@dataclass(frozen=True)
class RoundTripValidation:
    validator_id: str
    expected_projection: dict[str, Any]
    extracted_projection: dict[str, Any]
    deterministic_match: bool
    human_review_required: bool
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "validator_id": self.validator_id,
            "expected_projection": self.expected_projection,
            "extracted_projection": self.extracted_projection,
            "deterministic_match": self.deterministic_match,
            "human_review_required": self.human_review_required,
            "limitations": list(self.limitations),
        }


def expected_projection(semantics: ExpectedAssistantSemantics) -> dict[str, Any]:
    acquisitions = [
        f"decision|{item.observation_id.value}|{item.acquisition_mode.value}"
        for item in semantics.decision_directed_acquisitions
    ]
    acquisitions.extend(
        f"assessment|{item.observation_id.value}|{item.acquisition_mode.value}"
        for item in semantics.assessment_completion_acquisitions
    )
    return {
        "classifications": sorted(f"{pathway.value}:{classification.value}" for pathway, classification in semantics.classifications.items()),
        "actions": sorted(item.value for item in semantics.actions),
        "decision_status": semantics.decision_status.value,
        "action_set_sufficient": semantics.action_set_sufficient,
        "assessment_complete": semantics.assessment_complete,
        "urgent_action_required": semantics.urgent_action_required,
        "acquisitions": sorted(acquisitions),
    }


def extract_target_semantics(text: str) -> dict[str, Any]:
    decision_status = _extract_single(text, _DECISION_PHRASES, "decision status")
    action_sufficient = _extract_single(text, _ACTION_SUFFICIENCY_PHRASES, "action sufficiency")
    assessment_complete = _extract_single(text, _ASSESSMENT_PHRASES, "assessment completeness")
    decision_section, assessment_section = _acquisition_sections(text)
    acquisitions = [
        f"decision|{value}"
        for phrase, value in _ACQUISITION_PHRASES.items()
        if phrase in decision_section
    ]
    acquisitions.extend(
        f"assessment|{value}"
        for phrase, value in _ACQUISITION_PHRASES.items()
        if phrase in assessment_section
    )
    return {
        "classifications": sorted(value for phrase, value in _CLASSIFICATION_PHRASES.items() if phrase in text),
        "actions": sorted(value for phrase, value in _ACTION_PHRASES.items() if phrase in text),
        "decision_status": decision_status,
        "action_set_sufficient": action_sufficient,
        "assessment_complete": assessment_complete,
        "urgent_action_required": _URGENT_PHRASE in text,
        "acquisitions": sorted(acquisitions),
    }


def validate_target_round_trip(
    text: str,
    semantics: ExpectedAssistantSemantics,
) -> RoundTripValidation:
    expected = expected_projection(semantics)
    extracted = extract_target_semantics(text)
    return RoundTripValidation(
        validator_id=VALIDATOR_ID,
        expected_projection=expected,
        extracted_projection=extracted,
        deterministic_match=extracted == expected,
        human_review_required=True,
        limitations=(
            "Controlled-language extraction is coupled to the conservative renderer and is not independent clinical review.",
            "Free-form semantic fidelity and naturalness still require human/domain-expert review.",
            "No external LLM extractor was used.",
        ),
    )


def _extract_single(text: str, mapping: dict[str, Any], label: str) -> Any:
    matches = [value for phrase, value in mapping.items() if phrase in text]
    if len(matches) != 1:
        raise ValueError(f"target must contain exactly one {label} phrase")
    return matches[0]


def _acquisition_sections(text: str) -> tuple[str, str]:
    decision_marker = "Acquire next:"
    assessment_marker = "Assessment still to complete:"
    decision_start = text.find(decision_marker)
    assessment_start = text.find(assessment_marker)
    decision_section = ""
    assessment_section = ""
    if decision_start >= 0:
        decision_end = assessment_start if assessment_start > decision_start else len(text)
        decision_section = text[decision_start:decision_end]
    if assessment_start >= 0:
        assessment_section = text[assessment_start:]
    return decision_section, assessment_section
