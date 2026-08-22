#!/usr/bin/env python3
"""Run a fixture-only experiment-tracker smoke test in an isolated directory."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from edge_imci.experiments.accounting import derive_cost
from edge_imci.experiments.provenance import atomic_write_json
from edge_imci.experiments.registry import SCHEMA_DIR, ExperimentRegistry
from edge_imci.experiments.tracking import RunTracker, build_run_index, validate_run_sidecar


def run_smoke(root: Path) -> dict:
    experiment = {
        "experiment_id": "fixture-noop-v1",
        "definition_version": "1.0.0",
        "experiment_type": "SYNTHETIC_GENERATION",
        "priority": "CORE",
        "status": "READY",
        "hypothesis": "Fixture-only metadata exercises the tracker.",
        "decision_question": "Does the infrastructure round trip?",
        "branch_id": "fixture-core",
        "prerequisites": [],
        "branch_trigger": None,
        "material_configuration": {"fixture": True},
        "reproducibility": {"required_reference_kinds": [], "references": [], "unresolved_inputs": []},
        "evidence": [
            {
                "evidence_id": "fixture_metric",
                "evidence_class": "SCIENTIFIC",
                "applicability": "APPLICABLE",
                "artifact_ref": None,
            }
        ],
        "run_ids": [],
    }
    matrix = {"schema_version": "1.0.0", "registry_id": "fixture-registry", "experiments": [experiment]}
    branches = {
        "schema_version": "1.0.0",
        "campaign_id": "fixture-campaign",
        "branches": [
            {
                "branch_id": "fixture-core",
                "title": "Fixture core",
                "priority": "CORE",
                "critical_path": True,
                "state": "OPEN",
                "evidence_trigger": "Fixture smoke",
                "prerequisites": [],
                "expected_comparison": "No-op fixture round trip",
                "experiment_ids": ["fixture-noop-v1"],
            }
        ],
    }
    matrix_path = atomic_write_json(root / "matrix.json", matrix)
    branch_path = atomic_write_json(root / "branches.json", branches)
    registry = ExperimentRegistry(matrix_path, branch_path, repo_root=root, schema_dir=SCHEMA_DIR)
    registry.validate()

    dummy = root / "dummy.txt"
    dummy.write_text("fixture-only artifact", encoding="utf-8")
    output = root / "runs" / "noop"
    tracker = RunTracker(
        registry,
        repo_root=root,
        run_id_factory=lambda: "fixture-noop-run-001",
        git_capture=lambda _: {"git_commit": None, "dirty_worktree": None, "git_capture": "FIXTURE"},
    )
    with tracker.start(
        experiment_id="fixture-noop-v1",
        output_dir=output,
        config={"config_id": "fixture-config", "version": "1.0.0", "data": {"noop": True}},
        execution={
            "environment_kind": "LOCAL_DEV",
            "execution_provider": "fixture",
            "local_dev": {
                "host_id": "fixture-host",
                "os": "FixtureOS",
                "architecture": "x86_64",
                "python_version": "fixture",
                "environment_identity": "fixture-environment",
            },
        },
    ) as run:
        run.record_scientific_metrics({"fixture_score": 1})
        run.record_validation(
            {
                "validator_id": "fixture-validator",
                "version": "1.0.0",
                "status": "PASSED",
                "pass_count": 1,
                "fail_count": 0,
                "error_codes": {},
            }
        )
        run.record_usage(
            usage_id="fixture-usage",
            source="fixture",
            metrics={"request_count": 1},
            raw_payload={"fixture": True},
        )
        run.add_artifact(dummy, artifact_id="fixture-artifact", role="FIXTURE_RESULT")

    sidecar = output / "edgeimci_run.json"
    final = validate_run_sidecar(sidecar)
    index = build_run_index([root / "runs"], repo_root=root, schema_path=SCHEMA_DIR / "run.schema.json")
    rate_card = {
        "schema_version": "1.0.0",
        "rate_card_id": "fictional-smoke-rate",
        "version": "1.0.0",
        "provider": "fixture",
        "service": "fixture",
        "currency": "USD",
        "effective_from": "2026-01-01",
        "effective_to": None,
        "region": "test",
        "deployment": "fixture",
        "pricing_mode": "FIXTURE",
        "rate_class": "ESTIMATE_RATE",
        "unit_rates": [{"metric": "request_count", "unit": "PER_UNIT", "price": "0.25"}],
        "source": {"uri": "fixture://smoke", "retrieved_at": "2026-01-01T00:00:00Z", "verified": True},
    }
    cost = derive_cost({"request_count": 1}, rate_card, calculation_id="fixture-cost")
    return {
        "run_id": final["run_id"],
        "run_status": final["status"],
        "indexed_runs": len(index["runs"]),
        "artifact_sha256": final["artifacts"][0]["sha256"],
        "fixture_cost": cost["total"],
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="edgeimci-experiment-smoke-") as directory:
        print(json.dumps(run_smoke(Path(directory)), indent=2))


if __name__ == "__main__":
    main()
