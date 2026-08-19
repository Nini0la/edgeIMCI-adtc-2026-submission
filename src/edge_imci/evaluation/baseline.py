"""Run an adapter against a benchmark and persist objective scores."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from edge_imci.evaluation.scoring import aggregate_scores, failed_score, score_prediction
from edge_imci.inference.adapters import ModelAdapter
from edge_imci.schemas.case import ClinicalCase


def build_prompt(case: ClinicalCase) -> str:
    input_json = json.dumps(case.to_dict(include_expected=False), sort_keys=True)
    return (
        f"CASE_ID: {case.case_id}\n"
        "Return one JSON object with these keys: detected_danger_signs, classifications, referral, "
        "actions, missing_required_observations. Use only facts in CASE_INPUT.\n"
        f"CASE_INPUT: {input_json}\n"
    )


def run_baseline(
    cases: list[ClinicalCase],
    adapter: ModelAdapter,
    output_dir: str | Path,
    *,
    benchmark_version: str = "imci_v0",
) -> dict[str, Any]:
    if not cases:
        raise ValueError("benchmark is empty")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    per_case: list[dict[str, Any]] = []
    scores = []
    total_latency_ms = 0.0
    for case in cases:
        if case.expected_result is None:
            raise ValueError(f"case {case.case_id} has no expected result")
        prompt = build_prompt(case)
        started = time.perf_counter_ns()
        failure: str | None = None
        prediction: dict[str, Any] | None = None
        raw_output = ""
        try:
            raw_output = adapter.generate(prompt)
            decoded = json.loads(raw_output)
            if not isinstance(decoded, dict):
                raise ValueError("adapter output must be a JSON object")
            prediction = decoded
            score = score_prediction(prediction, case.expected_result)
        except Exception as error:
            failure = f"{type(error).__name__}: {error}"
            score = failed_score()
        latency_ms = (time.perf_counter_ns() - started) / 1_000_000
        total_latency_ms += latency_ms
        scores.append(score)
        per_case.append(
            {
                "case_id": case.case_id,
                "categories": [item.value for item in case.generation.categories],
                "raw_output": raw_output,
                "prediction": prediction,
                "score": score.to_dict(),
                "latency_ms": latency_ms,
                "generated_token_count": None,
                "tokens_per_second": None,
                "failure": failure,
            }
        )

    run_artifact: dict[str, Any] = {
        "model_identifier": adapter.model_id,
        "benchmark_version": benchmark_version,
        "case_count": len(cases),
        "aggregate_scores": aggregate_scores(scores),
        "total_latency_ms": total_latency_ms,
        "generated_token_count": None,
        "tokens_per_second": None,
        "failures": sum(item["failure"] is not None for item in per_case),
        "per_case": per_case,
    }
    (output_path / "run.json").write_text(json.dumps(run_artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return run_artifact
