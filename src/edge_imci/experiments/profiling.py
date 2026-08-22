"""Official-ADTC preservation checks and deterministic comparable-run summaries."""

from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any, Iterable

from edge_imci.experiments.provenance import (
    atomic_write_json,
    hash_canonical,
    hash_file,
    repo_relative,
    resolve_repo_path,
)
from edge_imci.experiments.registry import (
    REPO_ROOT,
    SCHEMA_DIR,
    load_json_object,
    validate_against_schema,
)
from edge_imci.experiments.tracking import validate_run_sidecar

_METRIC_PATHS = {
    "generation_tokens_per_second": ("throughput", "tokens_per_second_generation"),
    "first_token_latency_ms": ("throughput", "first_token_latency_ms"),
    "peak_rss_mb": ("memory", "peak_rss_mb"),
    "steady_state_rss_mb": ("memory", "steady_state_rss_mb"),
}


def validate_official_adtc_report(
    report_path: str | Path, pinned_schema_path: str | Path
) -> dict[str, Any]:
    """Validate caller-supplied bytes; never rewrite the official report."""
    report = load_json_object(report_path)
    validate_against_schema(report, pinned_schema_path)
    return report


def _artifact(record: dict[str, Any], role: str) -> dict[str, Any] | None:
    return next((item for item in record["artifacts"] if item["role"] == role), None)


def validate_profile_sidecar(
    sidecar_path: str | Path,
    *,
    official_schema_path: str | Path,
    repo_root: str | Path = REPO_ROOT,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    record = validate_run_sidecar(sidecar_path)
    if record["execution"]["environment_kind"] != "OFFICIAL_ADTC":
        raise ValueError("profile sidecar must use OFFICIAL_ADTC telemetry")
    report_artifact = _artifact(record, "OFFICIAL_ADTC_REPORT")
    model_artifact = _artifact(record, "DEPLOYED_MODEL")
    if record["status"] == "SUCCEEDED" and (
        report_artifact is None or model_artifact is None
    ):
        raise ValueError(
            "successful profile requires official report and deployed model artifacts"
        )
    if report_artifact is None:
        return record, None
    root = Path(repo_root).resolve()
    report_path = resolve_repo_path(root, report_artifact["path"])
    digest, size = hash_file(report_path)
    if digest != report_artifact["sha256"] or size != report_artifact["bytes"]:
        raise ValueError("official report bytes changed after registration")
    report = validate_official_adtc_report(report_path, official_schema_path)
    if model_artifact is not None:
        model_path = resolve_repo_path(root, model_artifact["path"])
        model_digest, model_size = hash_file(model_path)
        if (
            model_digest != model_artifact["sha256"]
            or model_size != model_artifact["bytes"]
        ):
            raise ValueError("deployed model bytes changed after registration")
    return record, report


def _value(report: dict[str, Any], path: tuple[str, ...]) -> float:
    value: Any = report
    for key in path:
        value = value[key]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"official profile metric {'.'.join(path)} is not numeric")
    return float(value)


def comparison_fingerprint(record: dict[str, Any], report: dict[str, Any]) -> str:
    model = _artifact(record, "DEPLOYED_MODEL")
    if model is None:
        raise ValueError("profile has no deployed model artifact")
    extension = record["execution"]["official_adtc"]
    comparable = {
        "experiment_id": record["experiment_id"],
        "model_sha256": model["sha256"],
        "profiler_revision": extension["profiler_revision"],
        "report_schema_revision": extension["report_schema_revision"],
        "measurement_mode": extension["measured_on"],
        "environment": report["environment"],
        "runtime_settings": record.get("profiling", {}).get("runtime_settings", {}),
        "workload": extension["workload"],
        "accuracy_configuration": record.get("profiling", {}).get(
            "accuracy_configuration", {}
        ),
    }
    return hash_canonical(comparable)


def _stats(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "minimum": min(values),
        "maximum": max(values),
    }


def create_profile_summary(
    sidecar_paths: Iterable[str | Path],
    *,
    profile_summary_id: str,
    generated_at: str,
    official_schema_path: str | Path,
    repo_root: str | Path = REPO_ROOT,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    candidates: list[tuple[Path, dict[str, Any], dict[str, Any], str]] = []
    excluded: list[dict[str, str]] = []
    for raw_path in sidecar_paths:
        path = Path(raw_path)
        record, report = validate_profile_sidecar(
            path, official_schema_path=official_schema_path, repo_root=root
        )
        if record["status"] != "SUCCEEDED" or report is None:
            excluded.append(
                {
                    "run_id": record["run_id"],
                    "reason": f"terminal status {record['status']} has no successful official report",
                }
            )
            continue
        candidates.append(
            (path, record, report, comparison_fingerprint(record, report))
        )
    if not candidates:
        raise ValueError("profile summary requires at least one successful run")
    candidates.sort(key=lambda item: item[1]["run_id"])
    anchor = candidates[0][3]
    mode = candidates[0][1]["execution"]["official_adtc"]["measured_on"]
    experiment_id = candidates[0][1]["experiment_id"]
    included = []
    metric_values = {name: [] for name in _METRIC_PATHS}
    for path, record, report, fingerprint in candidates:
        if fingerprint != anchor:
            excluded.append(
                {
                    "run_id": record["run_id"],
                    "reason": "comparison fingerprint differs from anchor run",
                }
            )
            continue
        report_artifact = _artifact(record, "OFFICIAL_ADTC_REPORT")
        assert report_artifact is not None
        included.append(
            {
                "run_id": record["run_id"],
                "sidecar_path": repo_relative(root, path),
                "official_report_sha256": report_artifact["sha256"],
            }
        )
        for name, metric_path in _METRIC_PATHS.items():
            metric_values[name].append(_value(report, metric_path))
    if not included:
        raise ValueError("no profile runs match the comparison anchor")
    summary = {
        "schema_version": "1.0.0",
        "profile_summary_id": profile_summary_id,
        "experiment_id": experiment_id,
        "generated_at": generated_at,
        "aggregation_method": "edgeimci-profile-summary-v1",
        "comparison_fingerprint": anchor,
        "measurement_mode": mode,
        "included_runs": sorted(included, key=lambda item: item["run_id"]),
        "excluded_runs": sorted(excluded, key=lambda item: item["run_id"]),
        "metrics": {name: _stats(values) for name, values in metric_values.items()},
    }
    validate_against_schema(summary, SCHEMA_DIR / "profile_summary.schema.json")
    if output_path is not None:
        atomic_write_json(output_path, summary)
    return summary
