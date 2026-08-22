from __future__ import annotations

import json
from pathlib import Path

import pytest

from edge_imci.experiments.registry import SCHEMA_DIR
from edge_imci.experiments.telemetry import validate_execution, validate_telemetry
from edge_imci.experiments.tracking import RunTracker, build_run_index, validate_run_sidecar
from tests.test_experiment_registry import _experiment, fake_registry


def local_execution() -> dict:
    return {
        "environment_kind": "LOCAL_DEV",
        "execution_provider": "local",
        "local_dev": {
            "host_id": "fake-host",
            "os": "FakeOS 1",
            "architecture": "x86_64",
            "python_version": "3.12.0",
            "environment_identity": "fake-lock-sha256",
        },
    }


def tracker(tmp_path: Path, run_ids: list[str] | None = None) -> RunTracker:
    ids = iter(run_ids or ["fake-run-001"])
    return RunTracker(
        fake_registry(tmp_path),
        repo_root=tmp_path,
        run_id_factory=lambda: next(ids),
        git_capture=lambda _: {"git_commit": "a" * 40, "dirty_worktree": False},
    )


def config() -> dict:
    return {"config_id": "fake-config", "version": "1.0.0", "data": {"alpha": 1, "beta": [2, 3]}}


def test_running_sidecar_exists_before_body_and_success_is_terminal(tmp_path: Path) -> None:
    output = tmp_path / "runs" / "one"
    with tracker(tmp_path).start(
        experiment_id="fake-ready-v1", output_dir=output, config=config(), execution=local_execution()
    ) as run:
        running = validate_run_sidecar(output / "edgeimci_run.json")
        assert running["status"] == "RUNNING"
        assert running["finished_at"] is None
        assert (output / "edgeimci_config_snapshot.json").exists()
        run.record_scientific_metrics({"fake_acceptance_rate": 0.75})
        run.record_validation(
            {
                "validator_id": "fake-validator",
                "version": "1.0.0",
                "status": "PASSED",
                "pass_count": 3,
                "fail_count": 0,
                "error_codes": {},
            }
        )
    terminal = validate_run_sidecar(output / "edgeimci_run.json")
    assert terminal["status"] == "SUCCEEDED"
    assert terminal["scientific_results"] == {"fake_acceptance_rate": 0.75}
    with pytest.raises(RuntimeError, match="terminal"):
        run.record_scientific_metrics({"late": True})


def test_exception_and_interruption_finalize_and_reraise(tmp_path: Path) -> None:
    failed = tmp_path / "runs" / "failed"
    with pytest.raises(RuntimeError, match="boom"):
        with tracker(tmp_path).start(
            experiment_id="fake-ready-v1",
            output_dir=failed,
            config=config(),
            execution=local_execution(),
            command=["runner", "--api-key", "top-secret"],
        ):
            raise RuntimeError("boom token=top-secret")
    failed_record = validate_run_sidecar(failed / "edgeimci_run.json")
    assert failed_record["status"] == "FAILED"
    assert "top-secret" not in json.dumps(failed_record)

    interrupted = tmp_path / "runs" / "interrupted"
    with pytest.raises(KeyboardInterrupt):
        with tracker(tmp_path, ["fake-run-002"]).start(
            experiment_id="fake-ready-v1", output_dir=interrupted, config=config(), execution=local_execution()
        ):
            raise KeyboardInterrupt()
    assert validate_run_sidecar(interrupted / "edgeimci_run.json")["status"] == "INTERRUPTED"


def test_multiple_runs_parent_links_index_and_duplicate_output_rejection(tmp_path: Path) -> None:
    run_tracker = tracker(tmp_path, ["parent", "child"])
    parent_dir = tmp_path / "runs" / "parent"
    child_dir = tmp_path / "runs" / "child"
    with run_tracker.start(
        experiment_id="fake-ready-v1", output_dir=parent_dir, config=config(), execution=local_execution()
    ):
        pass
    with run_tracker.start(
        experiment_id="fake-ready-v1",
        output_dir=child_dir,
        config=config(),
        execution=local_execution(),
        parent_run_id="parent",
    ):
        pass

    index = build_run_index([tmp_path / "runs"], repo_root=tmp_path, schema_path=SCHEMA_DIR / "run.schema.json")
    assert [item["run_id"] for item in index["runs"]] == ["child", "parent"]
    assert index["runs"][0]["parent_run_id"] == "parent"
    with pytest.raises(FileExistsError, match="immutable"):
        tracker(tmp_path, ["ignored"]).start(
            experiment_id="fake-ready-v1", output_dir=parent_dir, config=config(), execution=local_execution()
        )


def test_completed_experiment_can_have_a_new_immutable_repeat_run(tmp_path: Path) -> None:
    registry = fake_registry(tmp_path, _experiment(status="COMPLETE"))
    run_tracker = RunTracker(
        registry,
        repo_root=tmp_path,
        run_id_factory=lambda: "repeat-run",
        git_capture=lambda _: {"git_commit": "a" * 40, "dirty_worktree": False},
    )
    with run_tracker.start(
        experiment_id="fake-ready-v1",
        output_dir=tmp_path / "runs" / "repeat",
        config=config(),
        execution=local_execution(),
    ):
        pass
    assert validate_run_sidecar(tmp_path / "runs" / "repeat" / "edgeimci_run.json")["status"] == "SUCCEEDED"


def test_material_experiment_identity_change_is_detected_across_runs(tmp_path: Path) -> None:
    registry = fake_registry(tmp_path)
    ids = iter(["before", "after"])
    run_tracker = RunTracker(
        registry,
        repo_root=tmp_path,
        run_id_factory=lambda: next(ids),
        git_capture=lambda _: {"git_commit": "a" * 40, "dirty_worktree": False},
    )
    with run_tracker.start(
        experiment_id="fake-ready-v1", output_dir=tmp_path / "runs" / "before", config=config(), execution=local_execution()
    ):
        pass
    registry.matrix["experiments"][0]["material_configuration"] = {"factor": "B"}
    with run_tracker.start(
        experiment_id="fake-ready-v1", output_dir=tmp_path / "runs" / "after", config=config(), execution=local_execution()
    ):
        pass
    with pytest.raises(ValueError, match="material experiment identity"):
        build_run_index([tmp_path / "runs"], repo_root=tmp_path, schema_path=SCHEMA_DIR / "run.schema.json")


def test_duplicate_run_ids_are_rejected_by_index(tmp_path: Path) -> None:
    for directory in ("one", "two"):
        with tracker(tmp_path, ["duplicate-run-id"]).start(
            experiment_id="fake-ready-v1",
            output_dir=tmp_path / "runs" / directory,
            config=config(),
            execution=local_execution(),
        ):
            pass
    with pytest.raises(ValueError, match="duplicate run_id"):
        build_run_index([tmp_path / "runs"], repo_root=tmp_path, schema_path=SCHEMA_DIR / "run.schema.json")


def test_artifacts_usage_and_secrets_are_derived_or_sanitized(tmp_path: Path) -> None:
    artifact = tmp_path / "dummy.txt"
    artifact.write_text("fixture-only", encoding="utf-8")
    output = tmp_path / "runs" / "artifact"
    with tracker(tmp_path).start(
        experiment_id="fake-ready-v1", output_dir=output, config=config(), execution=local_execution()
    ) as run:
        registered = run.add_artifact(artifact, artifact_id="dummy", role="FAKE_RESULT")
        run.record_usage(
            usage_id="fake-usage",
            source="fixture-provider",
            metrics={"request_count": 1},
            raw_payload={"request_id": "safe", "authorization": "Bearer secret", "nested": {"api_key": "secret"}},
        )
    record = validate_run_sidecar(output / "edgeimci_run.json")
    assert registered["bytes"] == len("fixture-only")
    assert registered["sha256"]
    assert record["usage"][0]["raw_sanitized"] == {"request_id": "safe", "nested": {}}


def test_model_dataset_prompt_and_validation_provenance_is_derived(tmp_path: Path) -> None:
    (tmp_path / "local.gguf").write_bytes(b"fixture-checkpoint")
    (tmp_path / "dataset.json").write_text('{"fixture": true}\n', encoding="utf-8")
    (tmp_path / "prompt.txt").write_text("fixture prompt", encoding="utf-8")
    (tmp_path / "validation.json").write_text('{"passed": 1}\n', encoding="utf-8")
    output = tmp_path / "runs" / "provenance"
    with tracker(tmp_path).start(
        experiment_id="fake-ready-v1",
        output_dir=output,
        config=config(),
        execution=local_execution(),
        models=[
            {
                "role": "BASE",
                "model_provider": "fixture-publisher",
                "model_source": "local-fixture",
                "model_id": "fixture-local-model",
                "artifact_path": "local.gguf",
                "remote_only": False,
            },
            {
                "role": "TEACHER",
                "model_provider": "fixture-publisher",
                "model_source": "fixture-api",
                "model_id": "fixture-remote-model",
                "revision": "immutable-snapshot-001",
                "remote_only": True,
            },
        ],
        datasets=[
            {
                "dataset_id": "fixture-data",
                "version": "1.0.0",
                "manifest_path": "dataset.json",
                "split": "fixture",
            }
        ],
        prompts=[
            {
                "prompt_id": "fixture-prompt",
                "version": "1.0.0",
                "source_path": "prompt.txt",
                "strategy": "FIXTURE",
                "sampling": {},
            }
        ],
    ) as run:
        run.record_validation(
            {
                "validator_id": "fixture-validator",
                "version": "1.0.0",
                "status": "PASSED",
                "pass_count": 1,
                "fail_count": 0,
                "error_codes": {},
                "artifact_path": "validation.json",
            }
        )
    record = validate_run_sidecar(output / "edgeimci_run.json")
    assert record["models"][0]["checkpoint_sha256"]
    assert record["models"][0]["artifact_bytes"] == len(b"fixture-checkpoint")
    assert "checkpoint_sha256" not in record["models"][1]
    assert record["datasets"][0]["sha256"]
    assert record["prompts"][0]["sha256"]
    assert record["validation"][0]["artifact_sha256"]


def test_remote_model_requires_revision_and_rejects_fabricated_hash(tmp_path: Path) -> None:
    base = {
        "role": "TEACHER",
        "model_provider": "fixture-publisher",
        "model_source": "fixture-api",
        "model_id": "fixture-remote-model",
        "remote_only": True,
    }
    with pytest.raises(ValueError, match="immutable revision"):
        tracker(tmp_path).start(
            experiment_id="fake-ready-v1",
            output_dir=tmp_path / "runs" / "missing-revision",
            config=config(),
            execution=local_execution(),
            models=[base],
        )
    with pytest.raises(ValueError, match="fabricated"):
        tracker(tmp_path, ["fake-run-002"]).start(
            experiment_id="fake-ready-v1",
            output_dir=tmp_path / "runs" / "fabricated-hash",
            config=config(),
            execution=local_execution(),
            models=[{**base, "revision": "snapshot", "checkpoint_sha256": "a" * 64}],
        )


@pytest.mark.parametrize(
    ("kind", "key", "extension"),
    [
        ("TARGET_HARDWARE", "target_hardware", {"designation": "PARTICIPANT_PROXY", "hardware": {}, "runtime": "fake", "settings": {}, "workload": {}}),
        ("MODAL", "modal", {"app_id": "a", "function_name": "f", "region": "x", "gpu_type": "fake", "gpu_count": 1, "image_identity": "sha"}),
        ("EXTERNAL_API", "external_api", {"request_mode": "STANDARD_API", "deployment": "fake", "region": "x", "model_snapshot": "v1"}),
        ("EXTERNAL_API", "external_api", {"request_mode": "AZURE_BATCH", "deployment": "fake", "region": "x", "model_snapshot": "v1"}),
        ("HYBRID", "hybrid", {"component_run_ids": ["api", "modal"]}),
        ("OFFICIAL_ADTC", "official_adtc", {"measured_on": "participant_laptop", "profiler_revision": "abc", "report_schema_revision": "def", "workload": {}}),
        ("MANAGED_TRAINING", "managed_training", {"service": "fake", "job_id": "j", "region": "x", "machine_type": "m"}),
    ],
)
def test_environment_contracts(kind: str, key: str, extension: dict) -> None:
    execution = {"environment_kind": kind, "execution_provider": "fake", key: extension}
    if kind == "EXTERNAL_API":
        execution["api_provider"] = "fake-api"
    assert validate_execution(execution)["environment_kind"] == kind


def test_environment_contract_rejects_cross_environment_and_null_fields() -> None:
    with pytest.raises(ValueError, match="only the 'local_dev'"):
        validate_execution({**local_execution(), "external_api": {}})
    invalid = local_execution()
    invalid["local_dev"]["gpu_seconds"] = None
    with pytest.raises(ValueError, match="absent, not null"):
        validate_execution(invalid)
    with pytest.raises(ValueError, match="does not apply"):
        validate_execution({**local_execution(), "api_provider": "leaked-api"})
    api_metrics = local_execution()
    api_metrics["local_dev"]["input_tokens"] = 10
    with pytest.raises(ValueError, match="API-only"):
        validate_execution(api_metrics)
    secret = local_execution()
    secret["local_dev"]["api_key"] = "must-not-be-stored"
    with pytest.raises(ValueError, match="secret-bearing"):
        validate_execution(secret)


def test_incremental_telemetry_is_environment_typed() -> None:
    assert validate_telemetry("EXTERNAL_API", {"input_tokens": 100, "accepted_items": 2}) == {
        "input_tokens": 100,
        "accepted_items": 2,
    }
    assert validate_telemetry(
        "TARGET_HARDWARE", {"generation_tokens_per_second": 12.5, "peak_memory_mb": 2048}
    )["peak_memory_mb"] == 2048
    with pytest.raises(ValueError, match="do not apply to LOCAL_DEV"):
        validate_telemetry("LOCAL_DEV", {"input_tokens": 100})
