"""Minimal model adapter boundary used by benchmark runners."""

from __future__ import annotations

import json
from typing import Protocol

from edge_imci.schemas.case import EvaluationResult


class ModelAdapter(Protocol):
    @property
    def model_id(self) -> str:
        ...

    def generate(self, prompt: str) -> str:
        ...


class MockOracleAdapter:
    """Deterministic test adapter that returns supplied expected results by case ID."""

    def __init__(self, expected_by_case_id: dict[str, EvaluationResult]) -> None:
        self._expected_by_case_id = expected_by_case_id

    @property
    def model_id(self) -> str:
        return "mock-oracle"

    def generate(self, prompt: str) -> str:
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
        prediction.pop("fired_rule_ids", None)
        return json.dumps(prediction, sort_keys=True)
