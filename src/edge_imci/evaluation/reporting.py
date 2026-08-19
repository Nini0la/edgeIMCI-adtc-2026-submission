"""Build a deterministic index over separate auditable benchmark run artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

_INTERNAL_EVIDENCE = {
    "case_id",
    "prompt",
    "raw_model_output",
    "parsed_prediction",
    "expected_oracle_result",
    "parse_status",
    "parse_error",
    "score",
    "overall_pass",
    "latency_ms",
}
_EXTERNAL_EVIDENCE = {
    "question_id",
    "prompt",
    "raw_model_output",
    "parsed_answer",
    "parse_valid",
    "parse_error",
    "expected_answer",
    "is_correct",
    "included_in_denominator",
    "latency_ms",
}


def build_results_index(run_paths: Iterable[str | Path]) -> dict[str, Any]:
    sections: dict[str, list[dict[str, Any]]] = {}
    for raw_path in sorted((Path(path) for path in run_paths), key=str):
        content = raw_path.read_bytes()
        artifact = json.loads(content)
        schema_version = artifact.get("schema_version")
        if schema_version == "edge-imci-run-v1":
            _validate_records(artifact, _INTERNAL_EVIDENCE)
            section = "edge_imci_v0_development_regression"
            summary = {
                "aggregate_scores": artifact["aggregate_scores"],
                "parse_failure_count": artifact["parse_failure_count"],
                "parse_failure_rate": artifact["parse_failure_rate"],
                "generation_failure_count": artifact["generation_failure_count"],
            }
        elif schema_version == "edge-imci-external-run-v1":
            _validate_records(artifact, _EXTERNAL_EVIDENCE)
            section = f"{artifact['benchmark_id']}::{artifact['evaluation_policy']}"
            summary = {
                "correct_count": artifact["correct_count"],
                "denominator": artifact["denominator"],
                "accuracy": artifact["accuracy"],
                "invalid_count": artifact["invalid_count"],
                "invalid_rate": artifact["invalid_rate"],
                "generation_failure_count": artifact["generation_failure_count"],
                "by_label": artifact["by_label"],
                "policy_warning": artifact["policy_warning"],
            }
        else:
            raise ValueError(f"unsupported run artifact schema in {raw_path}: {schema_version}")
        sections.setdefault(section, []).append(
            {
                "artifact_path": str(raw_path),
                "artifact_sha256": hashlib.sha256(content).hexdigest(),
                "schema_version": schema_version,
                "model_identifier": artifact["model_identifier"],
                "model_metadata": artifact["model_metadata"],
                "runtime_metadata": artifact["runtime_metadata"],
                "prompt_version": artifact["prompt_version"],
                "case_or_question_count": len(artifact["per_case"]),
                "summary": summary,
            }
        )
    return {
        "schema_version": "edge-imci-results-index-v1",
        "aggregation_policy": "sections are intentionally separate; no cross-benchmark overall score",
        "sections": sections,
    }


def write_results_index(run_paths: Iterable[str | Path], output_path: str | Path) -> dict[str, Any]:
    index = build_results_index(run_paths)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _validate_records(artifact: dict[str, Any], required_fields: set[str]) -> None:
    records = artifact.get("per_case")
    if not isinstance(records, list) or len(records) != artifact.get("case_count", artifact.get("question_count")):
        raise ValueError("run artifact per-case evidence count does not match scheduled count")
    for record in records:
        missing = required_fields - set(record)
        if missing:
            raise ValueError(f"run artifact evidence record missing fields: {sorted(missing)}")
