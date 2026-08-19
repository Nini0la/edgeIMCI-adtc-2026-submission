"""Strict deterministic parser for generative model predictions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from edge_imci.schemas.case import Action, Classification, DangerSign, Pathway, ReferralRequirement, StringEnum
from edge_imci.schemas.prediction import MissingObservation, ModelPrediction

_REQUIRED_FIELDS = frozenset(
    {
        "sufficient_information",
        "detected_danger_signs",
        "classifications",
        "referral",
        "actions",
        "missing_required_observations",
    }
)
_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)
EnumT = TypeVar("EnumT", bound=StringEnum)


class ParseStatus(StringEnum):
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True)
class PredictionParseResult:
    status: ParseStatus
    prediction: ModelPrediction | None = None
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.status is ParseStatus.SUCCESS:
            if self.prediction is None or self.error_code is not None or self.error_message is not None:
                raise ValueError("successful parse result must contain only a prediction")
        elif self.prediction is not None or self.error_code is None or self.error_message is None:
            raise ValueError("failed parse result must contain only error details")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "prediction": self.prediction.to_dict() if self.prediction else None,
            "error": (
                {"code": self.error_code, "message": self.error_message}
                if self.error_code is not None
                else None
            ),
        }


class _ParseFailure(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class _DuplicateKey(ValueError):
    pass


def parse_model_output(raw_output: str) -> PredictionParseResult:
    try:
        prediction = _parse(raw_output)
    except _ParseFailure as error:
        return PredictionParseResult(
            status=ParseStatus.FAILURE,
            error_code=error.code,
            error_message=str(error),
        )
    return PredictionParseResult(status=ParseStatus.SUCCESS, prediction=prediction)


def _parse(raw_output: str) -> ModelPrediction:
    if not isinstance(raw_output, str) or not raw_output.strip():
        raise _ParseFailure("empty_output", "model output is empty")
    text = raw_output.strip()
    if text.startswith("```"):
        match = _FENCE.fullmatch(text)
        if match is None:
            raise _ParseFailure("invalid_wrapper", "Markdown fence must contain exactly one JSON object")
        text = match.group(1).strip()
    elif "```" in text:
        raise _ParseFailure("invalid_wrapper", "text surrounding a Markdown JSON fence is not allowed")

    try:
        decoded = json.loads(text, object_pairs_hook=_unique_object)
    except _DuplicateKey as error:
        raise _ParseFailure("duplicate_key", str(error)) from error
    except json.JSONDecodeError as error:
        raise _ParseFailure("invalid_json", f"invalid JSON: {error.msg}") from error
    if not isinstance(decoded, dict):
        raise _ParseFailure("invalid_top_level", "prediction must be a JSON object")

    actual_fields = frozenset(decoded)
    if actual_fields != _REQUIRED_FIELDS:
        missing = sorted(_REQUIRED_FIELDS - actual_fields)
        extra = sorted(actual_fields - _REQUIRED_FIELDS)
        raise _ParseFailure("invalid_fields", f"missing fields={missing}; extra fields={extra}")
    if type(decoded["sufficient_information"]) is not bool:
        raise _ParseFailure("invalid_type", "sufficient_information must be a boolean")

    classifications_raw = decoded["classifications"]
    if not isinstance(classifications_raw, dict):
        raise _ParseFailure("invalid_type", "classifications must be an object")
    try:
        prediction = ModelPrediction(
            sufficient_information=decoded["sufficient_information"],
            detected_danger_signs=_enum_list(decoded["detected_danger_signs"], DangerSign, "detected_danger_signs"),
            classifications={
                _enum_value(pathway, Pathway, "classifications key"): _enum_value(
                    classification, Classification, "classifications value"
                )
                for pathway, classification in classifications_raw.items()
            },
            referral=_enum_value(decoded["referral"], ReferralRequirement, "referral"),
            actions=_enum_list(decoded["actions"], Action, "actions"),
            missing_required_observations=_enum_list(
                decoded["missing_required_observations"],
                MissingObservation,
                "missing_required_observations",
            ),
        )
    except ValueError as error:
        raise _ParseFailure("invalid_prediction", str(error)) from error
    return prediction


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _enum_list(value: Any, enum_type: Callable[[str], EnumT], field_name: str) -> tuple[EnumT, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list of strings")
    return tuple(_enum_value(item, enum_type, field_name) for item in value)


def _enum_value(value: Any, enum_type: Callable[[str], EnumT], field_name: str) -> EnumT:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must contain strings")
    try:
        return enum_type(value)
    except ValueError as error:
        raise ValueError(f"unsupported {field_name}: {value}") from error
