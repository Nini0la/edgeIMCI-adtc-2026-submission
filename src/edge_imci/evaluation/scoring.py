"""Objective competency scoring for structured benchmark predictions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from edge_imci.schemas.case import EvaluationResult
from edge_imci.schemas.prediction import ModelPrediction


@dataclass(frozen=True)
class CaseScore:
    sufficient_information_correct: bool
    classification_correct: bool
    danger_sign_handling: bool
    referral_correct: bool
    actions_correct: bool
    required_information_complete: bool
    no_unsupported_output: bool
    overall_pass: bool

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)


def score_prediction(prediction: ModelPrediction, expected: EvaluationResult) -> CaseScore:
    expected_data = expected.to_dict()
    prediction_data = prediction.to_dict()
    sufficient_information_correct = prediction.sufficient_information == (
        not expected.missing_required_observations
    )
    classification_correct = prediction_data["classifications"] == expected_data["classifications"]
    danger_sign_handling = set(prediction_data["detected_danger_signs"]) == set(
        expected_data["detected_danger_signs"]
    )
    referral_correct = prediction_data["referral"] == expected_data["referral"]
    actions_correct = set(prediction_data["actions"]) == set(expected_data["actions"])
    required_information_complete = set(prediction_data["missing_required_observations"]) == set(
        expected_data["missing_required_observations"]
    )

    expected_classifications = set(expected_data["classifications"].items())
    predicted_classification_items = set(prediction_data["classifications"].items())
    no_unsupported_output = (
        predicted_classification_items <= expected_classifications
        and set(prediction_data["actions"]) <= set(expected_data["actions"])
    )
    checks = (
        sufficient_information_correct,
        classification_correct,
        danger_sign_handling,
        referral_correct,
        actions_correct,
        required_information_complete,
        no_unsupported_output,
    )
    return CaseScore(
        sufficient_information_correct=sufficient_information_correct,
        classification_correct=classification_correct,
        danger_sign_handling=danger_sign_handling,
        referral_correct=referral_correct,
        actions_correct=actions_correct,
        required_information_complete=required_information_complete,
        no_unsupported_output=no_unsupported_output,
        overall_pass=all(checks),
    )


def failed_score() -> CaseScore:
    return CaseScore(False, False, False, False, False, False, False, False)


def aggregate_scores(scores: list[CaseScore]) -> dict[str, float | int]:
    if not scores:
        raise ValueError("cannot aggregate an empty score list")
    names = CaseScore.__dataclass_fields__.keys()
    aggregate: dict[str, float | int] = {name: sum(getattr(score, name) for score in scores) / len(scores) for name in names}
    aggregate["case_count"] = len(scores)
    aggregate["passed_cases"] = sum(score.overall_pass for score in scores)
    return aggregate
