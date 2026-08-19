from __future__ import annotations

import json

from edge_imci.evaluation.baseline import run_baseline
from edge_imci.evaluation.scoring import score_prediction
from edge_imci.generation.cases import generate_cases
from edge_imci.inference.adapters import MockOracleAdapter


def test_mock_adapter_runs_end_to_end(tmp_path):
    cases = generate_cases()
    adapter = MockOracleAdapter({case.case_id: case.expected_result for case in cases})

    artifact = run_baseline(cases, adapter, tmp_path)

    assert artifact["model_identifier"] == "mock-oracle"
    assert artifact["case_count"] == 82
    assert artifact["aggregate_scores"]["passed_cases"] == 82
    assert artifact["aggregate_scores"]["overall_pass"] == 1.0
    assert artifact["failures"] == 0
    assert json.loads((tmp_path / "run.json").read_text()) == artifact


def test_unsupported_classification_and_action_are_detected():
    case = next(case for case in generate_cases() if case.case_id == "resp_normal_cold_child")
    prediction = case.expected_result.to_dict()
    prediction["classifications"]["dehydration"] = "SEVERE_DEHYDRATION"
    prediction["actions"].append("URGENT_REFERRAL")

    score = score_prediction(prediction, case.expected_result)

    assert not score.classification_correct
    assert not score.actions_correct
    assert not score.no_unsupported_output
    assert not score.overall_pass


def test_invalid_adapter_output_is_recorded_as_failure(tmp_path):
    class InvalidAdapter:
        model_id = "invalid-test"

        def generate(self, prompt: str) -> str:
            return "not-json"

    artifact = run_baseline(generate_cases()[:1], InvalidAdapter(), tmp_path)

    assert artifact["failures"] == 1
    assert artifact["aggregate_scores"]["passed_cases"] == 0
    assert artifact["per_case"][0]["failure"].startswith("JSONDecodeError")
