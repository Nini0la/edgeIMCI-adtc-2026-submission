from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from edge_imci.information_policy.holistic_artifacts import (
    HOLISTIC_DECISIONS_PATH,
    HOLISTIC_DECISIONS_YAML_PATH,
    HOLISTIC_POLICY_PATH,
    HOLISTIC_POLICY_YAML_PATH,
    HOLISTIC_RULE_PATH,
    HOLISTIC_RULE_YAML_PATH,
    load_holistic_artifacts,
)
from edge_imci.rules.yaml_sync import render_rule_yaml
from edge_imci.information_policy.artifacts import render_generated_yaml


def test_holistic_artifacts_pin_scope_and_completion_authority() -> None:
    artifacts = load_holistic_artifacts()
    policy = artifacts.policy
    assert artifacts.rule_set.rule_set_id == "imci-major-sick-child-v1"
    assert policy["policy_id"] == "imci-major-sick-child-holistic-completeness-v2"
    assert policy["population"]["age_months"] == {"gte": 2, "lt": 60}
    assert policy["product_authorization"]["final_holistic_synthesis_condition"] == "SUPPORTED_ENCOUNTER_COMPLETE"
    assert "decision_sufficient_authorizes_final_synthesis" not in policy["product_authorization"]
    assert "internal_diagnostics" not in policy
    assert policy["encounter_specific_unresolved_question_ids_block_completion"]
    assert policy["unknown_semantics"]["omitted_is_unknown"]
    assert not policy["unknown_semantics"]["unknown_is_negative"]
    assert artifacts.decisions["status"] == "APPROVED_FOR_HACKATHON_SCOPE"
    assert len(artifacts.decisions["decisions"]) == 13
    assert policy["unresolved_questions"] == []


def test_holistic_yaml_mirrors_match_canonical_json() -> None:
    rule_json = json.loads(HOLISTIC_RULE_PATH.read_text(encoding="utf-8"))
    policy_json = json.loads(HOLISTIC_POLICY_PATH.read_text(encoding="utf-8"))
    decisions_json = json.loads(HOLISTIC_DECISIONS_PATH.read_text(encoding="utf-8"))
    assert yaml.safe_load(HOLISTIC_RULE_YAML_PATH.read_text(encoding="utf-8")) == rule_json
    assert yaml.safe_load(HOLISTIC_POLICY_YAML_PATH.read_text(encoding="utf-8")) == policy_json
    assert yaml.safe_load(HOLISTIC_DECISIONS_YAML_PATH.read_text(encoding="utf-8")) == decisions_json
    assert HOLISTIC_RULE_YAML_PATH.read_text(encoding="utf-8") == render_rule_yaml(
        rule_json,
        HOLISTIC_RULE_PATH,
        "scripts/sync_holistic_artifacts.py",
    )
    assert HOLISTIC_POLICY_YAML_PATH.read_text(encoding="utf-8") == render_generated_yaml(
        policy_json,
        HOLISTIC_POLICY_PATH.name,
        "scripts/sync_holistic_artifacts.py",
    )
    assert HOLISTIC_DECISIONS_YAML_PATH.read_text(encoding="utf-8") == render_generated_yaml(
        decisions_json,
        HOLISTIC_DECISIONS_PATH.name,
        "scripts/sync_holistic_artifacts.py",
    )


def test_every_evaluator_rule_id_exists_in_canonical_expanded_rule_set() -> None:
    evaluator = Path("src/edge_imci/evaluation/holistic.py").read_text(encoding="utf-8")
    referenced = set(re.findall(r'"(IMCI-MSC-[A-Z0-9-]+)"', evaluator))
    canonical = load_holistic_artifacts().rule_set.ids()
    assert referenced <= canonical
