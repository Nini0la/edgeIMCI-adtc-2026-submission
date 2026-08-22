"""Experiment and campaign registry loading, validation, and YAML synchronization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import jsonschema
import yaml

from edge_imci.experiments.provenance import hash_canonical, resolve_repo_path

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_DIR = REPO_ROOT / "experiments" / "registry"
DEFAULT_MATRIX_PATH = REGISTRY_DIR / "experiment_matrix.json"
DEFAULT_MATRIX_YAML_PATH = REGISTRY_DIR / "experiment_matrix.yaml"
DEFAULT_BRANCH_PATH = REGISTRY_DIR / "campaign_branches.json"
DEFAULT_RUN_INDEX_PATH = REGISTRY_DIR / "run_index.json"
SCHEMA_DIR = REGISTRY_DIR / "schemas"


class _IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        return super().increase_indent(flow, indentless=False)


def load_json_object(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate_against_schema(value: Any, schema_path: str | Path) -> None:
    schema = load_json_object(schema_path)
    validator_class = jsonschema.validators.validator_for(schema)
    validator_class.check_schema(schema)
    validator = validator_class(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(
        validator.iter_errors(value), key=lambda item: list(item.absolute_path)
    )
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path) or "<root>"
        raise ValueError(f"schema validation failed at {location}: {first.message}")


def _validate_refs(items: Iterable[dict[str, Any]], repo_root: Path) -> None:
    for item in items:
        location = item.get("location")
        if not location:
            continue
        if item.get("remote_only"):
            if not item.get("immutable_revision"):
                raise ValueError(
                    f"remote reference {item['reference_id']} lacks immutable_revision"
                )
            continue
        path = resolve_repo_path(repo_root, location)
        if item.get("sha256"):
            from edge_imci.experiments.provenance import hash_file

            actual, _ = hash_file(path)
            if actual != item["sha256"]:
                raise ValueError(f"reference digest mismatch: {location}")


def experiment_definition_digest(experiment: dict[str, Any]) -> str:
    """Hash only definition fields; lifecycle and run links do not change identity."""
    ignored = {"status", "run_ids", "evidence"}
    return hash_canonical(
        {key: value for key, value in experiment.items() if key not in ignored}
    )


class ExperimentRegistry:
    def __init__(
        self,
        matrix_path: str | Path = DEFAULT_MATRIX_PATH,
        branch_path: str | Path = DEFAULT_BRANCH_PATH,
        *,
        repo_root: str | Path = REPO_ROOT,
        schema_dir: str | Path = SCHEMA_DIR,
    ) -> None:
        self.matrix_path = Path(matrix_path)
        self.branch_path = Path(branch_path)
        self.repo_root = Path(repo_root).resolve()
        self.schema_dir = Path(schema_dir)
        self.matrix = load_json_object(self.matrix_path)
        self.branches = load_json_object(self.branch_path)

    def validate(self, *, check_references: bool = True) -> None:
        validate_against_schema(self.matrix, self.schema_dir / "experiment.schema.json")
        validate_against_schema(
            self.branches, self.schema_dir / "campaign_branch.schema.json"
        )
        experiments = self.matrix["experiments"]
        ids = [item["experiment_id"] for item in experiments]
        if len(ids) != len(set(ids)):
            raise ValueError("experiment_id values must be unique")
        by_id = {item["experiment_id"]: item for item in experiments}
        branch_ids = [item["branch_id"] for item in self.branches["branches"]]
        if len(branch_ids) != len(set(branch_ids)):
            raise ValueError("branch_id values must be unique")
        for experiment in experiments:
            refs = experiment["reproducibility"]["references"]
            reference_ids = [item["reference_id"] for item in refs]
            if len(reference_ids) != len(set(reference_ids)):
                raise ValueError(
                    f"duplicate reproducibility reference in {experiment['experiment_id']}"
                )
            available = {item["reference_kind"] for item in refs}
            required = set(experiment["reproducibility"]["required_reference_kinds"])
            unresolved = experiment["reproducibility"]["unresolved_inputs"]
            if experiment["status"] in {"READY", "RUNNING", "COMPLETE"}:
                if unresolved or required - available:
                    raise ValueError(
                        f"{experiment['experiment_id']} is {experiment['status']} with unresolved reproducibility inputs"
                    )
                for ref in refs:
                    if not ref.get("sha256") and not (
                        ref.get("remote_only") and ref.get("immutable_revision")
                    ):
                        raise ValueError(
                            f"ready reference lacks immutable identity: {ref['reference_id']}"
                        )
            evidence_ids = [item["evidence_id"] for item in experiment["evidence"]]
            if len(evidence_ids) != len(set(evidence_ids)):
                raise ValueError(
                    f"duplicate evidence ID in {experiment['experiment_id']}"
                )
            for evidence in experiment["evidence"]:
                if (
                    evidence["applicability"] == "NOT_APPLICABLE"
                    and evidence.get("artifact_ref") is not None
                ):
                    raise ValueError(
                        "not-applicable evidence cannot have an artifact reference"
                    )
                if check_references and evidence.get("artifact_ref"):
                    resolve_repo_path(self.repo_root, evidence["artifact_ref"])
            if check_references:
                _validate_refs(refs, self.repo_root)
        for branch in self.branches["branches"]:
            unknown = set(branch["experiment_ids"]) - set(by_id)
            if unknown:
                raise ValueError(
                    f"branch {branch['branch_id']} references unknown experiments: {sorted(unknown)}"
                )
            if branch["state"] == "DORMANT" and branch["critical_path"]:
                raise ValueError("a dormant branch cannot be on the critical path")

    def get(self, experiment_id: str) -> dict[str, Any]:
        for experiment in self.matrix["experiments"]:
            if experiment["experiment_id"] == experiment_id:
                return experiment
        raise KeyError(f"unknown experiment_id: {experiment_id}")


def render_matrix_yaml(
    data: dict[str, Any], source_name: str = "experiment_matrix.json"
) -> str:
    header = (
        f"# Generated from experiments/registry/{source_name}.\n"
        "# Edit canonical JSON and run `python -m edge_imci.experiments.cli sync-yaml`.\n"
    )
    return header + yaml.dump(
        data,
        Dumper=_IndentedSafeDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=110,
    )


def sync_matrix_yaml(
    matrix_path: str | Path = DEFAULT_MATRIX_PATH,
    yaml_path: str | Path = DEFAULT_MATRIX_YAML_PATH,
) -> Path:
    data = load_json_object(matrix_path)
    output = Path(yaml_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_matrix_yaml(data, Path(matrix_path).name), encoding="utf-8"
    )
    return output
