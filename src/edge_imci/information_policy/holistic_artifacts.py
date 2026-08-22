"""Load and validate the major sick-child rule and completeness artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from edge_imci.evaluation.holistic import HOLISTIC_COMPLETENESS_POLICY_ID, HOLISTIC_RULE_SET_ID
from edge_imci.rules.loader import RuleSet, load_rule_set


_ROOT = Path(__file__).resolve().parents[3]
HOLISTIC_RULE_PATH = _ROOT / "data" / "rules" / "imci_major_sick_child_v1.json"
HOLISTIC_RULE_YAML_PATH = HOLISTIC_RULE_PATH.with_suffix(".yaml")
HOLISTIC_POLICY_PATH = (
    _ROOT
    / "configs"
    / "information_policy"
    / "imci_major_sick_child_holistic_completeness_v2.json"
)
HOLISTIC_POLICY_YAML_PATH = HOLISTIC_POLICY_PATH.with_suffix(".yaml")
HOLISTIC_DECISIONS_PATH = (
    _ROOT
    / "configs"
    / "information_policy"
    / "imci_major_sick_child_review_decisions_v1.json"
)
HOLISTIC_DECISIONS_YAML_PATH = HOLISTIC_DECISIONS_PATH.with_suffix(".yaml")


@dataclass(frozen=True)
class HolisticArtifacts:
    rule_set: RuleSet
    policy: dict[str, Any]
    decisions: dict[str, Any]


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


@lru_cache(maxsize=1)
def load_holistic_artifacts() -> HolisticArtifacts:
    artifacts = HolisticArtifacts(
        rule_set=load_rule_set(HOLISTIC_RULE_PATH),
        policy=_load_json(HOLISTIC_POLICY_PATH),
        decisions=_load_json(HOLISTIC_DECISIONS_PATH),
    )
    validate_holistic_artifacts(artifacts)
    return artifacts


def validate_holistic_artifacts(artifacts: HolisticArtifacts) -> None:
    policy = artifacts.policy
    decisions = artifacts.decisions
    if artifacts.rule_set.rule_set_id != HOLISTIC_RULE_SET_ID:
        raise ValueError("unexpected holistic rule-set ID")
    if policy.get("policy_id") != HOLISTIC_COMPLETENESS_POLICY_ID:
        raise ValueError("unexpected holistic completeness policy ID")
    if policy.get("rule_set_id") != HOLISTIC_RULE_SET_ID:
        raise ValueError("holistic policy must pin the expanded rule set")
    if policy.get("status") != "APPROVED_FOR_HACKATHON_SCOPE":
        raise ValueError("holistic policy must retain its hackathon-scope approval boundary")
    if decisions.get("decision_set_id") != policy.get("review_decision_set_id"):
        raise ValueError("holistic policy must pin the approved review-decision set")
    if decisions.get("rule_set_id") != HOLISTIC_RULE_SET_ID:
        raise ValueError("review decisions must pin the expanded rule set")
    if decisions.get("completeness_policy_id") != HOLISTIC_COMPLETENESS_POLICY_ID:
        raise ValueError("review decisions must pin the completeness policy")
    if decisions.get("status") != "APPROVED_FOR_HACKATHON_SCOPE":
        raise ValueError("review decisions must retain the hackathon-only boundary")
    if decisions.get("production_clinical_use_authorized") is not False:
        raise ValueError("review decisions must not authorize production clinical use")
    decision_ids = [item.get("question_id") for item in decisions.get("decisions", [])]
    if len(decision_ids) != 13 or len(set(decision_ids)) != 13:
        raise ValueError("review decision set must contain exactly 13 unique decisions")
    if decision_ids != policy.get("resolved_questions"):
        raise ValueError("policy resolved-question order must match the decision set")
    if policy.get("unresolved_questions"):
        raise ValueError("approved hackathon policy must not retain resolved questions as unresolved")
    population = policy.get("population", {}).get("age_months")
    if population != {"gte": 2, "lt": 60}:
        raise ValueError("holistic policy must declare exactly ages 2-59 months")
    authorization = policy.get("product_authorization", {})
    if authorization.get("final_holistic_synthesis_condition") != "SUPPORTED_ENCOUNTER_COMPLETE":
        raise ValueError("final synthesis must be gated by supported encounter completeness")
    obsolete_sufficiency_keys = (
        "decision_sufficient_authorizes_final_synthesis",
        "action_set_sufficient_authorizes_final_synthesis",
        "exact_rule_sufficient_authorizes_final_synthesis",
    )
    if any(name in authorization for name in obsolete_sufficiency_keys):
        raise ValueError("v2 must model encounter completeness, not sufficiency authorizers")
    if "internal_diagnostics" in policy:
        raise ValueError("v2 must not reintroduce legacy sufficiency diagnostics")
    if not policy.get("encounter_specific_unresolved_question_ids_block_completion"):
        raise ValueError("clinically significant unresolved branches must block completion")
    unknown = policy.get("unknown_semantics", {})
    if not unknown.get("omitted_is_unknown") or unknown.get("unknown_is_negative"):
        raise ValueError("v2 must preserve UNKNOWN and must not treat omission as negative")
    if unknown.get("silence_can_make_pathway_not_applicable"):
        raise ValueError("silence cannot make a pathway not applicable")
    if not policy.get("urgent_action_semantics", {}).get("independent_of_supported_encounter_complete"):
        raise ValueError("urgent actions must remain independent of completeness")
