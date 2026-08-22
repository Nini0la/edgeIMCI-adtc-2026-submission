"""Versioned whole-encounter schemas for the major sick-child IMCI scope.

These types intentionally do not replace the frozen ``ClinicalCase`` contract.
They preserve UNKNOWN as ``None`` and support the five major assessment areas
for children aged 2 completed months to under 5 years.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from edge_imci.schemas.case import DrinkingStatus, GeneralDangerSignObservations, SkinPinch, StringEnum


HOLISTIC_SCHEMA_VERSION = "edge-imci-major-sick-child-encounter-v1"


class MajorAssessment(StringEnum):
    ENCOUNTER = "supported_encounter"
    GENERAL_DANGER_SIGNS = "general_danger_signs"
    RESPIRATORY = "respiratory"
    DIARRHOEA = "diarrhoea"
    FEVER = "fever"
    EAR_PROBLEM = "ear_problem"


class HolisticClassification(StringEnum):
    VERY_SEVERE_DISEASE = "VERY_SEVERE_DISEASE"
    SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE = "SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE"
    PNEUMONIA = "PNEUMONIA"
    COUGH_OR_COLD = "COUGH_OR_COLD"
    SEVERE_DEHYDRATION = "SEVERE_DEHYDRATION"
    SOME_DEHYDRATION = "SOME_DEHYDRATION"
    NO_DEHYDRATION = "NO_DEHYDRATION"
    SEVERE_PERSISTENT_DIARRHOEA = "SEVERE_PERSISTENT_DIARRHOEA"
    PERSISTENT_DIARRHOEA = "PERSISTENT_DIARRHOEA"
    DYSENTERY = "DYSENTERY"
    VERY_SEVERE_FEBRILE_DISEASE = "VERY_SEVERE_FEBRILE_DISEASE"
    MALARIA = "MALARIA"
    FEVER_NO_MALARIA = "FEVER_NO_MALARIA"
    FEVER = "FEVER"
    SEVERE_COMPLICATED_MEASLES = "SEVERE_COMPLICATED_MEASLES"
    MEASLES_WITH_EYE_OR_MOUTH_COMPLICATIONS = "MEASLES_WITH_EYE_OR_MOUTH_COMPLICATIONS"
    MEASLES = "MEASLES"
    MASTOIDITIS = "MASTOIDITIS"
    ACUTE_EAR_INFECTION = "ACUTE_EAR_INFECTION"
    CHRONIC_EAR_INFECTION = "CHRONIC_EAR_INFECTION"
    NO_EAR_INFECTION = "NO_EAR_INFECTION"


class HolisticAction(StringEnum):
    COMPLETE_ASSESSMENT_QUICKLY = "COMPLETE_ASSESSMENT_QUICKLY"
    GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY = "GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY"
    PREVENT_LOW_BLOOD_SUGAR = "PREVENT_LOW_BLOOD_SUGAR"
    KEEP_WARM = "KEEP_WARM"
    URGENT_REFERRAL = "URGENT_REFERRAL"
    REFER_TO_HOSPITAL = "REFER_TO_HOSPITAL"
    GIVE_DIAZEPAM_IF_CONVULSING_NOW = "GIVE_DIAZEPAM_IF_CONVULSING_NOW"
    GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC = "GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC"
    GIVE_ORAL_AMOXICILLIN_5_DAYS = "GIVE_ORAL_AMOXICILLIN_5_DAYS"
    GIVE_FIRST_DOSE_AMOXICILLIN_AND_REFER = "GIVE_FIRST_DOSE_AMOXICILLIN_AND_REFER"
    GIVE_RAPID_ACTING_INHALED_BRONCHODILATOR_TRIAL = "GIVE_RAPID_ACTING_INHALED_BRONCHODILATOR_TRIAL"
    REASSESS_BREATHING_AFTER_BRONCHODILATOR = "REASSESS_BREATHING_AFTER_BRONCHODILATOR"
    GIVE_INHALED_BRONCHODILATOR_5_DAYS = "GIVE_INHALED_BRONCHODILATOR_5_DAYS"
    REFER_FOR_TB_OR_ASTHMA_ASSESSMENT = "REFER_FOR_TB_OR_ASTHMA_ASSESSMENT"
    REFER_FOR_OXYGEN_SATURATION_BELOW_90 = "REFER_FOR_OXYGEN_SATURATION_BELOW_90"
    SOOTHE_THROAT_AND_RELIEVE_COUGH = "SOOTHE_THROAT_AND_RELIEVE_COUGH"
    ADVISE_WHEN_TO_RETURN_IMMEDIATELY = "ADVISE_WHEN_TO_RETURN_IMMEDIATELY"
    FOLLOW_UP_2_DAYS_IF_FEVER_PERSISTS = "FOLLOW_UP_2_DAYS_IF_FEVER_PERSISTS"
    FOLLOW_UP_3_DAYS = "FOLLOW_UP_3_DAYS"
    FOLLOW_UP_3_DAYS_IF_FEVER_PERSISTS = "FOLLOW_UP_3_DAYS_IF_FEVER_PERSISTS"
    FOLLOW_UP_5_DAYS = "FOLLOW_UP_5_DAYS"
    FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING = "FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING"
    GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C = "GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C"
    GIVE_FLUID_ZINC_AND_FOOD_PLAN_B = "GIVE_FLUID_ZINC_AND_FOOD_PLAN_B"
    GIVE_FLUID_ZINC_AND_FOOD_PLAN_A = "GIVE_FLUID_ZINC_AND_FOOD_PLAN_A"
    FREQUENT_ORS_SIPS_DURING_REFERRAL = "FREQUENT_ORS_SIPS_DURING_REFERRAL"
    CONTINUE_BREASTFEEDING = "CONTINUE_BREASTFEEDING"
    TREAT_DEHYDRATION_BEFORE_REFERRAL = "TREAT_DEHYDRATION_BEFORE_REFERRAL"
    ADVISE_FEEDING_FOR_PERSISTENT_DIARRHOEA = "ADVISE_FEEDING_FOR_PERSISTENT_DIARRHOEA"
    GIVE_MULTIVITAMINS_MINERALS_ZINC_14_DAYS = "GIVE_MULTIVITAMINS_MINERALS_ZINC_14_DAYS"
    GIVE_CIPROFLOXACIN_3_DAYS = "GIVE_CIPROFLOXACIN_3_DAYS"
    GIVE_CHOLERA_ANTIBIOTIC_PER_LOCAL_PROTOCOL = "GIVE_CHOLERA_ANTIBIOTIC_PER_LOCAL_PROTOCOL"
    REASSESS_DEHYDRATION_AFTER_PLAN_B = "REASSESS_DEHYDRATION_AFTER_PLAN_B"
    REASSESS_DEHYDRATION_AFTER_PLAN_C = "REASSESS_DEHYDRATION_AFTER_PLAN_C"
    GIVE_FIRST_DOSE_SEVERE_MALARIA_TREATMENT = "GIVE_FIRST_DOSE_SEVERE_MALARIA_TREATMENT"
    GIVE_FIRST_LINE_ORAL_ANTIMALARIAL = "GIVE_FIRST_LINE_ORAL_ANTIMALARIAL"
    GIVE_PARACETAMOL_FOR_HIGH_FEVER = "GIVE_PARACETAMOL_FOR_HIGH_FEVER"
    GIVE_PARACETAMOL_FOR_EAR_PAIN = "GIVE_PARACETAMOL_FOR_EAR_PAIN"
    GIVE_APPROPRIATE_ANTIBIOTIC_FOR_IDENTIFIED_BACTERIAL_CAUSE = "GIVE_APPROPRIATE_ANTIBIOTIC_FOR_IDENTIFIED_BACTERIAL_CAUSE"
    REFER_PROLONGED_FEVER_FOR_ASSESSMENT = "REFER_PROLONGED_FEVER_FOR_ASSESSMENT"
    GIVE_VITAMIN_A_TREATMENT = "GIVE_VITAMIN_A_TREATMENT"
    APPLY_TETRACYCLINE_EYE_OINTMENT = "APPLY_TETRACYCLINE_EYE_OINTMENT"
    TREAT_MOUTH_ULCERS_WITH_GENTIAN_VIOLET = "TREAT_MOUTH_ULCERS_WITH_GENTIAN_VIOLET"
    GIVE_ANTIBIOTIC_5_DAYS = "GIVE_ANTIBIOTIC_5_DAYS"
    DRY_EAR_BY_WICKING = "DRY_EAR_BY_WICKING"
    GIVE_TOPICAL_QUINOLONE_EARDROPS_14_DAYS = "GIVE_TOPICAL_QUINOLONE_EARDROPS_14_DAYS"
    NO_EAR_TREATMENT = "NO_EAR_TREATMENT"


class MalariaRisk(StringEnum):
    HIGH = "HIGH"
    LOW = "LOW"
    NONE_NO_TRAVEL = "NONE_NO_TRAVEL"


class MalariaTestResult(StringEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


class RehydrationStage(StringEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    REASSESSMENT_COMPLETE = "REASSESSMENT_COMPLETE"


class RuleEffect(StringEnum):
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    SUPPRESSED = "SUPPRESSED"
    OVERRIDDEN = "OVERRIDDEN"


@dataclass(frozen=True)
class HolisticPatientFacts:
    age_months: int | None
    has_cough_or_difficult_breathing: bool | None
    has_diarrhoea: bool | None
    has_fever: bool | None
    has_ear_problem: bool | None

    def __post_init__(self) -> None:
        if self.age_months is not None and not 2 <= self.age_months < 60:
            raise ValueError("age_months must be at least 2 and less than 60")


@dataclass(frozen=True)
class HolisticRespiratoryObservations:
    cough_duration_days: int | None = None
    respiratory_rate: int | None = None
    chest_indrawing: bool | None = None
    stridor_when_calm: bool | None = None
    wheezing: bool | None = None
    recurrent_wheeze: bool | None = None
    child_calm: bool | None = None
    breaths_counted_one_minute: bool | None = None
    pulse_oximeter_available: bool | None = None
    oxygen_saturation_percent: float | None = None
    hiv_exposed_or_infected: bool | None = None
    bronchodilator_trial_completed: bool | None = None
    post_bronchodilator_respiratory_rate: int | None = None
    post_bronchodilator_chest_indrawing: bool | None = None
    post_bronchodilator_child_calm: bool | None = None
    post_bronchodilator_breaths_counted_one_minute: bool | None = None

    def __post_init__(self) -> None:
        for name in ("cough_duration_days", "respiratory_rate", "post_bronchodilator_respiratory_rate"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.oxygen_saturation_percent is not None and not 0 <= self.oxygen_saturation_percent <= 100:
            raise ValueError("oxygen_saturation_percent must be between 0 and 100")


@dataclass(frozen=True)
class DehydrationAssessment:
    restless_or_irritable: bool | None = None
    sunken_eyes: bool | None = None
    drinking_status: DrinkingStatus | None = None
    skin_pinch: SkinPinch | None = None


@dataclass(frozen=True)
class PostRehydrationAssessment:
    lethargic_or_unconscious: bool | None = None
    restless_or_irritable: bool | None = None
    sunken_eyes: bool | None = None
    drinking_status: DrinkingStatus | None = None
    skin_pinch: SkinPinch | None = None


@dataclass(frozen=True)
class HolisticDiarrhoeaObservations:
    duration_days: int | None = None
    blood_in_stool: bool | None = None
    dehydration: DehydrationAssessment = field(default_factory=DehydrationAssessment)
    cholera_in_area: bool | None = None
    rehydration_stage: RehydrationStage | None = None
    post_rehydration: PostRehydrationAssessment | None = None

    def __post_init__(self) -> None:
        if self.duration_days is not None and self.duration_days < 0:
            raise ValueError("duration_days cannot be negative")


@dataclass(frozen=True)
class HolisticFeverObservations:
    temperature_c: float | None = None
    malaria_risk: MalariaRisk | None = None
    fever_duration_days: int | None = None
    fever_present_every_day: bool | None = None
    stiff_neck: bool | None = None
    runny_nose: bool | None = None
    obvious_cause_of_fever_present: bool | None = None
    identified_bacterial_cause_present: bool | None = None
    malaria_test_available: bool | None = None
    malaria_test_result: MalariaTestResult | None = None
    measles_within_last_3_months: bool | None = None
    generalized_rash: bool | None = None
    measles_cough: bool | None = None
    red_eyes: bool | None = None
    mouth_ulcers: bool | None = None
    mouth_ulcers_deep_or_extensive: bool | None = None
    pus_draining_from_eye: bool | None = None
    clouding_of_cornea: bool | None = None

    def __post_init__(self) -> None:
        if self.fever_duration_days is not None and self.fever_duration_days < 0:
            raise ValueError("fever_duration_days cannot be negative")


@dataclass(frozen=True)
class HolisticEarObservations:
    ear_pain: bool | None = None
    ear_discharge_reported: bool | None = None
    ear_discharge_duration_days: int | None = None
    pus_draining_from_ear: bool | None = None
    tender_swelling_behind_ear: bool | None = None

    def __post_init__(self) -> None:
        if self.ear_discharge_duration_days is not None and self.ear_discharge_duration_days < 0:
            raise ValueError("ear_discharge_duration_days cannot be negative")


@dataclass(frozen=True)
class HolisticEncounter:
    encounter_id: str
    patient_facts: HolisticPatientFacts
    danger_signs: GeneralDangerSignObservations
    respiratory: HolisticRespiratoryObservations | None = None
    diarrhoea: HolisticDiarrhoeaObservations | None = None
    fever: HolisticFeverObservations | None = None
    ear: HolisticEarObservations | None = None
    schema_version: str = HOLISTIC_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.encounter_id:
            raise ValueError("encounter_id is required")


@dataclass(frozen=True)
class ClassificationTrace:
    pathway: MajorAssessment
    classification: HolisticClassification
    rule_id: str
    stage: str = "INITIAL"


@dataclass(frozen=True)
class ActionTrace:
    action: HolisticAction
    rule_id: str
    effect: RuleEffect = RuleEffect.ADDED
    reason: str = ""


@dataclass(frozen=True)
class HolisticEvaluationResult:
    rule_set_id: str
    completeness_policy_id: str
    supported_encounter_complete: bool
    final_holistic_synthesis_authorized: bool
    urgent_action_required: bool
    internal_classifications: tuple[ClassificationTrace, ...] = ()
    final_classifications: tuple[ClassificationTrace, ...] = ()
    urgent_actions: tuple[HolisticAction, ...] = ()
    intermediate_actions: tuple[HolisticAction, ...] = ()
    deferred_actions: tuple[HolisticAction, ...] = ()
    final_actions: tuple[HolisticAction, ...] = ()
    action_trace: tuple[ActionTrace, ...] = ()
    fired_rule_ids: tuple[str, ...] = ()
    missing_elements: dict[MajorAssessment, tuple[str, ...]] = field(default_factory=dict)
    unresolved_question_ids: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.final_holistic_synthesis_authorized != self.supported_encounter_complete:
            raise ValueError("final holistic synthesis is authorized exactly when the supported encounter is complete")
        if not self.supported_encounter_complete and (self.final_classifications or self.final_actions):
            raise ValueError("incomplete encounters cannot expose final classifications or final actions")
        if self.urgent_action_required != bool(self.urgent_actions):
            raise ValueError("urgent_action_required must match urgent_actions")

    def to_dict(self) -> dict[str, Any]:
        return _enum_values(asdict(self))


def _enum_values(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {_enum_values(key): _enum_values(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_enum_values(item) for item in value]
    return value
