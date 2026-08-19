"""Minimal model adapter boundary used by benchmark runners."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from edge_imci.schemas.case import EvaluationResult


@dataclass(frozen=True)
class GenerationOutput:
    text: str
    input_token_count: int | None = None
    output_token_count: int | None = None
    generation_seconds: float | None = None

    @property
    def tokens_per_second(self) -> float | None:
        if self.output_token_count is None or self.generation_seconds in (None, 0):
            return None
        return self.output_token_count / self.generation_seconds


class ModelAdapter(Protocol):
    @property
    def model_id(self) -> str:
        ...

    @property
    def model_metadata(self) -> dict[str, Any]:
        ...

    @property
    def runtime_metadata(self) -> dict[str, Any]:
        ...

    def generate(self, prompt: str) -> GenerationOutput:
        ...


class MockOracleAdapter:
    """Deterministic test adapter that returns supplied expected results by case ID."""

    def __init__(self, expected_by_case_id: dict[str, EvaluationResult]) -> None:
        self._expected_by_case_id = expected_by_case_id

    @property
    def model_id(self) -> str:
        return "mock-oracle"

    @property
    def model_metadata(self) -> dict[str, Any]:
        return {"model_id": self.model_id, "base_or_instruct": "mock"}

    @property
    def runtime_metadata(self) -> dict[str, Any]:
        return {"backend": "mock", "quantization": None, "dtype": None}

    def generate(self, prompt: str) -> GenerationOutput:
        first_line = prompt.splitlines()[0]
        prefix = "CASE_ID: "
        if not first_line.startswith(prefix):
            raise ValueError("prompt does not begin with CASE_ID")
        case_id = first_line.removeprefix(prefix)
        try:
            result = self._expected_by_case_id[case_id]
        except KeyError as error:
            raise ValueError(f"unknown case ID: {case_id}") from error
        prediction = result.to_dict()
        prediction["sufficient_information"] = not result.missing_required_observations
        prediction.pop("fired_rule_ids", None)
        return GenerationOutput(json.dumps(prediction, sort_keys=True))
