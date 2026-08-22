"""Discriminated, environment-specific execution telemetry validation."""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping

from edge_imci.experiments.provenance import sanitize_value


class EnvironmentKind(str, Enum):
    LOCAL_DEV = "LOCAL_DEV"
    TARGET_HARDWARE = "TARGET_HARDWARE"
    MODAL = "MODAL"
    EXTERNAL_API = "EXTERNAL_API"
    HYBRID = "HYBRID"
    OFFICIAL_ADTC = "OFFICIAL_ADTC"
    MANAGED_TRAINING = "MANAGED_TRAINING"


_EXTENSION_KEYS = {
    EnvironmentKind.LOCAL_DEV: "local_dev",
    EnvironmentKind.TARGET_HARDWARE: "target_hardware",
    EnvironmentKind.MODAL: "modal",
    EnvironmentKind.EXTERNAL_API: "external_api",
    EnvironmentKind.HYBRID: "hybrid",
    EnvironmentKind.OFFICIAL_ADTC: "official_adtc",
    EnvironmentKind.MANAGED_TRAINING: "managed_training",
}

_REQUIRED = {
    EnvironmentKind.LOCAL_DEV: {
        "host_id",
        "os",
        "architecture",
        "python_version",
        "environment_identity",
    },
    EnvironmentKind.TARGET_HARDWARE: {
        "designation",
        "hardware",
        "runtime",
        "settings",
        "workload",
    },
    EnvironmentKind.MODAL: {
        "app_id",
        "function_name",
        "region",
        "gpu_type",
        "gpu_count",
        "image_identity",
    },
    EnvironmentKind.EXTERNAL_API: {
        "request_mode",
        "deployment",
        "region",
        "model_snapshot",
    },
    EnvironmentKind.HYBRID: {"component_run_ids"},
    EnvironmentKind.OFFICIAL_ADTC: {
        "measured_on",
        "profiler_revision",
        "report_schema_revision",
        "workload",
    },
    EnvironmentKind.MANAGED_TRAINING: {"service", "job_id", "region", "machine_type"},
}

_API_ONLY_FIELDS = {
    "input_tokens",
    "output_tokens",
    "cached_tokens",
    "reasoning_tokens",
    "provider_request_id",
    "batch_id",
}

_TELEMETRY_ALLOWED = {
    EnvironmentKind.LOCAL_DEV: {
        "relevant_counts",
        "task_status",
        "wall_duration_seconds",
    },
    EnvironmentKind.TARGET_HARDWARE: {
        "generation_tokens_per_second",
        "first_token_latency_ms",
        "total_latency_ms",
        "peak_memory_mb",
        "steady_memory_mb",
        "artifact_bytes",
        "cpu_percent",
        "thermal_notes",
        "throttled",
    },
    EnvironmentKind.MODAL: {
        "call_id",
        "job_id",
        "queue_seconds",
        "gpu_seconds",
        "job_duration_seconds",
        "task_status",
        "provider_usage",
    },
    EnvironmentKind.EXTERNAL_API: {
        "request_count",
        "batch_id",
        "batch_status",
        "attempts",
        "accepted_items",
        "rejected_items",
        "retries",
        "error_codes",
        "input_tokens",
        "output_tokens",
        "cached_tokens",
        "reasoning_tokens",
        "request_latency_seconds",
        "throughput_per_second",
    },
    EnvironmentKind.HYBRID: {
        "component_statuses",
        "combined_wall_duration_seconds",
    },
    EnvironmentKind.OFFICIAL_ADTC: {
        "profiler_status",
        "official_report_registered",
    },
    EnvironmentKind.MANAGED_TRAINING: {
        "task_status",
        "queue_seconds",
        "job_duration_seconds",
        "accelerator_seconds",
        "provider_usage",
    },
}


def _keys(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        nested = set().union(*(_keys(item) for item in value.values()), set())
        return {str(key) for key in value} | nested
    if isinstance(value, (list, tuple)):
        return set().union(*(_keys(item) for item in value), set())
    return set()


def _has_none(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(item is None or _has_none(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(item is None or _has_none(item) for item in value)
    return False


def validate_execution(execution: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one telemetry extension and reject cross-environment leakage."""
    if sanitize_value(execution) != dict(execution):
        raise ValueError("execution metadata contains a secret-bearing field")
    try:
        kind = EnvironmentKind(execution["environment_kind"])
    except (KeyError, ValueError) as error:
        raise ValueError("execution has an invalid environment_kind") from error
    expected = _EXTENSION_KEYS[kind]
    extension_keys = set(execution) & set(_EXTENSION_KEYS.values())
    if extension_keys != {expected}:
        raise ValueError(
            f"{kind.value} execution must contain only the {expected!r} extension"
        )
    extension = execution[expected]
    if not isinstance(extension, Mapping):
        raise ValueError(f"execution extension {expected} must be an object")
    missing = _REQUIRED[kind] - set(extension)
    if missing:
        raise ValueError(f"{kind.value} telemetry is missing: {sorted(missing)}")
    if _has_none(extension):
        raise ValueError(
            "non-applicable or unavailable telemetry fields must be absent, not null"
        )
    if kind is not EnvironmentKind.EXTERNAL_API and (_keys(extension) & _API_ONLY_FIELDS):
        raise ValueError(f"API-only telemetry fields do not apply to {kind.value}")
    if kind is EnvironmentKind.EXTERNAL_API:
        if extension["request_mode"] not in {"STANDARD_API", "AZURE_BATCH"}:
            raise ValueError(
                "external API request_mode must be STANDARD_API or AZURE_BATCH"
            )
        if not execution.get("api_provider"):
            raise ValueError("EXTERNAL_API requires api_provider")
    elif "api_provider" in execution:
        raise ValueError(f"api_provider does not apply to {kind.value}")
    if kind is EnvironmentKind.HYBRID and not extension["component_run_ids"]:
        raise ValueError("HYBRID requires at least one component run")
    if kind is EnvironmentKind.OFFICIAL_ADTC and extension["measured_on"] not in {
        "participant_laptop",
        "audit_cloud_vm",
    }:
        raise ValueError("invalid official ADTC measurement designation")
    return dict(execution)


def validate_telemetry(environment_kind: str, telemetry: Mapping[str, Any]) -> dict[str, Any]:
    """Validate incremental telemetry against the active environment adapter."""
    kind = EnvironmentKind(environment_kind)
    sanitized = sanitize_value(telemetry)
    if sanitized != dict(telemetry):
        raise ValueError("telemetry contains a secret-bearing field")
    unknown = set(telemetry) - _TELEMETRY_ALLOWED[kind]
    if unknown:
        raise ValueError(f"telemetry fields do not apply to {kind.value}: {sorted(unknown)}")
    if _has_none(telemetry):
        raise ValueError("unavailable telemetry fields must be absent, not null")
    return dict(telemetry)
