from __future__ import annotations

import json

from edge_imci.evaluation.baseline import PROMPT_VERSION, run_baseline
from edge_imci.generation.cases import generate_cases
from edge_imci.inference.adapters import GenerationOutput, MockOracleAdapter


def test_mock_adapter_runs_end_to_end_with_complete_evidence(tmp_path):
    cases = generate_cases()
    adapter = MockOracleAdapter({case.case_id: case.expected_result for case in cases})

    artifact = run_baseline(cases, adapter, tmp_path)

    assert artifact["model_identifier"] == "mock-oracle"
    assert artifact["case_count"] == 82
    assert artifact["aggregate_scores"]["passed_cases"] == 82
    assert artifact["aggregate_scores"]["overall_pass"] == 1.0
    assert artifact["parse_failure_count"] == 0
    assert artifact["generation_failure_count"] == 0
    record = artifact["per_case"][0]
    assert record["benchmark_version"] == artifact["benchmark_version"]
    assert record["prompt_version"] == PROMPT_VERSION
    assert record["prompt"].startswith(f"CASE_ID: {record['case_id']}")
    assert record["raw_model_output"]
    assert record["parsed_prediction"] is not None
    assert record["expected_oracle_result"]
    assert record["parse_status"] == "success"
    assert record["parse_error"] is None
    assert record["overall_pass"]
    assert record["latency_ms"] >= 0
    assert "input_token_count" in record
    assert "output_token_count" in record
    assert "generation_throughput_tokens_per_second" in record
    assert json.loads((tmp_path / "run.json").read_text()) == artifact


def test_invalid_adapter_output_propagates_to_aggregate_failure_metrics(tmp_path):
    class InvalidAdapter:
        model_id = "invalid-test"
        model_metadata = {"model_id": model_id}
        runtime_metadata = {"backend": "test"}

        def generate(self, prompt: str) -> GenerationOutput:
            return GenerationOutput("not-json")

    artifact = run_baseline(generate_cases()[:1], InvalidAdapter(), tmp_path)

    assert artifact["parse_failure_count"] == 1
    assert artifact["parse_failure_rate"] == 1.0
    assert artifact["generation_failure_count"] == 0
    assert artifact["aggregate_scores"]["passed_cases"] == 0
    assert artifact["per_case"][0]["parse_status"] == "failure"
    assert artifact["per_case"][0]["parse_error"]["code"] == "invalid_json"
    assert not artifact["per_case"][0]["overall_pass"]


def test_generation_exception_is_preserved_as_failure(tmp_path):
    class BrokenAdapter:
        model_id = "broken-test"
        model_metadata = {"model_id": model_id}
        runtime_metadata = {"backend": "test"}

        def generate(self, prompt: str) -> GenerationOutput:
            raise RuntimeError("backend unavailable")

    artifact = run_baseline(generate_cases()[:1], BrokenAdapter(), tmp_path)

    assert artifact["generation_failure_count"] == 1
    assert artifact["per_case"][0]["parse_status"] == "generation_error"
    assert artifact["per_case"][0]["parse_error"]["message"] == "RuntimeError: backend unavailable"
