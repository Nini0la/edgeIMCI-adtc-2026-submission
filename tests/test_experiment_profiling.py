from __future__ import annotations

import json
from pathlib import Path

import pytest

from edge_imci.experiments.profiling import create_profile_summary, validate_profile_sidecar
from edge_imci.experiments.tracking import RunTracker
from tests.test_experiment_registry import fake_registry
from tests.test_experiment_tracking import config


def official_schema(tmp_path: Path) -> Path:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "profiler_version", "environment", "throughput", "memory"],
        "properties": {
            "schema_version": {"const": "fixture-1"},
            "profiler_version": {"const": "fixture-profiler-1"},
            "environment": {
                "type": "object",
                "additionalProperties": False,
                "required": ["measured_on", "cpu", "ram_mb", "os"],
                "properties": {
                    "measured_on": {"enum": ["participant_laptop", "audit_cloud_vm"]},
                    "cpu": {"type": "string"},
                    "ram_mb": {"type": "integer"},
                    "os": {"type": "string"},
                },
            },
            "throughput": {
                "type": "object",
                "additionalProperties": False,
                "required": ["tokens_per_second_generation", "first_token_latency_ms"],
                "properties": {
                    "tokens_per_second_generation": {"type": "number"},
                    "first_token_latency_ms": {"type": "number"},
                },
            },
            "memory": {
                "type": "object",
                "additionalProperties": False,
                "required": ["peak_rss_mb", "steady_state_rss_mb"],
                "properties": {
                    "peak_rss_mb": {"type": "number"},
                    "steady_state_rss_mb": {"type": "number"},
                },
            },
        },
    }
    path = tmp_path / "official.schema.json"
    path.write_text(json.dumps(schema), encoding="utf-8")
    return path


def execution(mode: str) -> dict:
    return {
        "environment_kind": "OFFICIAL_ADTC",
        "execution_provider": "adtc-profiler",
        "official_adtc": {
            "measured_on": mode,
            "profiler_revision": "fixture-profiler-commit",
            "report_schema_revision": "fixture-schema-commit",
            "workload": {"prompt_tokens": 512, "generated_tokens": 128},
        },
    }


def report(mode: str, generation: float, latency: float, peak: float, steady: float) -> dict:
    return {
        "schema_version": "fixture-1",
        "profiler_version": "fixture-profiler-1",
        "environment": {"measured_on": mode, "cpu": "Fixture CPU", "ram_mb": 8192, "os": "Fixture OS"},
        "throughput": {"tokens_per_second_generation": generation, "first_token_latency_ms": latency},
        "memory": {"peak_rss_mb": peak, "steady_state_rss_mb": steady},
    }


def create_profile_run(
    tmp_path: Path,
    *,
    run_id: str,
    mode: str,
    report_data: dict,
    model_path: Path,
) -> Path:
    output = tmp_path / "profiles" / run_id
    output.mkdir(parents=True)
    report_path = output / "submission.json"
    report_path.write_text(json.dumps(report_data, sort_keys=True), encoding="utf-8")
    run_tracker = RunTracker(
        fake_registry(tmp_path),
        repo_root=tmp_path,
        run_id_factory=lambda: run_id,
        git_capture=lambda _: {"git_commit": "a" * 40, "dirty_worktree": False},
    )
    with run_tracker.start(
        experiment_id="fake-ready-v1",
        output_dir=output,
        config=config(),
        execution=execution(mode),
        profiling={
            "runtime_settings": {"threads": 4},
            "accuracy_configuration": {"skipped": False, "seed": 42},
        },
    ) as run:
        run.add_artifact(
            report_path,
            artifact_id="official-report",
            role="OFFICIAL_ADTC_REPORT",
            creation="OFFICIAL_EXTERNAL",
            validation_state="VALID",
        )
        run.add_artifact(
            model_path,
            artifact_id="deployed-model",
            role="DEPLOYED_MODEL",
            creation="CONSUMED",
            validation_state="VALID",
        )
    return output / "edgeimci_run.json"


def test_profile_summary_aggregates_only_comparable_runs(tmp_path: Path) -> None:
    schema = official_schema(tmp_path)
    model = tmp_path / "fixture.gguf"
    model.write_bytes(b"not-a-real-model")
    one = create_profile_run(
        tmp_path,
        run_id="profile-1",
        mode="participant_laptop",
        report_data=report("participant_laptop", 10, 100, 2000, 1500),
        model_path=model,
    )
    two = create_profile_run(
        tmp_path,
        run_id="profile-2",
        mode="participant_laptop",
        report_data=report("participant_laptop", 14, 120, 2200, 1600),
        model_path=model,
    )
    audit = create_profile_run(
        tmp_path,
        run_id="profile-audit",
        mode="audit_cloud_vm",
        report_data=report("audit_cloud_vm", 30, 50, 1800, 1400),
        model_path=model,
    )

    summary = create_profile_summary(
        [one, two, audit],
        profile_summary_id="fixture-profile-summary-v1",
        generated_at="2026-01-01T00:00:00Z",
        official_schema_path=schema,
        repo_root=tmp_path,
    )

    assert [item["run_id"] for item in summary["included_runs"]] == ["profile-1", "profile-2"]
    assert summary["excluded_runs"] == [
        {"run_id": "profile-audit", "reason": "comparison fingerprint differs from anchor run"}
    ]
    assert summary["metrics"]["generation_tokens_per_second"] == {
        "count": 2,
        "mean": 12.0,
        "median": 12.0,
        "minimum": 10.0,
        "maximum": 14.0,
    }
    reversed_summary = create_profile_summary(
        [audit, two, one],
        profile_summary_id="fixture-profile-summary-v1",
        generated_at="2026-01-01T00:00:00Z",
        official_schema_path=schema,
        repo_root=tmp_path,
    )
    assert reversed_summary == summary


def test_official_report_is_never_rewritten_and_digest_drift_is_detected(tmp_path: Path) -> None:
    schema = official_schema(tmp_path)
    model = tmp_path / "fixture.gguf"
    model.write_bytes(b"not-a-real-model")
    sidecar = create_profile_run(
        tmp_path,
        run_id="profile-1",
        mode="participant_laptop",
        report_data=report("participant_laptop", 10, 100, 2000, 1500),
        model_path=model,
    )
    report_path = sidecar.parent / "submission.json"
    before = report_path.read_bytes()
    validate_profile_sidecar(sidecar, official_schema_path=schema, repo_root=tmp_path)
    assert report_path.read_bytes() == before

    report_path.write_bytes(before + b"\n")
    with pytest.raises(ValueError, match="bytes changed"):
        validate_profile_sidecar(sidecar, official_schema_path=schema, repo_root=tmp_path)


def test_strict_official_schema_rejects_custom_fields(tmp_path: Path) -> None:
    schema = official_schema(tmp_path)
    model = tmp_path / "fixture.gguf"
    model.write_bytes(b"not-a-real-model")
    bad = report("participant_laptop", 10, 100, 2000, 1500)
    bad["edgeimci_profile_id"] = "must-not-be-in-official-report"
    sidecar = create_profile_run(
        tmp_path,
        run_id="bad-profile",
        mode="participant_laptop",
        report_data=bad,
        model_path=model,
    )
    with pytest.raises(ValueError, match="Additional properties"):
        validate_profile_sidecar(sidecar, official_schema_path=schema, repo_root=tmp_path)


def test_failed_profile_does_not_require_fabricated_report(tmp_path: Path) -> None:
    schema = official_schema(tmp_path)
    output = tmp_path / "profiles" / "failed"
    run_tracker = RunTracker(
        fake_registry(tmp_path),
        repo_root=tmp_path,
        run_id_factory=lambda: "failed-profile",
        git_capture=lambda _: {"git_commit": "a" * 40, "dirty_worktree": False},
    )
    with pytest.raises(RuntimeError):
        with run_tracker.start(
            experiment_id="fake-ready-v1",
            output_dir=output,
            config=config(),
            execution=execution("participant_laptop"),
        ):
            raise RuntimeError("fixture profiler failed")
    record, official = validate_profile_sidecar(
        output / "edgeimci_run.json", official_schema_path=schema, repo_root=tmp_path
    )
    assert record["status"] == "FAILED"
    assert official is None
