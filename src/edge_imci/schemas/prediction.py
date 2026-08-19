"""Typed model prediction contract derived from the deterministic oracle output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from edge_imci.schemas.case import (
    Action,
    Classification,
    DangerSign,
    Pathway,
    ReferralRequirement,
    StringEnum,
)


class MissingObservation(StringEnum):
    DANGER_UNABLE_TO_DRINK = "danger_signs.unable_to_drink_or_breastfeed"
    DANGER_VOMITS_EVERYTHING = "danger_signs.vomits_everything"
    DANGER_HAD_CONVULSIONS = "danger_signs.had_convulsions"
    DANGER_LETHARGIC_OR_UNCONSCIOUS = "danger_signs.lethargic_or_unconscious"
    DANGER_CONVULSING_NOW = "danger_signs.convulsing_now"
    RESPIRATORY_RATE = "respiratory.respiratory_rate"
    RESPIRATORY_CHEST_INDRAWING = "respiratory.chest_indrawing"
    RESPIRATORY_STRIDOR_WHEN_CALM = "respiratory.stridor_when_calm"
    DEHYDRATION_RESTLESS_OR_IRRITABLE = "dehydration.restless_or_irritable"
    DEHYDRATION_SUNKEN_EYES = "dehydration.sunken_eyes"
    DEHYDRATION_DRINKING_STATUS = "dehydration.drinking_status"
    DEHYDRATION_SKIN_PINCH = "dehydration.skin_pinch"
_CLASSIFICATIONS_BY_PATHWAY = {
    Pathway.GENERAL_DANGER_SIGNS: frozenset({Classification.VERY_SEVERE_DISEASE}),
    Pathway.RESPIRATORY: frozenset(
        {
            Classification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE,
            Classification.PNEUMONIA,
            Classification.COUGH_OR_COLD,
        }
    ),
    Pathway.DEHYDRATION: frozenset(
        {
            Classification.SEVERE_DEHYDRATION,
            Classification.SOME_DEHYDRATION,
            Classification.NO_DEHYDRATION,
        }
    ),
}




@dataclass(frozen=True)
class ModelPrediction:
    sufficient_information: bool
    detected_danger_signs: tuple[DangerSign, ...]
    classifications: dict[Pathway, Classification]
    referral: ReferralRequirement
    actions: tuple[Action, ...]
    missing_required_observations: tuple[MissingObservation, ...]

    def __post_init__(self) -> None:
        _require_unique(self.detected_danger_signs, "detected_danger_signs")
        _require_unique(self.actions, "actions")
        _require_unique(self.missing_required_observations, "missing_required_observations")
        for pathway, classification in self.classifications.items():
            if classification not in _CLASSIFICATIONS_BY_PATHWAY[pathway]:
                raise ValueError(f"classification {classification.value} is invalid for pathway {pathway.value}")
        if self.sufficient_information == bool(self.missing_required_observations):
            raise ValueError(
                "sufficient_information must be true exactly when missing_required_observations is empty"
            )
        urgent_action = Action.URGENT_REFERRAL in self.actions
        if (self.referral is ReferralRequirement.URGENT) != urgent_action:
            raise ValueError("referral and URGENT_REFERRAL action contradict each other")
        general_classification = self.classifications.get(Pathway.GENERAL_DANGER_SIGNS)
        if self.detected_danger_signs:
            if general_classification is not Classification.VERY_SEVERE_DISEASE:
                raise ValueError("detected danger signs require VERY_SEVERE_DISEASE classification")
            if self.referral is not ReferralRequirement.URGENT:
                raise ValueError("detected danger signs require urgent referral")
        elif general_classification is not None:
            raise ValueError("general danger-sign classification requires a detected danger sign")
        respiratory_classification = self.classifications.get(Pathway.RESPIRATORY)
        if (
            respiratory_classification is Classification.SEVERE_PNEUMONIA_OR_VERY_SEVERE_DISEASE
            and self.referral is not ReferralRequirement.URGENT
        ):
            raise ValueError("severe respiratory classification requires urgent referral")

    def to_dict(self) -> dict[str, Any]:
        return {
            "sufficient_information": self.sufficient_information,
            "detected_danger_signs": [item.value for item in self.detected_danger_signs],
            "classifications": {pathway.value: classification.value for pathway, classification in self.classifications.items()},
            "referral": self.referral.value,
            "actions": [item.value for item in self.actions],
            "missing_required_observations": [item.value for item in self.missing_required_observations],
        }


def _require_unique(values: tuple[object, ...], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} cannot contain duplicates")
