"""Run an adapter against an internal benchmark and preserve auditable evidence."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from edge_imci.evaluation.parsing import ParseStatus, parse_model_output
from edge_imci.evaluation.scoring import aggregate_scores, failed_score, score_prediction
from edge_imci.inference.adapters import ModelAdapter
from edge_imci.schemas.case import Action, Classification, ClinicalCase, DangerSign, Pathway
from edge_imci.schemas.prediction import MissingObservation

PROMPT_VERSION = "edge-imci-structured-v2"
DEFAULT_BENCHMARK_VERSION = "edge-imci-development-regression-v0"


def build_prompt(case: ClinicalCase) -> str:
    input_json = json.dumps(case.to_dict(include_expected=False), sort_keys=True)
    return (
        f"CASE_ID: {case.case_id}\n"
        f"PROMPT_VERSION: {PROMPT_VERSION}\n"
        "Evaluate only the structured facts in CASE_INPUT. Return exactly one JSON object and no explanation.\n"
        "Required JSON types: sufficient_information is a boolean; detected_danger_signs is an array of enum "
        "strings; classifications is an object mapping pathway enum strings to classification enum strings; "
        "referral is one enum string; actions is an array of enum strings; missing_required_observations is an "
        "array of enum strings. Emit each required key exactly once and no other keys.\n"
        "sufficient_information must be true exactly when missing_required_observations is empty.\n"
        f"Classification pathways: {[item.value for item in Pathway]}.\n"
        f"Classification values: {[item.value for item in Classification]}.\n"
        f"Danger-sign values: {[item.value for item in DangerSign]}.\n"
        f"Action values: {[item.value for item in Action]}.\n"
        f"Missing-observation values: {[item.value for item in MissingObservation]}.\n"
        "referral must be NONE or URGENT and must agree with whether actions contains URGENT_REFERRAL. "
        "Arrays must not contain duplicates. Do not emit fired rule IDs.\n"
        f"CASE_INPUT: {input_json}\n"
    )


def run_baseline(
    cases: list[ClinicalCase],
    adapter: ModelAdapter,
    output_dir: str | Path,
    *,
    benchmark_version: str = DEFAULT_BENCHMARK_VERSION,
) -> dict[str, Any]:
    if not cases:
        raise ValueError("benchmark is empty")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    per_case: list[dict[str, Any]] = []
    scores = []
    total_latency_ms = 0.0
    parse_failure_count = 0
    generation_failure_count = 0
    for case in cases:
        if case.expected_result is None:
            raise ValueError(f"case {case.case_id} has no expected result")
        prompt = build_prompt(case)
        started = time.perf_counter_ns()
        raw_output = ""
        parsed_prediction: dict[str, Any] | None = None
        parse_status = "failure"
        parse_error: dict[str, str] | None = None
        input_token_count: int | None = None
        output_token_count: int | None = None
        generation_throughput: float | None = None
        try:
            generation = adapter.generate(prompt)
            raw_output = generation.text
            input_token_count = generation.input_token_count
            output_token_count = generation.output_token_count
            generation_throughput = generation.tokens_per_second
            parsed = parse_model_output(raw_output)
            parse_status = parsed.status.value
            if parsed.status is ParseStatus.SUCCESS:
                assert parsed.prediction is not None
                parsed_prediction = parsed.prediction.to_dict()
                score = score_prediction(parsed.prediction, case.expected_result)
            else:
                parse_failure_count += 1
                parse_error = {
                    "code": parsed.error_code or "parse_failure",
                    "message": parsed.error_message or "parse failed",
                }
                score = failed_score()
        except Exception as error:
            generation_failure_count += 1
            parse_status = "generation_error"
            parse_error = {
                "code": "generation_error",
                "message": f"{type(error).__name__}: {error}",
            }
            score = failed_score()
        latency_ms = (time.perf_counter_ns() - started) / 1_000_000
        total_latency_ms += latency_ms
        scores.append(score)
        per_case.append(
            {
                "case_id": case.case_id,
                "benchmark_version": benchmark_version,
                "prompt_version": PROMPT_VERSION,
                "categories": [item.value for item in case.generation.categories],
                "prompt": prompt,
                "raw_model_output": raw_output,
                "parsed_prediction": parsed_prediction,
                "expected_oracle_result": case.expected_result.to_dict(),
                "parse_status": parse_status,
                "parse_error": parse_error,
                "score": score.to_dict(),
                "overall_pass": score.overall_pass,
                "latency_ms": latency_ms,
                "input_token_count": input_token_count,
                "output_token_count": output_token_count,
                "generation_throughput_tokens_per_second": generation_throughput,
            }
        )

    run_artifact: dict[str, Any] = {
        "schema_version": "edge-imci-run-v1",
        "evaluation_kind": "internal_structured",
        "model_identifier": adapter.model_id,
        "model_metadata": adapter.model_metadata,
        "runtime_metadata": adapter.runtime_metadata,
        "benchmark_version": benchmark_version,
        "prompt_version": PROMPT_VERSION,
        "case_count": len(cases),
        "aggregate_scores": aggregate_scores(scores),
        "parse_failure_count": parse_failure_count,
        "parse_failure_rate": parse_failure_count / len(cases),
        "generation_failure_count": generation_failure_count,
        "total_latency_ms": total_latency_ms,
        "per_case": per_case,
    }
    (output_path / "run.json").write_text(
        json.dumps(run_artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return run_artifact
