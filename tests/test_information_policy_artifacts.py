from __future__ import annotations

import json

import yaml

from edge_imci.information_policy.artifacts import (
    CONSTRAINT_SET_ID,
    DEFAULT_CONSTRAINT_PATH,
    DEFAULT_CONSTRAINT_YAML_PATH,
    DEFAULT_POLICY_PATH,
    DEFAULT_POLICY_YAML_PATH,
    POLICY_ID,
    load_information_policy_artifacts,
    render_generated_yaml,
)
from edge_imci.schemas.trajectory import CANONICAL_OBSERVATION_ORDER


def _yaml_body(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[2:]) + "\n"


def test_canonical_policy_and_constraint_artifacts_are_valid_and_pinned():
    artifacts = load_information_policy_artifacts()

    assert artifacts.policy["policy_id"] == POLICY_ID
    assert artifacts.policy["constraint_set_id"] == CONSTRAINT_SET_ID
    assert artifacts.constraints["constraint_set_id"] == CONSTRAINT_SET_ID
    assert tuple(item["observation_id"] for item in artifacts.policy["observations"]) == tuple(
        item.value for item in CANONICAL_OBSERVATION_ORDER
    )
    assert artifacts.policy["approved_decisions"] == ["IP-RQ-001", "IP-RQ-002"]
    assert {item["question_id"] for item in artifacts.policy["unresolved_questions"]} == {
        "IP-CQ-001",
        "IP-CQ-002",
        "IP-CQ-003",
        "IP-CQ-004",
    }


def test_yaml_mirrors_equal_canonical_json_and_deterministic_rendering():
    policy = json.loads(DEFAULT_POLICY_PATH.read_text(encoding="utf-8"))
    constraints = json.loads(DEFAULT_CONSTRAINT_PATH.read_text(encoding="utf-8"))

    assert yaml.safe_load(DEFAULT_POLICY_YAML_PATH.read_text(encoding="utf-8")) == policy
    assert yaml.safe_load(DEFAULT_CONSTRAINT_YAML_PATH.read_text(encoding="utf-8")) == constraints
    assert DEFAULT_POLICY_YAML_PATH.read_text(encoding="utf-8") == render_generated_yaml(
        policy,
        DEFAULT_POLICY_PATH.name,
        "scripts/sync_information_policy.py",
    )
    assert DEFAULT_CONSTRAINT_YAML_PATH.read_text(encoding="utf-8") == render_generated_yaml(
        constraints,
        DEFAULT_CONSTRAINT_PATH.name,
        "scripts/sync_information_policy.py",
    )
    assert yaml.safe_load(_yaml_body(DEFAULT_POLICY_YAML_PATH)) == policy
    assert yaml.safe_load(_yaml_body(DEFAULT_CONSTRAINT_YAML_PATH)) == constraints


def test_completion_constraints_preserve_approved_enforcement_modes():
    by_id = load_information_policy_artifacts().constraints_by_id

    assert by_id["VC-COHERENCE-001"]["completion_pruning"] is True
    assert by_id["VC-COHERENCE-002"]["enforcement"] == "INPUT_VALIDATION_ONLY"
    assert by_id["VC-COHERENCE-002"]["completion_pruning"] is False
    assert by_id["VC-COHERENCE-002"]["unresolved_question_id"] == "IP-CQ-002"
    assert by_id["VC-EVIDENCE-001"]["enforcement"] == "PRESERVE_UNRESOLVED"
    assert by_id["VC-EVIDENCE-001"]["unresolved_question_id"] == "IP-CQ-003"
    assert by_id["VC-UNKNOWN-001"]["enforcement"] == "GLOBAL_COMPLETION_RULE"
