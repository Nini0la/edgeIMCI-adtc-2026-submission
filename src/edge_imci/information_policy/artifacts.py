"""Load, validate, and render the versioned information-policy artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from edge_imci.rules.loader import load_rule_set
from edge_imci.schemas.trajectory import (
    CANONICAL_OBSERVATION_ORDER,
    AcquisitionMode,
    ObservationId,
    acquisition_mode_for,
)

POLICY_ID = "imci-selected-v0-information-policy-v1"
CONSTRAINT_SET_ID = "imci-selected-v0-valid-completions-v1"
_CONFIG_DIR = Path(__file__).resolve().parents[3] / "configs" / "information_policy"
DEFAULT_POLICY_PATH = _CONFIG_DIR / "imci_selected_v0_information_policy_v1.json"
DEFAULT_POLICY_YAML_PATH = DEFAULT_POLICY_PATH.with_suffix(".yaml")
DEFAULT_CONSTRAINT_PATH = _CONFIG_DIR / "imci_selected_v0_valid_completions_v1.json"
DEFAULT_CONSTRAINT_YAML_PATH = DEFAULT_CONSTRAINT_PATH.with_suffix(".yaml")
_REQUIRED_CONSTRAINT_IDS = {
    "VC-SCOPE-001",
    "VC-DOMAIN-001",
    "VC-DOMAIN-002",
    "VC-DOMAIN-003",
    "VC-ENTRY-001",
    "VC-CONTAINER-001",
    "VC-COHERENCE-001",
    "VC-COHERENCE-002",
    "VC-EVIDENCE-001",
    "VC-UNKNOWN-001",
}
_REQUIRED_OPEN_QUESTIONS = {"IP-CQ-001", "IP-CQ-002", "IP-CQ-003", "IP-CQ-004"}


@dataclass(frozen=True)
class InformationPolicyArtifacts:
    policy: dict[str, Any]
    constraints: dict[str, Any]

    @property
    def observations(self) -> dict[ObservationId, dict[str, Any]]:
        return {ObservationId(item["observation_id"]): item for item in self.policy["observations"]}

    @property
    def constraints_by_id(self) -> dict[str, dict[str, Any]]:
        return {item["constraint_id"]: item for item in self.constraints["constraints"]}


class _IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        return super().increase_indent(flow, indentless=False)


def _load_json_object(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


@lru_cache(maxsize=4)
def load_information_policy_artifacts(
    policy_path: str | Path = DEFAULT_POLICY_PATH,
    constraint_path: str | Path = DEFAULT_CONSTRAINT_PATH,
) -> InformationPolicyArtifacts:
    artifacts = InformationPolicyArtifacts(
        policy=_load_json_object(policy_path),
        constraints=_load_json_object(constraint_path),
    )
    validate_information_policy_artifacts(artifacts)
    return artifacts


def validate_information_policy_artifacts(artifacts: InformationPolicyArtifacts) -> None:
    policy = artifacts.policy
    constraints = artifacts.constraints
    rule_set = load_rule_set()

    if policy.get("policy_id") != POLICY_ID or policy.get("status") != "APPROVED_V1":
        raise ValueError("policy artifact has an unexpected identity or approval status")
    if constraints.get("constraint_set_id") != CONSTRAINT_SET_ID or constraints.get("status") != "APPROVED_V1":
        raise ValueError("constraint artifact has an unexpected identity or approval status")
    if policy.get("rule_set_id") != rule_set.rule_set_id or constraints.get("rule_set_id") != rule_set.rule_set_id:
        raise ValueError("policy artifacts must pin the frozen rule-set ID")
    if policy.get("constraint_set_id") != constraints.get("constraint_set_id"):
        raise ValueError("policy artifact does not pin the loaded constraint set")

    observation_items = policy.get("observations", [])
    observation_ids = tuple(ObservationId(item["observation_id"]) for item in observation_items)
    if observation_ids != CANONICAL_OBSERVATION_ORDER:
        raise ValueError("policy observation catalog must use the complete canonical order")
    for item in observation_items:
        observation_id = ObservationId(item["observation_id"])
        if AcquisitionMode(item["acquisition_mode"]) is not acquisition_mode_for(observation_id):
            raise ValueError(f"artifact acquisition mode contradicts schema for {observation_id.value}")
        if not 1 <= item["default_priority_band"] <= 5:
            raise ValueError(f"invalid default priority band for {observation_id.value}")
        if not set(item.get("source_rule_ids", [])) <= rule_set.ids():
            raise ValueError(f"unknown source rule in observation {observation_id.value}")

    scheduler_order = tuple(ObservationId(item) for item in policy["scheduler"]["canonical_observation_order"])
    if scheduler_order != CANONICAL_OBSERVATION_ORDER:
        raise ValueError("scheduler order must match the trajectory schema order")
    if policy["scheduler"].get("uses_information_gain") or policy["scheduler"].get("stochastic"):
        raise ValueError("v1 scheduler must be deterministic and must not use information gain")

    open_questions = {item["question_id"] for item in policy.get("unresolved_questions", [])}
    if open_questions != _REQUIRED_OPEN_QUESTIONS:
        raise ValueError("all and only IP-CQ-001 through IP-CQ-004 must remain unresolved")
    if any(item.get("status") != "UNRESOLVED" for item in policy["unresolved_questions"]):
        raise ValueError("v1 unresolved questions cannot be silently resolved")

    constraint_items = constraints.get("constraints", [])
    constraint_ids = [item["constraint_id"] for item in constraint_items]
    if len(constraint_ids) != len(set(constraint_ids)) or set(constraint_ids) != _REQUIRED_CONSTRAINT_IDS:
        raise ValueError("constraint artifact must contain the complete unique v1 constraint set")
    by_id = artifacts.constraints_by_id
    if not by_id["VC-COHERENCE-001"].get("completion_pruning"):
        raise ValueError("VC-COHERENCE-001 must prune invalid completions")
    if by_id["VC-COHERENCE-002"].get("completion_pruning"):
        raise ValueError("VC-COHERENCE-002 is input validation only")
    if by_id["VC-COHERENCE-002"].get("unresolved_question_id") != "IP-CQ-002":
        raise ValueError("VC-COHERENCE-002 must retain IP-CQ-002")
    if by_id["VC-EVIDENCE-001"].get("unresolved_question_id") != "IP-CQ-003":
        raise ValueError("VC-EVIDENCE-001 must retain IP-CQ-003")


def render_generated_yaml(data: dict[str, Any], canonical_name: str, sync_script: str) -> str:
    header = (
        f"# Generated from configs/information_policy/{canonical_name}.\n"
        f"# Edit the canonical JSON and rerun {sync_script}; do not edit this mirror.\n"
    )
    body = yaml.dump(
        data,
        Dumper=_IndentedSafeDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=110,
    )
    return header + body


def sync_information_policy_yaml(
    policy_path: str | Path = DEFAULT_POLICY_PATH,
    constraint_path: str | Path = DEFAULT_CONSTRAINT_PATH,
    policy_yaml_path: str | Path = DEFAULT_POLICY_YAML_PATH,
    constraint_yaml_path: str | Path = DEFAULT_CONSTRAINT_YAML_PATH,
) -> tuple[Path, Path]:
    policy_output = Path(policy_yaml_path)
    constraint_output = Path(constraint_yaml_path)
    policy_output.parent.mkdir(parents=True, exist_ok=True)
    constraint_output.parent.mkdir(parents=True, exist_ok=True)
    script = "scripts/sync_information_policy.py"
    policy_output.write_text(
        render_generated_yaml(_load_json_object(policy_path), Path(policy_path).name, script),
        encoding="utf-8",
    )
    constraint_output.write_text(
        render_generated_yaml(_load_json_object(constraint_path), Path(constraint_path).name, script),
        encoding="utf-8",
    )
    return policy_output, constraint_output
