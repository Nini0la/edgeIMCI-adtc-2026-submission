"""Atomic, immutable execution-attempt tracking for EdgeIMCI experiments."""

from __future__ import annotations

import mimetypes
import re
import time
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from edge_imci.experiments.provenance import (
    atomic_write_json,
    capture_git_provenance,
    hash_canonical,
    hash_file,
    repo_relative,
    resolve_repo_path,
    runtime_provenance,
    sanitize_value,
)
from edge_imci.experiments.registry import (
    REPO_ROOT,
    SCHEMA_DIR,
    ExperimentRegistry,
    experiment_definition_digest,
    load_json_object,
    validate_against_schema,
)
from edge_imci.experiments.telemetry import validate_execution, validate_telemetry

SIDECAR_NAME = "edgeimci_run.json"
CONFIG_SNAPSHOT_NAME = "edgeimci_config_snapshot.json"
TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "INTERRUPTED"}


def _iso(value: datetime | str) -> str:
    if isinstance(value, str):
        return value
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _default_now() -> datetime:
    return datetime.now(timezone.utc)


def _clean_error_message(message: str) -> str:
    cleaned = re.sub(
        r"(?i)(api[_-]?key|token|password|secret|authorization)\s*[=:]\s*[^\s,;]+",
        r"\1=[REDACTED]",
        message,
    )
    return cleaned[:1000]


def _validate_run_invariants(record: Mapping[str, Any]) -> None:
    status = record["status"]
    if status == "RUNNING":
        if record["finished_at"] is not None or record["wall_duration_seconds"] is not None or record["error"] is not None:
            raise ValueError("RUNNING records cannot contain terminal fields")
    else:
        if record["finished_at"] is None or record["wall_duration_seconds"] is None:
            raise ValueError("terminal records require finish time and wall duration")
        if status == "SUCCEEDED" and record["error"] is not None:
            raise ValueError("SUCCEEDED records cannot contain an error")
    if record["parent_run_id"] == record["run_id"] or record["run_id"] in record["component_run_ids"]:
        raise ValueError("a run cannot link to itself")
    for field, key in (("usage", "usage_id"), ("artifacts", "artifact_id")):
        values = [item[key] for item in record[field]]
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {key} in run record")


def _normalize_model(item: Mapping[str, Any], repo_root: Path) -> dict[str, Any]:
    model = dict(item)
    remote = bool(model.get("remote_only"))
    model["remote_only"] = remote
    if remote:
        if not model.get("revision"):
            raise ValueError(
                f"remote model {model.get('model_id')} requires an immutable revision/snapshot"
            )
        if model.get("checkpoint_sha256"):
            raise ValueError(
                "remote-only models must not contain a fabricated local checkpoint hash"
            )
    else:
        artifact_path = model.get("artifact_path")
        if not artifact_path:
            raise ValueError(
                f"local model {model.get('model_id')} requires artifact_path"
            )
        local = resolve_repo_path(repo_root, artifact_path)
        digest, size = hash_file(local)
        if model.get("checkpoint_sha256") not in (None, digest):
            raise ValueError(f"model digest mismatch: {artifact_path}")
        model["checkpoint_sha256"] = digest
        model["artifact_bytes"] = size
    return model


def _normalize_dataset(item: Mapping[str, Any], repo_root: Path) -> dict[str, Any]:
    dataset = dict(item)
    path = dataset.get("manifest_path")
    if path:
        digest, _ = hash_file(resolve_repo_path(repo_root, path))
        if dataset.get("sha256") not in (None, digest):
            raise ValueError(f"dataset digest mismatch: {path}")
        dataset["sha256"] = digest
    elif not dataset.get("sha256"):
        raise ValueError(
            "dataset requires a local manifest hash or an explicit immutable hash"
        )
    return dataset


def _normalize_prompt(item: Mapping[str, Any], repo_root: Path) -> dict[str, Any]:
    prompt = dict(item)
    path = prompt.get("source_path")
    if not path:
        raise ValueError("prompt requires source_path")
    digest, _ = hash_file(resolve_repo_path(repo_root, path))
    if prompt.get("sha256") not in (None, digest):
        raise ValueError(f"prompt digest mismatch: {path}")
    prompt["sha256"] = digest
    return prompt


class RunHandle:
    def __init__(
        self,
        record: dict[str, Any],
        sidecar_path: Path,
        *,
        repo_root: Path,
        schema_path: Path,
        now: Callable[[], datetime | str],
        monotonic: Callable[[], float],
        monotonic_started: float,
    ) -> None:
        self.record = record
        self.sidecar_path = sidecar_path
        self.repo_root = repo_root
        self.schema_path = schema_path
        self._now = now
        self._monotonic = monotonic
        self._monotonic_started = monotonic_started

    @property
    def run_id(self) -> str:
        return self.record["run_id"]

    def _ensure_running(self) -> None:
        if self.record["status"] != "RUNNING":
            raise RuntimeError(f"run {self.run_id} is terminal and immutable")

    def _persist(self) -> None:
        validate_execution(self.record["execution"])
        validate_telemetry(self.record["execution"]["environment_kind"], self.record["telemetry"])
        validate_against_schema(self.record, self.schema_path)
        _validate_run_invariants(self.record)
        atomic_write_json(self.sidecar_path, self.record)

    def __enter__(self) -> RunHandle:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> bool:
        if exc is None:
            self.finalize("SUCCEEDED")
            return False
        status = (
            "INTERRUPTED"
            if isinstance(exc, (KeyboardInterrupt, SystemExit))
            else "FAILED"
        )
        self.finalize(
            status,
            error={
                "exception_type": type(exc).__name__,
                "message": _clean_error_message(str(exc)),
            },
        )
        return False

    def record_scientific_metrics(self, metrics: Mapping[str, Any]) -> None:
        self._ensure_running()
        self.record["scientific_results"].update(deepcopy(dict(metrics)))
        self._persist()

    def record_telemetry(self, telemetry: Mapping[str, Any]) -> None:
        self._ensure_running()
        candidate = {**self.record["telemetry"], **deepcopy(dict(telemetry))}
        self.record["telemetry"] = validate_telemetry(
            self.record["execution"]["environment_kind"], candidate
        )
        self._persist()

    def record_validation(self, result: Mapping[str, Any]) -> None:
        self._ensure_running()
        normalized = deepcopy(dict(result))
        artifact_path = normalized.get("artifact_path")
        if artifact_path:
            digest, _ = hash_file(resolve_repo_path(self.repo_root, artifact_path))
            if normalized.get("artifact_sha256") not in (None, digest):
                raise ValueError(f"validation artifact digest mismatch: {artifact_path}")
            normalized["artifact_sha256"] = digest
        self.record["validation"].append(normalized)
        self._persist()

    def record_usage(
        self,
        *,
        usage_id: str,
        source: str,
        metrics: Mapping[str, int | float | str],
        raw_payload: Mapping[str, Any] | None = None,
    ) -> None:
        self._ensure_running()
        if usage_id in {item["usage_id"] for item in self.record["usage"]}:
            raise ValueError(f"duplicate usage_id: {usage_id}")
        self.record["usage"].append(
            {
                "usage_id": usage_id,
                "source": source,
                "metrics": dict(metrics),
                "raw_sanitized": sanitize_value(raw_payload or {}),
            }
        )
        self._persist()

    def add_artifact(
        self,
        path: str | Path,
        *,
        artifact_id: str,
        role: str,
        creation: str = "PRODUCED",
        validation_state: str = "UNVALIDATED",
        media_type: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_running()
        if artifact_id in {item["artifact_id"] for item in self.record["artifacts"]}:
            raise ValueError(f"duplicate artifact_id: {artifact_id}")
        local = Path(path)
        if not local.is_absolute():
            local = resolve_repo_path(self.repo_root, local)
        relative = repo_relative(self.repo_root, local)
        digest, size = hash_file(local)
        artifact = {
            "artifact_id": artifact_id,
            "role": role,
            "path": relative,
            "sha256": digest,
            "bytes": size,
            "creation": creation,
            "validation_state": validation_state,
        }
        detected = media_type or mimetypes.guess_type(local.name)[0]
        if detected:
            artifact["media_type"] = detected
        self.record["artifacts"].append(artifact)
        self._persist()
        return artifact

    def finalize(self, status: str, *, error: dict[str, str] | None = None) -> None:
        self._ensure_running()
        if status not in TERMINAL_STATUSES:
            raise ValueError(f"invalid terminal status: {status}")
        self.record["status"] = status
        self.record["finished_at"] = _iso(self._now())
        self.record["wall_duration_seconds"] = max(
            0.0, self._monotonic() - self._monotonic_started
        )
        self.record["error"] = error
        self._persist()


class RunTracker:
    def __init__(
        self,
        registry: ExperimentRegistry | None = None,
        *,
        repo_root: str | Path = REPO_ROOT,
        now: Callable[[], datetime | str] = _default_now,
        monotonic: Callable[[], float] = time.monotonic,
        run_id_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
        git_capture: Callable[[Path], dict[str, Any]] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.registry = registry or ExperimentRegistry(repo_root=self.repo_root)
        self.now = now
        self.monotonic = monotonic
        self.run_id_factory = run_id_factory
        self.git_capture = git_capture or capture_git_provenance
        self.schema_path = self.registry.schema_dir / "run.schema.json"

    def start(
        self,
        *,
        experiment_id: str,
        output_dir: str | Path,
        config: Mapping[str, Any],
        execution: Mapping[str, Any],
        models: Sequence[Mapping[str, Any]] = (),
        datasets: Sequence[Mapping[str, Any]] = (),
        prompts: Sequence[Mapping[str, Any]] = (),
        parent_run_id: str | None = None,
        component_run_ids: Sequence[str] = (),
        command: Sequence[str] | None = None,
        profiling: Mapping[str, Any] | None = None,
    ) -> RunHandle:
        self.registry.validate()
        experiment = self.registry.get(experiment_id)
        if experiment["status"] not in {"READY", "RUNNING", "COMPLETE"}:
            raise ValueError(f"experiment {experiment_id} is not READY")
        validate_execution(execution)
        destination = Path(output_dir)
        if not destination.is_absolute():
            destination = resolve_repo_path(
                self.repo_root, destination, must_exist=False
            )
        else:
            repo_relative(self.repo_root, destination)
        destination.mkdir(parents=True, exist_ok=True)
        sidecar = destination / SIDECAR_NAME
        if sidecar.exists():
            existing = load_json_object(sidecar)
            if existing.get("status") in TERMINAL_STATUSES:
                raise FileExistsError(f"terminal run sidecar is immutable: {sidecar}")
            raise FileExistsError(f"run sidecar already exists: {sidecar}")

        config_data = deepcopy(config.get("data"))
        if not isinstance(config_data, dict):
            raise ValueError("config.data must be an object")
        snapshot = destination / CONFIG_SNAPSHOT_NAME
        atomic_write_json(snapshot, config_data, overwrite=False)
        config_record = {
            "config_id": config["config_id"],
            "version": config["version"],
            "snapshot_path": repo_relative(self.repo_root, snapshot),
            "sha256": hash_canonical(config_data),
        }
        if config.get("source_path"):
            resolve_repo_path(self.repo_root, config["source_path"])
            config_record["source_path"] = str(config["source_path"])

        started_monotonic = self.monotonic()
        record: dict[str, Any] = {
            "schema_version": "1.0.0",
            "run_id": self.run_id_factory(),
            "experiment_id": experiment_id,
            "experiment_definition_sha256": experiment_definition_digest(experiment),
            "status": "RUNNING",
            "started_at": _iso(self.now()),
            "finished_at": None,
            "wall_duration_seconds": None,
            "parent_run_id": parent_run_id,
            "component_run_ids": list(component_run_ids),
            "provenance": {
                "git": self.git_capture(self.repo_root),
                "runtime": runtime_provenance(repo_root=self.repo_root, command=command),
            },
            "execution": deepcopy(dict(execution)),
            "config": config_record,
            "models": [_normalize_model(item, self.repo_root) for item in models],
            "datasets": [_normalize_dataset(item, self.repo_root) for item in datasets],
            "prompts": [_normalize_prompt(item, self.repo_root) for item in prompts],
            "scientific_results": {},
            "validation": [],
            "telemetry": {},
            "usage": [],
            "artifacts": [],
            "accounting": [],
            "accounting_audit": [],
            "error": None,
        }
        if profiling is not None:
            record["profiling"] = deepcopy(dict(profiling))
        handle = RunHandle(
            record,
            sidecar,
            repo_root=self.repo_root,
            schema_path=self.schema_path,
            now=self.now,
            monotonic=self.monotonic,
            monotonic_started=started_monotonic,
        )
        handle._persist()
        return handle


def validate_run_sidecar(
    path: str | Path,
    *,
    schema_path: str | Path = SCHEMA_DIR / "run.schema.json",
) -> dict[str, Any]:
    record = load_json_object(path)
    validate_execution(record["execution"])
    validate_telemetry(record["execution"]["environment_kind"], record["telemetry"])
    validate_against_schema(record, schema_path)
    _validate_run_invariants(record)
    return record


def build_run_index(
    search_roots: Sequence[str | Path],
    *,
    output_path: str | Path | None = None,
    repo_root: str | Path = REPO_ROOT,
    schema_path: str | Path = SCHEMA_DIR / "run.schema.json",
) -> dict[str, Any]:
    """Discover only common sidecars; legacy run.json files remain legacy evidence."""
    root = Path(repo_root).resolve()
    sidecars: list[Path] = []
    for search_root in search_roots:
        base = Path(search_root)
        if not base.is_absolute():
            base = resolve_repo_path(root, base)
        sidecars.extend(sorted(base.rglob(SIDECAR_NAME)))
    records: list[tuple[Path, dict[str, Any]]] = [
        (path, validate_run_sidecar(path, schema_path=schema_path))
        for path in sorted(set(sidecars))
    ]
    run_ids = [item[1]["run_id"] for item in records]
    if len(run_ids) != len(set(run_ids)):
        raise ValueError("duplicate run_id discovered")
    known = set(run_ids)
    definitions: dict[str, set[str]] = {}
    for _, record in records:
        definitions.setdefault(record["experiment_id"], set()).add(
            record["experiment_definition_sha256"]
        )
        links = ([record["parent_run_id"]] if record["parent_run_id"] else []) + record[
            "component_run_ids"
        ]
        missing = set(links) - known
        if missing:
            raise ValueError(
                f"run {record['run_id']} links undiscovered runs: {sorted(missing)}"
            )
    reused = {key: values for key, values in definitions.items() if len(values) > 1}
    if reused:
        raise ValueError(
            f"material experiment identity changed across runs: {sorted(reused)}"
        )
    index = {
        "schema_version": "1.0.0",
        "index_id": "edgeimci-run-index-v1",
        "runs": [
            {
                "run_id": record["run_id"],
                "experiment_id": record["experiment_id"],
                "status": record["status"],
                "started_at": record["started_at"],
                "finished_at": record["finished_at"],
                "environment_kind": record["execution"]["environment_kind"],
                "sidecar_path": repo_relative(root, path),
                "parent_run_id": record["parent_run_id"],
                "component_run_ids": record["component_run_ids"],
            }
            for path, record in sorted(records, key=lambda item: item[1]["run_id"])
        ],
    }
    if output_path is not None:
        atomic_write_json(output_path, index)
    return index
