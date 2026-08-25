"""Typed, JSON-serializable benchmark case schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class StringEnum(str, Enum):
    """String-valued enum compatible with Python 3.10."""


class Pathway(StringEnum):
    GENERAL_DANGER_SIGNS = "general_danger_signs"
    RESPIRATORY = "respiratory"
    DEHYDRATION = "dehydration"


class Classification(StringEnum):
    VERY_SEVERE_DISEASE = "VERY_SEVERE_DISEASE"
    SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE = "SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE"
    PNEUMONIA = "PNEUMONIA"
    COUGH_OR_COLD = "COUGH_OR_COLD"
    SEVERE_DEHYDRATION = "SEVERE_DEHYDRATION"
    SOME_DEHYDRATION = "SOME_DEHYDRATION"
    NO_DEHYDRATION = "NO_DEHYDRATION"


class DangerSign(StringEnum):
    UNABLE_TO_DRINK_OR_BREASTFEED = "UNABLE_TO_DRINK_OR_BREASTFEED"
    VOMITS_EVERYTHING = "VOMITS_EVERYTHING"
    HAD_CONVULSIONS = "HAD_CONVULSIONS"
    LETHARGIC_OR_UNCONSCIOUS = "LETHARGIC_OR_UNCONSCIOUS"
    CONVULSING_NOW = "CONVULSING_NOW"


class Action(StringEnum):
    COMPLETE_ASSESSMENT_QUICKLY = "COMPLETE_ASSESSMENT_QUICKLY"
    GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY = "GIVE_PRE_REFERRAL_TREATMENT_IMMEDIATELY"
    PREVENT_LOW_BLOOD_SUGAR = "PREVENT_LOW_BLOOD_SUGAR"
    KEEP_WARM = "KEEP_WARM"
    URGENT_REFERRAL = "URGENT_REFERRAL"
    GIVE_DIAZEPAM_IF_CONVULSING_NOW = "GIVE_DIAZEPAM_IF_CONVULSING_NOW"
    GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC = "GIVE_FIRST_DOSE_APPROPRIATE_ANTIBIOTIC"
    GIVE_ORAL_AMOXICILLIN_5_DAYS = "GIVE_ORAL_AMOXICILLIN_5_DAYS"
    SOOTHE_THROAT_AND_RELIEVE_COUGH = "SOOTHE_THROAT_AND_RELIEVE_COUGH"
    ADVISE_WHEN_TO_RETURN_IMMEDIATELY = "ADVISE_WHEN_TO_RETURN_IMMEDIATELY"
    FOLLOW_UP_3_DAYS = "FOLLOW_UP_3_DAYS"
    FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING = "FOLLOW_UP_5_DAYS_IF_NOT_IMPROVING"
    GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C = "GIVE_FLUID_FOR_SEVERE_DEHYDRATION_PLAN_C"
    GIVE_FLUID_ZINC_AND_FOOD_PLAN_B = "GIVE_FLUID_ZINC_AND_FOOD_PLAN_B"
    GIVE_FLUID_ZINC_AND_FOOD_PLAN_A = "GIVE_FLUID_ZINC_AND_FOOD_PLAN_A"
    FREQUENT_ORS_SIPS_DURING_REFERRAL = "FREQUENT_ORS_SIPS_DURING_REFERRAL"
    CONTINUE_BREASTFEEDING = "CONTINUE_BREASTFEEDING"


class ReferralRequirement(StringEnum):
    NONE = "NONE"
    URGENT = "URGENT"


class DrinkingStatus(StringEnum):
    NORMAL = "NORMAL"
    EAGER_OR_THIRSTY = "EAGER_OR_THIRSTY"
    POORLY = "POORLY"
    UNABLE = "UNABLE"


class SkinPinch(StringEnum):
    NORMAL = "NORMAL"
    SLOWLY = "SLOWLY"
    VERY_SLOWLY = "VERY_SLOWLY"


class GenerationCategory(StringEnum):
    NORMAL = "normal"
    BOUNDARY = "boundary"
    COUNTERFACTUAL_TWIN = "counterfactual_twin"
    DANGER_SIGN = "danger_sign"
    MISSING_INFORMATION = "missing_information"
    DISTRACTOR = "distractor"


@dataclass(frozen=True)
class PatientFacts:
    age_months: int
    has_cough_or_difficult_breathing: bool = False
    has_diarrhoea: bool = False

    def __post_init__(self) -> None:
        if not 2 <= self.age_months < 60:
            raise ValueError("age_months must be at least 2 and less than 60")


@dataclass(frozen=True)
class GeneralDangerSignObservations:
    unable_to_drink_or_breastfeed: bool | None = None
    vomits_everything: bool | None = None
    had_convulsions: bool | None = None
    lethargic_or_unconscious: bool | None = None
    convulsing_now: bool | None = None


@dataclass(frozen=True)
class RespiratoryObservations:
    respiratory_rate: int | None = None
    chest_indrawing: bool | None = None
    stridor_when_calm: bool | None = None

    def __post_init__(self) -> None:
        if self.respiratory_rate is not None and self.respiratory_rate < 0:
            raise ValueError("respiratory_rate cannot be negative")


@dataclass(frozen=True)
class DehydrationObservations:
    restless_or_irritable: bool | None = None
    sunken_eyes: bool | None = None
    drinking_status: DrinkingStatus | None = None
    skin_pinch: SkinPinch | None = None


@dataclass(frozen=True)
class ClinicalObservations:
    danger_signs: GeneralDangerSignObservations
    respiratory: RespiratoryObservations | None = None
    dehydration: DehydrationObservations | None = None

    def __post_init__(self) -> None:
        if (
            self.dehydration is not None
            and self.danger_signs.lethargic_or_unconscious is True
            and self.dehydration.restless_or_irritable is True
        ):
            raise ValueError("a child cannot be both lethargic/unconscious and restless/irritable")
        if self.dehydration is not None and self.dehydration.drinking_status is DrinkingStatus.UNABLE:
            if self.danger_signs.unable_to_drink_or_breastfeed is False:
                raise ValueError("UNABLE drinking status conflicts with a negative general danger sign")


@dataclass(frozen=True)
class EvaluationResult:
    detected_danger_signs: tuple[DangerSign, ...] = ()
    classifications: dict[Pathway, Classification] = field(default_factory=dict)
    referral: ReferralRequirement = ReferralRequirement.NONE
    actions: tuple[Action, ...] = ()
    missing_required_observations: tuple[str, ...] = ()
    fired_rule_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "detected_danger_signs": [item.value for item in self.detected_danger_signs],
            "classifications": {key.value: value.value for key, value in self.classifications.items()},
            "referral": self.referral.value,
            "actions": [item.value for item in self.actions],
            "missing_required_observations": list(self.missing_required_observations),
            "fired_rule_ids": list(self.fired_rule_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationResult":
        return cls(
            detected_danger_signs=tuple(DangerSign(item) for item in data.get("detected_danger_signs", [])),
            classifications={Pathway(key): Classification(value) for key, value in data.get("classifications", {}).items()},
            referral=ReferralRequirement(data.get("referral", "NONE")),
            actions=tuple(Action(item) for item in data.get("actions", [])),
            missing_required_observations=tuple(data.get("missing_required_observations", [])),
            fired_rule_ids=tuple(data.get("fired_rule_ids", [])),
        )


@dataclass(frozen=True)
class SourceProvenance:
    document: str
    edition: str
    source_pdf_pages: tuple[int, ...]
    source_printed_pages: tuple[str, ...]
    source_rule_ids: tuple[str, ...]


@dataclass(frozen=True)
class GenerationMetadata:
    generator_version: str
    seed: int
    categories: tuple[GenerationCategory, ...]
    rule_family: str
    logic_signature: str
    template_family: str
    counterfactual_group_id: str | None = None


@dataclass(frozen=True)
class ClinicalCase:
    case_id: str
    patient_facts: PatientFacts
    presentation: str
    observations: ClinicalObservations
    known_missing_information: tuple[str, ...]
    expected_result: EvaluationResult | None
    provenance: SourceProvenance
    generation: GenerationMetadata

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("case_id is required")
        if not self.presentation.strip():
            raise ValueError("presentation is required")

    def to_dict(self, *, include_expected: bool = True) -> dict[str, Any]:
        data = asdict(self)
        data["observations"]["dehydration"] = _enum_values(data["observations"]["dehydration"])
        data["generation"]["categories"] = [item.value for item in self.generation.categories]
        data["provenance"]["source_pdf_pages"] = list(self.provenance.source_pdf_pages)
        data["provenance"]["source_printed_pages"] = list(self.provenance.source_printed_pages)
        data["provenance"]["source_rule_ids"] = list(self.provenance.source_rule_ids)
        data["known_missing_information"] = list(self.known_missing_information)
        if include_expected:
            data["expected_result"] = self.expected_result.to_dict() if self.expected_result else None
        else:
            data.pop("expected_result", None)
            data.pop("provenance", None)
            data.pop("generation", None)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClinicalCase":
        observations = data["observations"]
        respiratory_data = observations.get("respiratory")
        dehydration_data = observations.get("dehydration")
        provenance = data["provenance"]
        generation = data["generation"]
        return cls(
            case_id=data["case_id"],
            patient_facts=PatientFacts(**data["patient_facts"]),
            presentation=data["presentation"],
            observations=ClinicalObservations(
                danger_signs=GeneralDangerSignObservations(**observations["danger_signs"]),
                respiratory=RespiratoryObservations(**respiratory_data) if respiratory_data is not None else None,
                dehydration=DehydrationObservations(
                    restless_or_irritable=dehydration_data.get("restless_or_irritable"),
                    sunken_eyes=dehydration_data.get("sunken_eyes"),
                    drinking_status=DrinkingStatus(dehydration_data["drinking_status"]) if dehydration_data.get("drinking_status") else None,
                    skin_pinch=SkinPinch(dehydration_data["skin_pinch"]) if dehydration_data.get("skin_pinch") else None,
                ) if dehydration_data is not None else None,
            ),
            known_missing_information=tuple(data.get("known_missing_information", [])),
            expected_result=EvaluationResult.from_dict(data["expected_result"]) if data.get("expected_result") else None,
            provenance=SourceProvenance(
                document=provenance["document"],
                edition=provenance["edition"],
                source_pdf_pages=tuple(provenance["source_pdf_pages"]),
                source_printed_pages=tuple(provenance["source_printed_pages"]),
                source_rule_ids=tuple(provenance["source_rule_ids"]),
            ),
            generation=GenerationMetadata(
                generator_version=generation["generator_version"],
                seed=generation["seed"],
                categories=tuple(GenerationCategory(item) for item in generation["categories"]),
                rule_family=generation["rule_family"],
                logic_signature=generation["logic_signature"],
                template_family=generation["template_family"],
                counterfactual_group_id=generation.get("counterfactual_group_id"),
            ),
        )


def _enum_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _enum_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_enum_values(item) for item in value]
    if isinstance(value, StringEnum):
        return value.value
    return value
